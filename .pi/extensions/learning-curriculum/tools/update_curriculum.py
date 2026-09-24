#!/usr/bin/env -S uv run python
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "bin"))
from learning_curriculum import update_curriculum
try:
    print(json.dumps(update_curriculum(json.load(sys.stdin)), indent=2, ensure_ascii=False))
except Exception as e:
    print(json.dumps({"error": str(e)}, indent=2)); sys.exit(1)
