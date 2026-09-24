#!/usr/bin/env -S uv run python
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "bin"))
from source_library import project_root, search  # noqa: E402

try:
    params = json.load(sys.stdin)
    if "query" not in params or not isinstance(params["query"], str):
        raise ValueError("Missing required string parameter: query")
    result = search(project_root(), params["query"], int(params.get("max_results", 8)), params.get("source"))
    print(json.dumps({"results": result}, ensure_ascii=False, indent=2))
except Exception as e:
    print(json.dumps({"error": str(e)}, ensure_ascii=False, indent=2))
    sys.exit(1)
