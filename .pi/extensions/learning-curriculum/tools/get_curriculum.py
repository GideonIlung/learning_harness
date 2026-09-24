#!/usr/bin/env -S uv run python
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "bin"))
from learning_curriculum import get_curriculum
try:
    print(json.dumps(get_curriculum(json.load(sys.stdin) if not sys.stdin.isatty() else {}), indent=2, ensure_ascii=False))
except Exception as e:
    print(json.dumps({"error": str(e)}, indent=2)); sys.exit(1)
