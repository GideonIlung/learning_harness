#!/usr/bin/env -S uv run python
from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import sys
import time
from collections import defaultdict, deque
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

STATUSES = {"not_started", "learning", "review", "strong", "mastered"}
IMPORTANCE = {"core", "supporting", "advanced", "optional"}
DEFAULT_FILE = "concepts.json"


def project_root() -> Path:
    return Path(os.environ.get("LEARNING_CURRICULUM_PROJECT_ROOT", os.getcwd())).resolve()


def curriculum_dir(root: Path) -> Path:
    return root / "curriculum"


def curriculum_path(root: Path) -> Path:
    return curriculum_dir(root) / DEFAULT_FILE


def mastery_path(root: Path) -> Path:
    return root / "learner" / "mastery.json"


def canonical_id(s: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "_", s.strip().lower()).strip("_")
    return s or "concept"


def clean(s: Any) -> str:
    return " ".join(str(s or "").strip().split())


def uniq(seq: List[Any]) -> List[Any]:
    out, seen = [], set()
    for x in seq:
        key = json.dumps(x, sort_keys=True, ensure_ascii=False) if isinstance(x, (dict, list)) else str(x).lower()
        if key not in seen:
            seen.add(key); out.append(x)
    return out


def empty_curriculum() -> Dict[str, Any]:
    return {"version": 1, "updated_at": None, "concepts": {}}


def default_concept(cid: str, name: Optional[str] = None) -> Dict[str, Any]:
    return {
        "id": cid,
        "name": name or cid.replace("_", " ").title(),
        "description": "",
        "prerequisites": [],
        "learning_objectives": [],
        "importance": "supporting",
        "source_refs": [],
        "status": "not_started",
    }


def normalize_concept(c: Dict[str, Any]) -> Dict[str, Any]:
    cid = canonical_id(c.get("id") or c.get("name") or "concept")
    out = default_concept(cid, clean(c.get("name")) or None)
    out.update({k: c.get(k, out[k]) for k in out})
    out["id"] = cid
    out["name"] = clean(out.get("name")) or cid
    out["description"] = clean(out.get("description"))
    out["prerequisites"] = uniq([canonical_id(x) for x in out.get("prerequisites", []) if clean(x)])
    out["learning_objectives"] = uniq([clean(x) for x in out.get("learning_objectives", []) if clean(x)])
    out["importance"] = out.get("importance") if out.get("importance") in IMPORTANCE else "supporting"
    out["source_refs"] = uniq(out.get("source_refs", []) if isinstance(out.get("source_refs"), list) else [])
    out["status"] = out.get("status") if out.get("status") in STATUSES else "not_started"
    return out


def load_curriculum(root: Path) -> Dict[str, Any]:
    path = curriculum_path(root)
    if not path.exists():
        return empty_curriculum()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict): return empty_curriculum()
        data.setdefault("version", 1); data.setdefault("concepts", {})
        # Accept list or dict storage.
        if isinstance(data["concepts"], list):
            data["concepts"] = {normalize_concept(c)["id"]: normalize_concept(c) for c in data["concepts"] if isinstance(c, dict)}
        else:
            data["concepts"] = {canonical_id(k): normalize_concept({**v, "id": v.get("id", k)}) for k, v in data["concepts"].items() if isinstance(v, dict)}
        return data
    except Exception:
        return empty_curriculum()


def save_curriculum(root: Path, data: Dict[str, Any]) -> None:
    curriculum_dir(root).mkdir(parents=True, exist_ok=True)
    data["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    curriculum_path(root).write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_mastery(root: Path) -> Dict[str, Any]:
    if not mastery_path(root).exists(): return {"concepts": {}}
    try: return json.loads(mastery_path(root).read_text(encoding="utf-8"))
    except Exception: return {"concepts": {}}


def mastery_for(root: Path, concept: Dict[str, Any]) -> Dict[str, Any]:
    data = load_mastery(root).get("concepts", {})
    candidates = [concept["id"], concept["name"], concept["id"].replace("_", " ")]
    by_lower = {k.lower(): v for k, v in data.items()}
    state = None
    for c in candidates:
        if c and c.lower() in by_lower:
            state = by_lower[c.lower()]; break
    if not state:
        return {"level": "absent", "score": 0.0, "evidence": 0, "strong": False}
    dims = state.get("dimensions", {})
    counts = state.get("evidence_counts", {})
    vals = [float(dims.get(d, 0.0)) for d in ["intuition", "formal_understanding", "application", "reasoning", "transfer"]]
    score = sum(vals) / len(vals) if vals else 0.0
    evidence = sum(int(v.get("total", 0)) for v in counts.values() if isinstance(v, dict))
    strong = evidence >= 3 and (score >= 0.65 or (dims.get("application", 0) >= 0.7 and dims.get("reasoning", 0) >= 0.55))
    level = "strong" if strong else ("weak" if evidence else "absent")
    return {"level": level, "score": round(score, 3), "evidence": evidence, "strong": strong}


def dependents(concepts: Dict[str, Dict[str, Any]]) -> Dict[str, List[str]]:
    dep = defaultdict(list)
    for cid, c in concepts.items():
        for p in c.get("prerequisites", []): dep[p].append(cid)
    return {k: sorted(v) for k, v in dep.items()}


def prereq_closure_order(concepts: Dict[str, Dict[str, Any]], target: str) -> List[str]:
    target = canonical_id(target)
    if target not in concepts:
        # try by name
        for cid, c in concepts.items():
            if c.get("name", "").lower() == target.replace("_", " ").lower(): target = cid; break
    seen, temp, order = set(), set(), []
    def dfs(cid: str):
        if cid in seen: return
        if cid in temp: raise ValueError(f"Prerequisite cycle detected at {cid}")
        if cid not in concepts: return
        temp.add(cid)
        for p in concepts[cid].get("prerequisites", []): dfs(p)
        temp.remove(cid); seen.add(cid); order.append(cid)
    dfs(target)
    return order


def get_curriculum(params: Dict[str, Any]) -> Dict[str, Any]:
    root = project_root(); data = load_curriculum(root); concepts = data.get("concepts", {})
    dep = dependents(concepts)
    concept = params.get("concept")
    if concept:
        cid = canonical_id(concept)
        if cid not in concepts:
            for k, c in concepts.items():
                if c.get("name", "").lower() == clean(concept).lower(): cid = k; break
        if cid not in concepts: return {"error": f"Unknown concept: {concept}"}
        c = concepts[cid]
        out = {k: c[k] for k in ["id", "name", "description", "prerequisites", "learning_objectives", "source_refs", "status"]}
        out["dependent_concepts"] = dep.get(cid, [])
        out["learner_mastery"] = mastery_for(root, c)
        if params.get("include_prerequisites"):
            out["prerequisite_details"] = [concepts[p] for p in c.get("prerequisites", []) if p in concepts]
        if params.get("include_dependents"):
            out["dependent_details"] = [concepts[d] for d in dep.get(cid, []) if d in concepts]
        return out
    rows = []
    for cid, c in sorted(concepts.items(), key=lambda kv: (kv[1].get("importance") != "core", kv[1].get("name", "").lower())):
        m = mastery_for(root, c)
        rows.append({"id": cid, "name": c.get("name"), "status": c.get("status"), "importance": c.get("importance"), "prerequisites": c.get("prerequisites", []), "learner_mastery": m["level"]})
    return {"version": data.get("version", 1), "concept_count": len(rows), "concepts": rows}


def get_learning_path(params: Dict[str, Any]) -> Dict[str, Any]:
    if not clean(params.get("target")): raise ValueError("target is required")
    root = project_root(); data = load_curriculum(root); concepts = data.get("concepts", {})
    target_raw = clean(params["target"]); target = canonical_id(target_raw)
    if target not in concepts:
        for cid, c in concepts.items():
            if c.get("name", "").lower() == target_raw.lower(): target = cid; break
    if target not in concepts: return {"error": f"Unknown target: {target_raw}", "known_concepts": sorted(concepts)}
    ordered = prereq_closure_order(concepts, target)
    path = []
    for cid in ordered:
        c = concepts[cid]; m = mastery_for(root, c)
        if m["strong"] and cid != target:
            continue
        why = []
        if cid == target: why.append("target concept")
        needed_by = [x for x in ordered if cid in concepts.get(x, {}).get("prerequisites", [])]
        if needed_by: why.append("prerequisite for " + ", ".join(needed_by))
        if m["level"] == "absent": why.append("no learner mastery evidence yet")
        elif m["level"] == "weak": why.append(f"mastery evidence is weak (score {m['score']}, evidence {m['evidence']})")
        path.append({"id": cid, "name": c.get("name"), "status": c.get("status"), "mastery": m, "why": "; ".join(why) or "included by dependency order"})
    return {"target": target, "path": path, "skipped_strong_prerequisites": [cid for cid in ordered if cid != target and mastery_for(root, concepts[cid])["strong"]]}


def update_curriculum(params: Dict[str, Any]) -> Dict[str, Any]:
    root = project_root(); data = load_curriculum(root); concepts = data.setdefault("concepts", {})
    cid = canonical_id(params.get("id") or params.get("name") or (params.get("concept") or {}).get("id") or (params.get("concept") or {}).get("name") or "")
    if not cid: raise ValueError("id or name is required")
    existing = concepts.get(cid, default_concept(cid, params.get("name")))
    concept_obj = params.get("concept") if isinstance(params.get("concept"), dict) else {}
    for field in ["name", "description", "importance", "status"]:
        if field in concept_obj: existing[field] = concept_obj[field]
        if field in params and params[field] is not None: existing[field] = params[field]
    for field, aliases in [("prerequisites", ["prerequisites", "add_prerequisites"]), ("learning_objectives", ["learning_objectives", "add_learning_objectives"]), ("source_refs", ["source_refs", "add_source_refs"] )]:
        vals = list(existing.get(field, []))
        for a in aliases:
            incoming = concept_obj.get(a, params.get(a, []))
            if isinstance(incoming, str): incoming = [incoming]
            if isinstance(incoming, list): vals.extend(incoming)
        existing[field] = vals
    concepts[cid] = normalize_concept(existing)
    # Ensure referenced prerequisites exist as stubs rather than broken links.
    for p in concepts[cid].get("prerequisites", []): concepts.setdefault(p, default_concept(p))
    save_curriculum(root, data)
    return {"ok": True, "concept": concepts[cid], "path": str(curriculum_path(root))}


def render_overview() -> None:
    root = project_root(); data = load_curriculum(root); concepts = data.get("concepts", {})
    if not concepts:
        print("No curriculum concepts yet. Use update_curriculum or /build-curriculum."); return
    print(f"{'Concept':28} {'Status':13} {'Mastery':8} Prerequisites")
    print(f"{'-'*28} {'-'*13} {'-'*8} {'-'*30}")
    for cid, c in sorted(concepts.items(), key=lambda kv: kv[1].get("name", "").lower()):
        m = mastery_for(root, c)["level"]
        prereqs = ", ".join(c.get("prerequisites", [])) or "-"
        print(f"{c.get('name','')[:28]:28} {c.get('status','')[:13]:13} {m[:8]:8} {prereqs}")


def render_learning_path(target: str) -> None:
    result = get_learning_path({"target": target})
    if "error" in result:
        print(result["error"]); return
    print(f"Learning path for {result['target']}:")
    for i, item in enumerate(result["path"], 1):
        print(f"{i}. {item['name']} [{item['mastery']['level']}] — {item['why']}")
    if result.get("skipped_strong_prerequisites"):
        print("Skipped strong prerequisites: " + ", ".join(result["skipped_strong_prerequisites"]))


def build_curriculum() -> None:
    """Heuristic proposal from indexed sources. Writes a proposal, not the live curriculum."""
    root = project_root(); db = root / ".learning" / "source-index" / "source_index.sqlite"
    if not db.exists():
        print("No source index found. Run /index-sources first."); return
    con = sqlite3.connect(str(db)); con.row_factory = sqlite3.Row
    rows = con.execute("SELECT source, page, text FROM documents ORDER BY source, page LIMIT 250").fetchall(); con.close()
    stop = set("introduction example examples problem problems solution solutions chapter section figure table review exam practice nomenclature references".split())
    candidates: Dict[str, Dict[str, Any]] = {}
    heading_re = re.compile(r"^(?:\d+(?:\.\d+)*\s+)?([A-Z][A-Za-z][A-Za-z0-9 /,&()\-]{3,70})$")
    for r in rows:
        text = r["text"] or ""
        lines = [clean(x) for x in text.splitlines()[:80]]
        for line in lines:
            m = heading_re.match(line)
            if not m: continue
            name = clean(m.group(1)).strip(" :-")
            words = [w.lower() for w in re.findall(r"[A-Za-z]+", name)]
            if not words or words[0] in stop or len(name) < 4 or len(name.split()) > 8: continue
            cid = canonical_id(name)
            item = candidates.setdefault(cid, default_concept(cid, name))
            item["source_refs"].append({"source": r["source"], "page": r["page"], "note": "heading-like occurrence"})
    # Filter repeated/major candidates; keep top 30 by source refs.
    items = sorted(candidates.values(), key=lambda c: len(c["source_refs"]), reverse=True)[:30]
    concepts = {}
    for c in items:
        c["source_refs"] = uniq(c["source_refs"])[:5]
        c["description"] = "Proposed from repeated heading-like source occurrences; verify/refine before relying on this concept."
        c["learning_objectives"] = [f"Explain the purpose of {c['name']}.", f"Apply {c['name']} in representative problems.", f"Recognize when {c['name']} is relevant."]
        c["importance"] = "core" if len(c["source_refs"]) >= 3 else "supporting"
        c["status"] = "not_started"
        concepts[c["id"]] = normalize_concept(c)
    proposal = {"version": 1, "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "notes": ["Heuristic proposal only; headings were filtered but not blindly accepted.", "Prerequisite relationships are intentionally conservative/empty unless refined later."], "concepts": concepts}
    out = curriculum_dir(root) / "proposed_curriculum.json"
    curriculum_dir(root).mkdir(parents=True, exist_ok=True)
    if out.exists():
        out = curriculum_dir(root) / f"proposed_curriculum_{int(time.time())}.json"
    out.write_text(json.dumps(proposal, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
    print(f"Wrote curriculum proposal to {out}")
    if curriculum_path(root).exists(): print("Existing curriculum/concepts.json was not overwritten.")


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("curriculum")
    lp = sub.add_parser("learning-path"); lp.add_argument("target")
    sub.add_parser("build-curriculum")
    args = p.parse_args(argv)
    if args.cmd == "curriculum": render_overview()
    elif args.cmd == "learning-path": render_learning_path(args.target)
    elif args.cmd == "build-curriculum": build_curriculum()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
