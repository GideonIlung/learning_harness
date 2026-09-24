#!/usr/bin/env -S uv run python
"""Lightweight local source index for a learning project."""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sqlite3
import sys
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

TEXT_SUFFIXES = {".txt", ".md", ".markdown"}
PDF_SUFFIX = ".pdf"


def project_root() -> Path:
    return Path(os.environ.get("SOURCE_LIBRARY_PROJECT_ROOT", os.getcwd())).resolve()


def sources_dir(root: Path) -> Path:
    return root / "sources"


def index_dir(root: Path) -> Path:
    return root / ".learning" / "source-index"


def db_path(root: Path) -> Path:
    return index_dir(root) / "source_index.sqlite"


def manifest_path(root: Path) -> Path:
    return index_dir(root) / "manifest.json"


def iter_source_files(root: Path) -> Iterable[Path]:
    sdir = sources_dir(root)
    if not sdir.exists():
        return []
    return sorted(
        (p for p in sdir.rglob("*") if p.is_file() and p.suffix.lower() in TEXT_SUFFIXES | {PDF_SUFFIX}),
        key=lambda p: str(p.relative_to(sdir)).lower(),
    )


def load_pdf_reader():
    try:
        from pypdf import PdfReader  # type: ignore
        return PdfReader, "pypdf"
    except Exception:
        try:
            from PyPDF2 import PdfReader  # type: ignore
            return PdfReader, "PyPDF2"
        except Exception as e:
            raise RuntimeError(
                "PDF extraction requires 'pypdf' from the project-root pyproject.toml. Add it there if missing, then run: uv sync"
            ) from e


def extract_pdf_pages(path: Path) -> Tuple[List[str], Optional[str]]:
    PdfReader, backend = load_pdf_reader()
    try:
        reader = PdfReader(str(path))
        pages: List[str] = []
        for page in reader.pages:
            try:
                pages.append(page.extract_text() or "")
            except Exception as e:
                pages.append(f"[Text extraction failed for this page: {e}]")
        return pages, backend
    except Exception as e:
        raise RuntimeError(f"Unreadable PDF '{path.name}': {e}") from e


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")


def connect(path: Path) -> sqlite3.Connection:
    con = sqlite3.connect(str(path))
    con.row_factory = sqlite3.Row
    return con


def init_db(con: sqlite3.Connection) -> None:
    con.executescript(
        """
        PRAGMA journal_mode=WAL;
        CREATE TABLE documents (
            id INTEGER PRIMARY KEY,
            source TEXT NOT NULL,
            rel_path TEXT NOT NULL,
            kind TEXT NOT NULL,
            page INTEGER,
            page_count INTEGER,
            text TEXT NOT NULL
        );
        CREATE VIRTUAL TABLE documents_fts USING fts5(
            text, source UNINDEXED, page UNINDEXED, content='documents', content_rowid='id'
        );
        CREATE TRIGGER documents_ai AFTER INSERT ON documents BEGIN
            INSERT INTO documents_fts(rowid, text, source, page) VALUES (new.id, new.text, new.source, new.page);
        END;
        """
    )


def rebuild_index(root: Path) -> Dict[str, Any]:
    idir = index_dir(root)
    idir.mkdir(parents=True, exist_ok=True)
    tmp = idir / "source_index.tmp.sqlite"
    if tmp.exists():
        tmp.unlink()
    con = connect(tmp)
    init_db(con)
    manifest: Dict[str, Any] = {"created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "sources": [], "errors": []}
    sdir = sources_dir(root)
    for path in iter_source_files(root):
        rel = str(path.relative_to(sdir))
        filename = path.name
        suffix = path.suffix.lower()
        try:
            if suffix == PDF_SUFFIX:
                pages, backend = extract_pdf_pages(path)
                page_count = len(pages)
                for i, text in enumerate(pages, start=1):
                    con.execute(
                        "INSERT INTO documents(source, rel_path, kind, page, page_count, text) VALUES (?, ?, ?, ?, ?, ?)",
                        (filename, rel, "pdf", i, page_count, text),
                    )
                manifest["sources"].append({"source": filename, "rel_path": rel, "kind": "pdf", "page_count": page_count, "indexed": True, "extractor": backend})
            else:
                text = read_text(path)
                con.execute(
                    "INSERT INTO documents(source, rel_path, kind, page, page_count, text) VALUES (?, ?, ?, ?, ?, ?)",
                    (filename, rel, "text", None, None, text),
                )
                manifest["sources"].append({"source": filename, "rel_path": rel, "kind": "text", "page_count": None, "indexed": True})
        except Exception as e:
            manifest["errors"].append({"source": filename, "rel_path": rel, "error": str(e)})
            manifest["sources"].append({"source": filename, "rel_path": rel, "kind": "pdf" if suffix == PDF_SUFFIX else "text", "page_count": None, "indexed": False, "error": str(e)})
    con.commit()
    con.close()
    final = db_path(root)
    if final.exists():
        final.unlink()
    shutil.move(str(tmp), str(final))
    wal = Path(str(tmp) + "-wal")
    shm = Path(str(tmp) + "-shm")
    for extra in (wal, shm):
        if extra.exists():
            extra.unlink()
    manifest_path(root).write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return manifest


def fts_query(raw: str) -> str:
    terms = re.findall(r"[\w]+", raw, flags=re.UNICODE)
    if not terms:
        return '""'
    return " AND ".join(f'"{t}"' for t in terms)


def ensure_index(root: Path) -> None:
    if not db_path(root).exists():
        raise SystemExit("No source index found. Run /index-sources first.")


def search(root: Path, query: str, max_results: int = 8, source: Optional[str] = None) -> List[Dict[str, Any]]:
    ensure_index(root)
    max_results = max(1, min(int(max_results or 8), 50))
    con = connect(db_path(root))
    fq = fts_query(query)
    params: List[Any] = [fq]
    source_clause = ""
    fallback_source_clause = ""
    if source:
        source_clause = " AND d.source = ?"
        fallback_source_clause = " AND source = ?"
        params.append(source)
    params.append(max_results)
    try:
        rows = con.execute(
            f"""
            SELECT d.source, d.page,
                   snippet(documents_fts, 0, '[', ']', ' … ', 24) AS excerpt,
                   bm25(documents_fts) AS raw_score
            FROM documents_fts
            JOIN documents d ON d.id = documents_fts.rowid
            WHERE documents_fts MATCH ? {source_clause}
            ORDER BY raw_score
            LIMIT ?
            """,
            params,
        ).fetchall()
        return [
            {"source": r["source"], "page": r["page"], "excerpt": r["excerpt"], "score": -float(r["raw_score"])}
            for r in rows
        ]
    except sqlite3.Error:
        # Conservative fallback for unusual query/tokenization issues.
        like = f"%{query}%"
        params2: List[Any] = [like]
        if source:
            params2.append(source)
        params2.append(max_results)
        rows = con.execute(
            f"SELECT source, page, text FROM documents WHERE text LIKE ? {fallback_source_clause} LIMIT ?", params2
        ).fetchall()
        return [{"source": r["source"], "page": r["page"], "excerpt": make_excerpt(r["text"], query), "score": None} for r in rows]
    finally:
        con.close()


def make_excerpt(text: str, query: str, width: int = 260) -> str:
    m = re.search(re.escape(query), text, re.IGNORECASE)
    if not m:
        return text[:width].replace("\n", " ")
    start = max(0, m.start() - width // 2)
    end = min(len(text), m.end() + width // 2)
    return (("…" if start else "") + text[start:end] + ("…" if end < len(text) else "")).replace("\n", " ")


def read_pages(root: Path, source: str, start_page: int, end_page: int) -> Dict[str, Any]:
    ensure_index(root)
    if start_page < 1 or end_page < start_page:
        raise ValueError("Expected 1 <= start_page <= end_page.")
    con = connect(db_path(root))
    rows = con.execute(
        "SELECT source, page, page_count, text FROM documents WHERE source = ? AND page BETWEEN ? AND ? ORDER BY page",
        (source, start_page, end_page),
    ).fetchall()
    con.close()
    if not rows:
        raise ValueError(f"No indexed pages found for {source!r} in range {start_page}-{end_page}.")
    return {
        "source": source,
        "start_page": start_page,
        "end_page": end_page,
        "page_count": rows[0]["page_count"],
        "pages": [{"page": r["page"], "text": r["text"]} for r in rows],
    }


def sources_status(root: Path) -> List[Dict[str, Any]]:
    indexed: Dict[str, Dict[str, Any]] = {}
    if manifest_path(root).exists():
        try:
            man = json.loads(manifest_path(root).read_text(encoding="utf-8"))
            indexed = {s.get("rel_path") or s.get("source"): s for s in man.get("sources", [])}
        except Exception:
            pass
    sdir = sources_dir(root)
    out = []
    for path in iter_source_files(root):
        rel = str(path.relative_to(sdir))
        info = indexed.get(rel) or indexed.get(path.name) or {}
        out.append({"source": path.name, "rel_path": rel, "page_count": info.get("page_count"), "indexed": bool(info.get("indexed", False)), "error": info.get("error")})
    return out


def print_sources(root: Path) -> None:
    rows = sources_status(root)
    if not rows:
        print("No supported source files found in sources/.")
        return
    print(f"{'Indexed':7} {'Pages':>7}  Source")
    print(f"{'-'*7} {'-'*7}  {'-'*40}")
    for r in rows:
        pages = "-" if r["page_count"] is None else str(r["page_count"])
        mark = "yes" if r["indexed"] else "no"
        extra = f"  ERROR: {r['error']}" if r.get("error") else ""
        print(f"{mark:7} {pages:>7}  {r['rel_path']}{extra}")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Index and search project sources.")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("index-sources")
    sub.add_parser("sources")
    ps = sub.add_parser("search")
    ps.add_argument("query")
    ps.add_argument("--max-results", type=int, default=8)
    ps.add_argument("--source")
    pr = sub.add_parser("read-pages")
    pr.add_argument("source")
    pr.add_argument("start_page", type=int)
    pr.add_argument("end_page", type=int)
    args = parser.parse_args(argv)
    root = project_root()
    try:
        if args.cmd == "index-sources":
            man = rebuild_index(root)
            print(f"Indexed {sum(1 for s in man['sources'] if s.get('indexed'))} source file(s).")
            if man.get("errors"):
                print(f"Encountered {len(man['errors'])} error(s):", file=sys.stderr)
                for e in man["errors"]:
                    print(f"- {e['rel_path']}: {e['error']}", file=sys.stderr)
            print(f"Index: {db_path(root)}")
        elif args.cmd == "sources":
            print_sources(root)
        elif args.cmd == "search":
            print(json.dumps(search(root, args.query, args.max_results, args.source), indent=2, ensure_ascii=False))
        elif args.cmd == "read-pages":
            print(json.dumps(read_pages(root, args.source, args.start_page, args.end_page), indent=2, ensure_ascii=False))
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
