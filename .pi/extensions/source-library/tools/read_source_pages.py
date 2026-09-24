#!/usr/bin/env -S uv run python
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "bin"))
from source_library import project_root, read_pages  # noqa: E402

try:
    params = json.load(sys.stdin)
    for k in ("source", "start_page", "end_page"):
        if k not in params:
            raise ValueError(f"Missing required parameter: {k}")
    result = read_pages(project_root(), str(params["source"]), int(params["start_page"]), int(params["end_page"]))
    print(json.dumps(result, ensure_ascii=False, indent=2))
except Exception as e:
    print(json.dumps({"error": str(e)}, ensure_ascii=False, indent=2))
    sys.exit(1)
