#!/usr/bin/env -S uv run python
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "bin"))
from learning_session import advance_learning_concept
try:
    params = json.load(sys.stdin) if not sys.stdin.isatty() else {}
    result = advance_learning_concept(params)
    print(json.dumps(result, indent=2, ensure_ascii=False))
except Exception as e:
    print(json.dumps({"error": str(e)}, indent=2, ensure_ascii=False)); sys.exit(1)
