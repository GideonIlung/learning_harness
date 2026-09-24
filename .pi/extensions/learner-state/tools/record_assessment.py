#!/usr/bin/env -S uv run python
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "bin"))
from learner_state import project_root, record_assessment
try:
    params = json.load(sys.stdin)
    print(json.dumps(record_assessment(project_root(), params), indent=2, ensure_ascii=False))
except Exception as e:
    print(json.dumps({"error": str(e)}, indent=2, ensure_ascii=False)); sys.exit(1)
