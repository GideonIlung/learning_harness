#!/usr/bin/env -S uv run python
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "bin"))
from learner_state import project_root, record_misconception
try:
    p = json.load(sys.stdin)
    print(json.dumps(record_misconception(project_root(), p.get("concept", ""), p.get("misconception", ""), p.get("evidence")), indent=2, ensure_ascii=False))
except Exception as e:
    print(json.dumps({"error": str(e)}, indent=2, ensure_ascii=False)); sys.exit(1)
