#!/usr/bin/env -S uv run python
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

DIMENSIONS = ["recognition", "intuition", "formal_understanding", "application", "reasoning", "transfer"]
DISPLAY_DIMS = [("intuition", "Intuition"), ("formal_understanding", "Formal"), ("application", "Application"), ("transfer", "Transfer")]
DIFFICULTY_WEIGHT = {"easy": 0.75, "medium": 1.0, "hard": 1.25, "transfer": 1.5}
VALID_DIFFICULTIES = set(DIFFICULTY_WEIGHT)


def project_root() -> Path:
    return Path(os.environ.get("LEARNER_STATE_PROJECT_ROOT", os.getcwd())).resolve()


def learner_dir(root: Path) -> Path:
    return root / "learner"


def mastery_path(root: Path) -> Path:
    return learner_dir(root) / "mastery.json"


def history_path(root: Path) -> Path:
    return learner_dir(root) / "history.jsonl"


def now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def clamp(x: float) -> float:
    return max(0.0, min(1.0, x))


def canonical(s: str) -> str:
    return " ".join(s.strip().split())


def load_mastery(root: Path) -> Dict[str, Any]:
    path = mastery_path(root)
    if not path.exists():
        return {"concepts": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return {"concepts": {}}
        data.setdefault("concepts", {})
        return data
    except Exception:
        return {"concepts": {}}


def save_mastery(root: Path, data: Dict[str, Any]) -> None:
    learner_dir(root).mkdir(parents=True, exist_ok=True)
    mastery_path(root).write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def append_history(root: Path, event: Dict[str, Any]) -> None:
    learner_dir(root).mkdir(parents=True, exist_ok=True)
    with history_path(root).open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


def default_concept() -> Dict[str, Any]:
    return {
        "dimensions": {d: 0.0 for d in DIMENSIONS},
        "evidence_counts": {d: {"correct": 0, "incorrect": 0, "total": 0} for d in DIMENSIONS},
        "active_misconceptions": [],
        "resolved_misconceptions": [],
        "last_updated": None,
        "recent_assessments": []
    }


def get_concept(data: Dict[str, Any], concept: str) -> Dict[str, Any]:
    concepts = data.setdefault("concepts", {})
    if concept not in concepts or not isinstance(concepts[concept], dict):
        concepts[concept] = default_concept()
    c = concepts[concept]
    c.setdefault("dimensions", {})
    c.setdefault("evidence_counts", {})
    for d in DIMENSIONS:
        c["dimensions"].setdefault(d, 0.0)
        c["evidence_counts"].setdefault(d, {"correct": 0, "incorrect": 0, "total": 0})
    c.setdefault("active_misconceptions", [])
    c.setdefault("resolved_misconceptions", [])
    c.setdefault("recent_assessments", [])
    return c


def confidence_factor(correct: bool, confidence: Optional[float]) -> float:
    if confidence is None:
        return 1.0
    conf = max(0.0, min(100.0, float(confidence))) / 100.0
    if correct:
        # High confidence helps, but low confidence means fragile knowledge.
        return 0.55 + 0.45 * conf
    # High-confidence incorrect answers are stronger evidence of misconception.
    return 0.75 + 0.75 * conf


def hint_factor(hint_level: Optional[int]) -> float:
    h = 0 if hint_level is None else max(0, min(4, int(hint_level)))
    return max(0.25, 1.0 - 0.18 * h)


def update_value(old: float, correct: bool, confidence: Optional[float], difficulty: str, hint_level: Optional[int]) -> float:
    diff_w = DIFFICULTY_WEIGHT.get(difficulty, 1.0)
    cf = confidence_factor(correct, confidence)
    hf = hint_factor(hint_level)
    if correct:
        # Move partway toward 1.0. One answer cannot create mastery from zero.
        rate = min(0.18, 0.08 * diff_w * cf * hf)
        return clamp(old + (1.0 - old) * rate)
    else:
        # Move downward. High-confidence wrong answers and high hint need hurt more.
        h = 0 if hint_level is None else max(0, min(4, int(hint_level)))
        rate = min(0.25, 0.09 * diff_w * cf * (1.0 + 0.10 * h))
        return clamp(old * (1.0 - rate))


def validate_assessment(p: Dict[str, Any]) -> None:
    if not isinstance(p.get("concept"), str) or not canonical(p["concept"]):
        raise ValueError("concept is required and must be a nonempty string")
    if not isinstance(p.get("assessment_type"), str) or not canonical(p["assessment_type"]):
        raise ValueError("assessment_type is required and must be a nonempty string")
    if not isinstance(p.get("correct"), bool):
        raise ValueError("correct is required and must be boolean")
    if p.get("dimension") not in DIMENSIONS:
        raise ValueError(f"dimension must be one of: {', '.join(DIMENSIONS)}")
    if "confidence" in p and p["confidence"] is not None:
        c = float(p["confidence"])
        if c < 0 or c > 100:
            raise ValueError("confidence must be between 0 and 100")
    if "hint_level" in p and p["hint_level"] is not None:
        h = int(p["hint_level"])
        if h < 0 or h > 4:
            raise ValueError("hint_level must be between 0 and 4")
    if p.get("difficulty", "medium") not in VALID_DIFFICULTIES:
        raise ValueError("difficulty must be easy, medium, hard, or transfer")


def add_misconception_to_concept(c: Dict[str, Any], misconception: str) -> bool:
    m = canonical(misconception)
    if not m:
        return False
    existing = {canonical(x).lower() for x in c["active_misconceptions"]}
    if m.lower() not in existing:
        c["active_misconceptions"].append(m)
        return True
    return False


def record_assessment(root: Path, params: Dict[str, Any]) -> Dict[str, Any]:
    validate_assessment(params)
    concept = canonical(params["concept"])
    dim = params["dimension"]
    difficulty = params.get("difficulty") or "medium"
    event = {
        "timestamp": now(),
        "event_type": "assessment",
        "concept": concept,
        "assessment_type": canonical(params["assessment_type"]),
        "correct": params["correct"],
        "confidence": params.get("confidence"),
        "difficulty": difficulty,
        "dimension": dim,
        "hint_level": params.get("hint_level", 0),
        "notes": params.get("notes"),
        "misconception": canonical(params.get("misconception", "")) or None,
    }
    append_history(root, event)
    data = load_mastery(root)
    c = get_concept(data, concept)
    old = float(c["dimensions"].get(dim, 0.0))
    new = update_value(old, params["correct"], params.get("confidence"), difficulty, params.get("hint_level", 0))
    c["dimensions"][dim] = round(new, 4)
    counts = c["evidence_counts"][dim]
    counts["total"] = int(counts.get("total", 0)) + 1
    if params["correct"]:
        counts["correct"] = int(counts.get("correct", 0)) + 1
    else:
        counts["incorrect"] = int(counts.get("incorrect", 0)) + 1
    if event["misconception"]:
        add_misconception_to_concept(c, event["misconception"])
    summary = {k: event[k] for k in ["timestamp", "assessment_type", "correct", "confidence", "difficulty", "dimension", "hint_level"]}
    c["recent_assessments"].append(summary)
    c["recent_assessments"] = c["recent_assessments"][-10:]
    c["last_updated"] = event["timestamp"]
    save_mastery(root, data)
    return {"ok": True, "concept": concept, "dimension": dim, "old_mastery": round(old, 4), "new_mastery": c["dimensions"][dim], "state": c}


def record_misconception(root: Path, concept: str, misconception: str, evidence: Optional[str] = None) -> Dict[str, Any]:
    concept = canonical(concept)
    m = canonical(misconception)
    if not concept or not m:
        raise ValueError("concept and misconception are required")
    event = {"timestamp": now(), "event_type": "misconception_recorded", "concept": concept, "misconception": m, "evidence": evidence}
    append_history(root, event)
    data = load_mastery(root)
    c = get_concept(data, concept)
    added = add_misconception_to_concept(c, m)
    c["last_updated"] = event["timestamp"]
    save_mastery(root, data)
    return {"ok": True, "concept": concept, "misconception": m, "added": added, "active_misconceptions": c["active_misconceptions"]}


def clear_misconception(root: Path, concept: str, misconception: str, evidence: Optional[str] = None) -> Dict[str, Any]:
    concept = canonical(concept)
    m = canonical(misconception)
    if not concept or not m:
        raise ValueError("concept and misconception are required")
    event = {"timestamp": now(), "event_type": "misconception_resolved", "concept": concept, "misconception": m, "evidence": evidence}
    append_history(root, event)
    data = load_mastery(root)
    c = get_concept(data, concept)
    lowered = m.lower()
    before = len(c["active_misconceptions"])
    c["active_misconceptions"] = [x for x in c["active_misconceptions"] if canonical(x).lower() != lowered]
    if lowered not in {canonical(x).lower() for x in c["resolved_misconceptions"]}:
        c["resolved_misconceptions"].append(m)
    c["last_updated"] = event["timestamp"]
    save_mastery(root, data)
    return {"ok": True, "concept": concept, "misconception": m, "cleared": len(c["active_misconceptions"]) < before, "active_misconceptions": c["active_misconceptions"]}


def overview(root: Path) -> Dict[str, Any]:
    data = load_mastery(root)
    out = []
    for name, c0 in sorted(data.get("concepts", {}).items(), key=lambda kv: kv[0].lower()):
        c = get_concept(data, name)
        out.append({
            "concept": name,
            "dimensions": {d: c["dimensions"].get(d, 0.0) for d in DIMENSIONS},
            "active_misconceptions": c.get("active_misconceptions", []),
            "last_updated": c.get("last_updated")
        })
    return {"concepts": out}


def concept_state(root: Path, concept: str) -> Dict[str, Any]:
    data = load_mastery(root)
    c = data.get("concepts", {}).get(canonical(concept))
    return {"concept": canonical(concept), "state": c} if c else {"concept": canonical(concept), "state": None}


def print_learner(root: Path) -> None:
    data = load_mastery(root)
    concepts = data.get("concepts", {})
    if not concepts:
        print("No learner concepts are currently tracked.")
        return
    print(f"{'Concept':28} {'Intuition':>9} {'Formal':>8} {'Application':>12} {'Transfer':>9}")
    print(f"{'-'*28} {'-'*9} {'-'*8} {'-'*12} {'-'*9}")
    active = []
    for name in sorted(concepts, key=str.lower):
        c = get_concept(data, name)
        vals = c["dimensions"]
        print(f"{name[:28]:28} {vals.get('intuition',0):9.2f} {vals.get('formal_understanding',0):8.2f} {vals.get('application',0):12.2f} {vals.get('transfer',0):9.2f}")
        for m in c.get("active_misconceptions", []):
            active.append((name, m))
    if active:
        print("\nActive misconceptions:")
        for name, m in active[:10]:
            print(f"- {name}: {m}")


def recent_history(root: Path, limit: int = 20) -> List[Dict[str, Any]]:
    path = history_path(root)
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()[-limit:]
    events = []
    for line in lines:
        try:
            events.append(json.loads(line))
        except Exception:
            pass
    return events


def print_history(root: Path, limit: int = 20) -> None:
    events = recent_history(root, limit)
    if not events:
        print("No learner history recorded yet.")
        return
    for e in events:
        ts = e.get("timestamp", "")
        typ = e.get("event_type", "event")
        concept = e.get("concept", "")
        if typ == "assessment":
            mark = "✓" if e.get("correct") else "✗"
            print(f"{ts}  {mark} {concept} [{e.get('dimension')}, {e.get('difficulty')}, conf={e.get('confidence')}, hint={e.get('hint_level')}] {e.get('assessment_type')}")
            if e.get("misconception"):
                print(f"    misconception: {e.get('misconception')}")
            if e.get("notes"):
                print(f"    notes: {e.get('notes')}")
        elif typ == "misconception_recorded":
            print(f"{ts}  ! {concept} misconception recorded: {e.get('misconception')}")
        elif typ == "misconception_resolved":
            print(f"{ts}  ✓ {concept} misconception resolved: {e.get('misconception')}")
        else:
            print(f"{ts}  {typ}: {concept}")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Maintain persistent learner state.")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("learner")
    ph = sub.add_parser("history")
    ph.add_argument("--limit", type=int, default=20)
    args = parser.parse_args(argv)
    root = project_root()
    if args.cmd == "learner":
        print_learner(root)
    elif args.cmd == "history":
        print_history(root, args.limit)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
