#!/usr/bin/env -S uv run python
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "bin"))
from learner_state import project_root, overview, concept_state
try:
    params = json.load(sys.stdin) if not sys.stdin.isatty() else {}
    concept = params.get("concept")
    result = concept_state(project_root(), concept) if concept else overview(project_root())
    print(json.dumps(result, indent=2, ensure_ascii=False))
except Exception as e:
    print(json.dumps({"error": str(e)}, indent=2, ensure_ascii=False)); sys.exit(1)
