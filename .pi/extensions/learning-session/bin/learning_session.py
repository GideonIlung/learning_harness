#!/usr/bin/env -S uv run python
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
from typing import Any, Dict, List, Optional, Tuple

STAGES = [
    "DIAGNOSTIC", "OPENING_PROBLEM", "MOTIVATION", "INTUITION", "VISUALIZATION",
    "FORMALIZATION", "WORKED_EXAMPLE", "CHECKPOINT", "DERIVATION", "PROOF",
    "GUIDED_PRACTICE", "INDEPENDENT_PRACTICE", "TRANSFER", "REVIEW", "SUMMARY", "COMPLETE"
]
EVENT_TYPES = {
    "concept_introduced", "explanation_given", "visual_shown", "example_completed",
    "checkpoint_completed", "misconception_found", "misconception_repaired", "proof_completed",
    "transfer_completed"
}
DIMENSIONS = ["recognition", "intuition", "formal_understanding", "application", "reasoning", "transfer"]


def now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def project_root() -> Path:
    return Path(os.environ.get("LEARNING_SESSION_PROJECT_ROOT", os.getcwd())).resolve()


def state_path(root: Path) -> Path:
    return root / ".learning" / "current-session.json"


def history_dir(root: Path) -> Path:
    return root / ".learning" / "session-history"


def curriculum_path(root: Path) -> Path:
    return root / "curriculum" / "concepts.json"


def mastery_path(root: Path) -> Path:
    return root / "learner" / "mastery.json"


def source_db_path(root: Path) -> Path:
    return root / ".learning" / "source-index" / "source_index.sqlite"


def clean(s: Any) -> str:
    return " ".join(str(s or "").strip().split())


def canonical_id(s: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "_", clean(s).lower()).strip("_") or "concept"


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_curriculum(root: Path) -> Dict[str, Any]:
    data = load_json(curriculum_path(root), {"version": 1, "concepts": {}})
    if isinstance(data.get("concepts"), list):
        data["concepts"] = {canonical_id(c.get("id") or c.get("name")): c for c in data["concepts"] if isinstance(c, dict)}
    data.setdefault("concepts", {})
    return data


def load_mastery(root: Path) -> Dict[str, Any]:
    data = load_json(mastery_path(root), {"concepts": {}})
    data.setdefault("concepts", {})
    return data


def concept_lookup(concepts: Dict[str, Dict[str, Any]], topic: str) -> Optional[str]:
    cid = canonical_id(topic)
    if cid in concepts:
        return cid
    topic_l = clean(topic).lower()
    for k, c in concepts.items():
        if clean(c.get("name")).lower() == topic_l:
            return k
    # allow partial name match if unambiguous
    matches = [k for k, c in concepts.items() if topic_l in clean(c.get("name")).lower() or topic_l in k]
    return matches[0] if len(matches) == 1 else None


def mastery_for(root: Path, concept: Dict[str, Any]) -> Dict[str, Any]:
    data = load_mastery(root).get("concepts", {})
    keys = [concept.get("id", ""), concept.get("name", ""), str(concept.get("id", "")).replace("_", " ")]
    by_lower = {k.lower(): v for k, v in data.items() if isinstance(v, dict)}
    state = None
    for key in keys:
        if key and key.lower() in by_lower:
            state = by_lower[key.lower()]
            break
    if not state:
        return {"level": "absent", "score": 0.0, "evidence": 0, "dimensions": {}, "active_misconceptions": []}
    dims = state.get("dimensions", {}) if isinstance(state.get("dimensions"), dict) else {}
    counts = state.get("evidence_counts", {}) if isinstance(state.get("evidence_counts"), dict) else {}
    vals = [float(dims.get(d, 0.0) or 0.0) for d in ["intuition", "formal_understanding", "application", "reasoning", "transfer"]]
    score = sum(vals) / len(vals) if vals else 0.0
    evidence = sum(int(v.get("total", 0) or 0) for v in counts.values() if isinstance(v, dict))
    level = "strong" if evidence >= 3 and score >= 0.65 else ("moderate" if evidence >= 2 and score >= 0.35 else ("weak" if evidence else "absent"))
    return {
        "level": level,
        "score": round(score, 3),
        "evidence": evidence,
        "dimensions": {d: round(float(dims.get(d, 0.0) or 0.0), 3) for d in DIMENSIONS},
        "active_misconceptions": state.get("active_misconceptions", []),
    }


def prereq_order(concepts: Dict[str, Dict[str, Any]], target: str) -> List[str]:
    seen, temp, order = set(), set(), []
    def dfs(cid: str):
        if cid in seen or cid not in concepts:
            return
        if cid in temp:
            raise ValueError(f"Curriculum prerequisite cycle at {cid}")
        temp.add(cid)
        for p in concepts[cid].get("prerequisites", []) or []:
            dfs(canonical_id(p))
        temp.remove(cid); seen.add(cid); order.append(cid)
    dfs(target)
    return order


def build_learning_path(root: Path, target_topic: str) -> Tuple[str, List[Dict[str, Any]]]:
    cur = load_curriculum(root)
    concepts = cur.get("concepts", {})
    target = concept_lookup(concepts, target_topic)
    if not target:
        # topic-agnostic fallback: create virtual path item without writing curriculum.
        virtual = {"id": canonical_id(target_topic), "name": clean(target_topic), "description": "No curriculum entry found yet.", "prerequisites": [], "learning_objectives": []}
        return virtual["id"], [{"id": virtual["id"], "name": virtual["name"], "mastery": mastery_for(root, virtual), "status": "unknown", "why": "target topic; no curriculum entry found"}]
    ordered = prereq_order(concepts, target)
    path = []
    for cid in ordered:
        c = concepts[cid]
        m = mastery_for(root, {**c, "id": cid})
        if cid != target and m["level"] == "strong":
            continue
        why = []
        if cid == target: why.append("target concept")
        if m["level"] in {"absent", "weak"}: why.append(f"mastery evidence {m['level']}")
        elif m["level"] == "moderate": why.append("some evidence, but may need confirmation")
        path.append({"id": cid, "name": c.get("name", cid), "status": c.get("status", "not_started"), "mastery": m, "why": "; ".join(why) or "needed prerequisite"})
    return target, path


def search_sources(root: Path, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    db = source_db_path(root)
    if not db.exists():
        return []
    terms = re.findall(r"[\w]+", query)
    if not terms:
        return []
    fts = " AND ".join(f'"{t}"' for t in terms)
    con = sqlite3.connect(str(db)); con.row_factory = sqlite3.Row
    try:
        rows = con.execute(
            """
            SELECT d.source, d.page, snippet(documents_fts, 0, '[', ']', ' … ', 20) AS excerpt
            FROM documents_fts JOIN documents d ON d.id = documents_fts.rowid
            WHERE documents_fts MATCH ? ORDER BY bm25(documents_fts) LIMIT ?
            """, (fts, max_results)
        ).fetchall()
        return [{"source": r["source"], "page": r["page"], "excerpt": r["excerpt"]} for r in rows]
    except Exception:
        return []
    finally:
        con.close()


def load_state(root: Path) -> Dict[str, Any]:
    return load_json(state_path(root), {})


def save_state(root: Path, state: Dict[str, Any]) -> None:
    write_json(state_path(root), state)


def first_unmastered(path: List[Dict[str, Any]]) -> Dict[str, Any]:
    for item in path:
        if item.get("mastery", {}).get("level") != "strong":
            return item
    return path[-1]


def diagnostic_needed(path: List[Dict[str, Any]]) -> bool:
    if not path:
        return True
    weakish = [p for p in path[:3] if p.get("mastery", {}).get("level") in {"absent", "weak"}]
    return bool(weakish) or path[0].get("mastery", {}).get("evidence", 0) < 2


def start_learning_session(params: Dict[str, Any]) -> Dict[str, Any]:
    topic = clean(params.get("topic"))
    if not topic:
        raise ValueError("topic is required")
    root = project_root()
    target, path = build_learning_path(root, topic)
    current = first_unmastered(path)
    sources = search_sources(root, current.get("name") or topic, 5)
    need_diag = diagnostic_needed(path)
    stage = "DIAGNOSTIC" if need_diag else "OPENING_PROBLEM"
    state = {
        "session_id": f"lesson-{int(time.time())}",
        "target_topic": topic,
        "goal": clean(params.get("goal")),
        "available_time_minutes": params.get("available_time_minutes"),
        "current_concept": current["id"],
        "learning_path": path,
        "current_stage": stage,
        "concepts_visited": [],
        "assessments_completed": [],
        "misconceptions_discovered": [],
        "visuals_generated": [],
        "sources_used": sources,
        "events": [],
        "session_start_time": now(),
        "last_updated": now(),
    }
    save_state(root, state)
    known = [f"{p['name']}: {p.get('mastery',{}).get('level','absent')}" for p in path]
    return {
        "target": topic,
        "goal": state["goal"] or None,
        "known": known,
        "learning_path": [{"id": p["id"], "name": p["name"], "mastery": p["mastery"]["level"], "why": p["why"]} for p in path],
        "likely_starting_point": current.get("name"),
        "current_concept": current["id"],
        "suggested_first_action": "ASK_DIAGNOSTIC" if need_diag else "INTRODUCE_PROBLEM",
        "diagnostic_appropriate": need_diag,
        "source_refs_available": [{"source": s["source"], "page": s["page"]} for s in sources],
        "teaching_brief": "Use this as structure only. The LLM should generate diagnostic questions or lesson content adaptively."
    }


def event_counts(state: Dict[str, Any], concept: Optional[str] = None) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for e in state.get("events", []):
        if concept and e.get("concept") != concept:
            continue
        counts[e.get("event_type", "unknown")] = counts.get(e.get("event_type", "unknown"), 0) + 1
    return counts


def parse_recent(recent: str) -> Dict[str, bool]:
    r = recent.lower()
    return {
        "wrong_high_conf": bool(re.search(r"(wrong|incorrect|missed|error).{0,40}(high.conf|confiden|80|90|100)|high.conf.{0,40}(wrong|incorrect|error)", r)),
        "struggling": any(x in r for x in ["struggling", "stuck", "confused", "multiple errors", "two errors", "many hints", "hint level 3", "hint_level 3", "hint level 4"]),
        "uncertain_correct": ("correct" in r and any(x in r for x in ["uncertain", "low confidence", "not confident", "guess"])),
        "strong": any(x in r for x in ["strong performance", "independent", "correct without hints", "easy", "high confidence correct"]),
        "visual_stuck": any(x in r for x in ["abstract", "can't visualize", "spatial", "graph", "diagram", "transformation"]),
    }


def get_next_teaching_action(params: Dict[str, Any]) -> Dict[str, Any]:
    root = project_root(); state = load_state(root)
    if not state:
        return {"action": "START_SESSION", "reason": "No active learning session found."}
    recent = clean(params.get("recent_evidence"))
    signals = parse_recent(recent)
    concept = state.get("current_concept")
    counts = event_counts(state, concept)
    stage = state.get("current_stage", "DIAGNOSTIC")
    cur_item = next((p for p in state.get("learning_path", []) if p.get("id") == concept), {})
    mastery = mastery_for(root, {"id": concept, "name": cur_item.get("name", concept)})

    if signals["wrong_high_conf"]:
        return {"action": "DIAGNOSE_MISCONCEPTION", "reason": "Recent evidence suggests a confidently wrong answer; diagnose the misconception before adding new material.", "suggested_dimension_to_assess": "intuition"}
    if mastery.get("active_misconceptions"):
        return {"action": "REPAIR_MISCONCEPTION", "reason": "Learner-state has active misconceptions for the current concept.", "active_misconceptions": mastery["active_misconceptions"]}
    if signals["visual_stuck"] or (signals["struggling"] and counts.get("visual_shown", 0) == 0):
        return {"action": "DRAW_DIAGRAM", "reason": "The learner appears stuck on abstraction or structure; a targeted visual may reveal relationships."}
    if signals["struggling"]:
        return {"action": "REVIEW_PREREQUISITE", "reason": "Recent evidence suggests instability or high hint dependence; check whether the issue is prerequisite-related before continuing."}
    if signals["uncertain_correct"]:
        return {"action": "INDEPENDENT_PRACTICE", "reason": "Repeated correctness with low confidence calls for confidence-building practice with reduced scaffolding.", "suggested_dimension_to_assess": "application"}
    if signals["strong"] or (mastery["level"] in {"moderate", "strong"} and counts.get("checkpoint_completed", 0) >= 1):
        return {"action": "ASK_TRANSFER", "reason": "Performance appears strong enough to test flexible use in a less familiar context.", "suggested_dimension_to_assess": "transfer"}

    if stage == "DIAGNOSTIC":
        return {"action": "ASK_DIAGNOSTIC", "reason": "Session is at diagnostic stage; estimate prerequisites and misconceptions with a short diagnostic."}
    if counts.get("concept_introduced", 0) == 0:
        return {"action": "INTRODUCE_PROBLEM", "reason": "The concept has not yet been introduced; start problem-first to create need."}
    if counts.get("example_completed", 0) == 0:
        return {"action": "SHOW_WORKED_EXAMPLE", "reason": "Learner has had introduction but no worked example recorded yet."}
    if counts.get("checkpoint_completed", 0) == 0:
        return {"action": "ASK_CHECKPOINT", "reason": "The learner has seen explanation/example but has not demonstrated understanding in this session.", "suggested_dimension_to_assess": "application"}
    return {"action": "CONTINUE_ADAPTIVELY", "reason": "No strong signal to repair or advance yet; use teacher judgment and collect another meaningful checkpoint."}


def record_learning_event(params: Dict[str, Any]) -> Dict[str, Any]:
    root = project_root(); state = load_state(root)
    if not state:
        raise ValueError("No active learning session. Start one with start_learning_session or /learn.")
    et = clean(params.get("event_type"))
    if et not in EVENT_TYPES:
        raise ValueError(f"event_type must be one of: {', '.join(sorted(EVENT_TYPES))}")
    concept = canonical_id(params.get("concept") or state.get("current_concept") or "")
    event = {
        "timestamp": now(),
        "event_type": et,
        "concept": concept,
        "description": clean(params.get("description")),
    }
    if params.get("source_ref"):
        event["source_ref"] = params["source_ref"]
        if params["source_ref"] not in state.setdefault("sources_used", []):
            state["sources_used"].append(params["source_ref"])
    if params.get("visual_path"):
        event["visual_path"] = params["visual_path"]
        if params["visual_path"] not in state.setdefault("visuals_generated", []):
            state["visuals_generated"].append(params["visual_path"])
    state.setdefault("events", []).append(event)
    if concept not in state.setdefault("concepts_visited", []):
        state["concepts_visited"].append(concept)
    if et == "checkpoint_completed":
        state.setdefault("assessments_completed", []).append(event)
        state["current_stage"] = "CHECKPOINT"
    elif et == "misconception_found":
        state.setdefault("misconceptions_discovered", []).append(event)
        state["current_stage"] = "REVIEW"
    elif et == "visual_shown":
        state["current_stage"] = "VISUALIZATION"
    elif et == "example_completed":
        state["current_stage"] = "WORKED_EXAMPLE"
    elif et == "transfer_completed":
        state["current_stage"] = "TRANSFER"
    elif et == "proof_completed":
        state["current_stage"] = "PROOF"
    elif et == "concept_introduced":
        state["current_stage"] = "INTUITION"
    state["last_updated"] = now()
    save_state(root, state)
    return {"ok": True, "event": event, "current_stage": state["current_stage"]}


def advance_learning_concept(params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    root = project_root(); state = load_state(root)
    if not state:
        return {"result": "NO_ACTIVE_SESSION", "reason": "No active learning session found."}
    path = state.get("learning_path", [])
    concept = state.get("current_concept")
    idx = next((i for i, p in enumerate(path) if p.get("id") == concept), 0)
    item = path[idx] if path else {"id": concept, "name": concept}
    mastery = mastery_for(root, {"id": concept, "name": item.get("name", concept)})
    counts = event_counts(state, concept)
    recent_mis = [m for m in state.get("misconceptions_discovered", []) if m.get("concept") == concept]
    if recent_mis and not any(e for e in state.get("events", []) if e.get("event_type") == "misconception_repaired" and e.get("concept") == concept):
        return {"result": "CONTINUE_CURRENT_CONCEPT", "reason": "A misconception was found and no repair event is recorded yet."}
    prereqs = []
    cur = load_curriculum(root).get("concepts", {}).get(concept, {})
    for p in cur.get("prerequisites", []) or []:
        pc = load_curriculum(root).get("concepts", {}).get(canonical_id(p), {"id": canonical_id(p), "name": p})
        pm = mastery_for(root, {**pc, "id": canonical_id(p)})
        if pm["level"] in {"absent", "weak"}:
            prereqs.append({"id": canonical_id(p), "mastery": pm["level"]})
    if prereqs and counts.get("checkpoint_completed", 0) == 0:
        return {"result": "REVIEW_PREREQUISITE", "reason": "Current concept depends on weak/absent prerequisite evidence.", "prerequisites": prereqs}
    if counts.get("checkpoint_completed", 0) == 0 and mastery["level"] != "strong":
        return {"result": "CONTINUE_CURRENT_CONCEPT", "reason": "No session checkpoint is recorded for this concept yet."}
    if mastery["level"] == "strong" or counts.get("transfer_completed", 0) >= 1:
        if idx + 1 < len(path):
            state["current_concept"] = path[idx + 1]["id"]
            state["current_stage"] = "OPENING_PROBLEM"
            state["last_updated"] = now(); save_state(root, state)
            return {"result": "MOVE_TO_NEXT_CONCEPT", "reason": "Evidence is sufficient to move on without requiring perfect mastery.", "next_concept": state["current_concept"]}
        state["current_stage"] = "COMPLETE"; state["last_updated"] = now(); save_state(root, state)
        return {"result": "SESSION_COMPLETE", "reason": "Final concept has sufficient evidence or transfer completion recorded."}
    if mastery["level"] == "moderate" and counts.get("checkpoint_completed", 0) >= 1:
        return {"result": "READY_FOR_TRANSFER", "reason": "Moderate evidence plus a checkpoint suggests testing transfer before moving on."}
    return {"result": "CONTINUE_CURRENT_CONCEPT", "reason": "Evidence is not yet strong enough; continue with guided or independent practice.", "mastery": mastery}


def lesson_status_text() -> str:
    root = project_root(); state = load_state(root)
    if not state:
        return "No active lesson. Start one with /learn <topic>."
    concept = state.get("current_concept")
    lines = [f"Topic: {state.get('target_topic')}", f"Current concept: {concept}", f"Stage: {state.get('current_stage')}", "", "Learning path:"]
    for p in state.get("learning_path", []):
        marker = "→" if p.get("id") == concept else ("✓" if p.get("id") in state.get("concepts_visited", []) else "○")
        lines.append(f"{marker} {p.get('name')} [{p.get('mastery',{}).get('level','absent')}]")
    cur_item = next((p for p in state.get("learning_path", []) if p.get("id") == concept), {"id": concept, "name": concept})
    m = mastery_for(root, {"id": concept, "name": cur_item.get("name", concept)})
    lines.extend(["", "Current evidence:"])
    dims = m.get("dimensions", {})
    for d in ["intuition", "application", "reasoning", "transfer"]:
        val = dims.get(d, 0.0)
        label = "strong" if val >= 0.65 else ("developing" if val > 0 else "not tested")
        lines.append(f"* {d}: {label}")
    active = m.get("active_misconceptions") or [x.get("description") for x in state.get("misconceptions_discovered", []) if x.get("concept") == concept]
    if active:
        lines.append("\nActive misconception:")
        for a in active[:3]: lines.append(f"* {a}")
    return "\n".join(lines)


def end_lesson() -> Dict[str, Any]:
    root = project_root(); state = load_state(root)
    if not state:
        return {"message": "No active lesson to end."}
    concepts = state.get("concepts_visited", []) or [state.get("current_concept")]
    evidence = {
        "events": len(state.get("events", [])),
        "checkpoints": len(state.get("assessments_completed", [])),
        "visuals": len(state.get("visuals_generated", [])),
        "misconceptions": len(state.get("misconceptions_discovered", [])),
    }
    current = state.get("current_concept")
    cur_item = next((p for p in state.get("learning_path", []) if p.get("id") == current), {"id": current, "name": current})
    mastery = mastery_for(root, {"id": current, "name": cur_item.get("name", current)})
    unresolved = []
    if mastery["level"] in {"absent", "weak"}:
        unresolved.append(f"{current}: learner-state evidence is {mastery['level']}")
    unresolved += [m.get("description", "misconception") for m in state.get("misconceptions_discovered", [])[-3:]]
    summary = {
        "session_id": state.get("session_id"),
        "target_topic": state.get("target_topic"),
        "session_start_time": state.get("session_start_time"),
        "session_end_time": now(),
        "concepts_covered": concepts,
        "strongest_evidence": evidence,
        "unresolved_weaknesses": unresolved,
        "review_next_time": unresolved[:3] or [f"Attempt a transfer checkpoint for {current}"],
        "sources_used": state.get("sources_used", []),
        "visuals_generated": state.get("visuals_generated", []),
    }
    history_dir(root).mkdir(parents=True, exist_ok=True)
    archive = history_dir(root) / f"{state.get('session_id','lesson')}.json"
    write_json(archive, {"summary": summary, "state": state})
    try:
        state_path(root).unlink()
    except FileNotFoundError:
        pass
    summary["archive_path"] = str(archive)
    summary["note"] = "No learner-state mastery was automatically updated from explanation events; use learner-state assessment tools for actual performance evidence."
    return summary


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Coordinate adaptive learning-session state.")
    sub = parser.add_subparsers(dest="cmd", required=True)
    learn = sub.add_parser("learn"); learn.add_argument("topic", nargs="+")
    sub.add_parser("lesson-status")
    sub.add_parser("end-lesson")
    args = parser.parse_args(argv)
    if args.cmd == "learn":
        brief = start_learning_session({"topic": " ".join(args.topic)})
        print(f"Target: {brief['target']}")
        print("Known:")
        for k in brief["known"]: print(f"* {k}")
        print(f"Likely starting point: {brief['likely_starting_point']}")
        print(f"Suggested first action: {brief['suggested_first_action']}")
        if brief.get("source_refs_available"):
            print("Sources available:")
            for s in brief["source_refs_available"][:5]: print(f"* {s['source']} p.{s['page']}")
    elif args.cmd == "lesson-status":
        print(lesson_status_text())
    elif args.cmd == "end-lesson":
        print(json.dumps(end_lesson(), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
