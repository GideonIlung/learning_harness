#!/usr/bin/env bash
set -euo pipefail
ROOT="$(mktemp -d)"
mkdir -p "$ROOT/curriculum" "$ROOT/learner"
cat > "$ROOT/curriculum/concepts.json" <<'JSON'
{"version":1,"concepts":{"a":{"id":"a","name":"A","description":"","prerequisites":[],"learning_objectives":[],"importance":"core","source_refs":[],"status":"not_started"},"b":{"id":"b","name":"B","description":"","prerequisites":["a"],"learning_objectives":[],"importance":"core","source_refs":[],"status":"not_started"}}}
JSON
cat > "$ROOT/learner/mastery.json" <<'JSON'
{"concepts":{"A":{"dimensions":{"intuition":0.9,"formal_understanding":0.8,"application":0.8,"reasoning":0.7,"transfer":0.5},"evidence_counts":{"intuition":{"total":1},"formal_understanding":{"total":1},"application":{"total":1},"reasoning":{"total":1},"transfer":{"total":0}}}}}
JSON
export LEARNING_CURRICULUM_PROJECT_ROOT="$ROOT"
OUT=$(printf '{"target":"b"}' | uv run python .pi/extensions/learning-curriculum/tools/get_learning_path.py)
echo "$OUT" | grep '"id": "b"' >/dev/null
if echo "$OUT" | grep '"id": "a"' >/dev/null; then echo "strong prerequisite was not skipped" >&2; exit 1; fi
printf '{"id":"c","name":"C","prerequisites":["b"],"learning_objectives":["Explain C"]}' | uv run python .pi/extensions/learning-curriculum/tools/update_curriculum.py >/dev/null
printf '{"concept":"b","include_dependents":true}' | uv run python .pi/extensions/learning-curriculum/tools/get_curriculum.py | grep '"c"' >/dev/null
echo "learning-curriculum tests passed"
