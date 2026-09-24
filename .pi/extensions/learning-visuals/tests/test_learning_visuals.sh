#!/usr/bin/env bash
set -euo pipefail
ROOT="$(mktemp -d "/tmp/learning visuals test.XXXXXX")"
mkdir -p "$ROOT"
TOOL="$(cd "$(dirname "$0")/../tools" && pwd)/create_learning_visual.py"
printf '%s' '{"visual_type":"function_plot","title":"Parabola and tangent","description":"x^2 and tangent near x=1","spec":{"x_range":[-1,3],"y_range":[-1,5],"axis_labels":["x","y"],"functions":[{"expr":"x^2","label":"f(x)=x^2"},{"expr":"2*x-1","label":"tangent at x=1"}],"highlighted_points":[{"x":1,"y":1,"label":"(1,1)"}]}}' | LEARNING_VISUALS_PROJECT_ROOT="$ROOT" uv run python "$TOOL" > "$ROOT/fn.json"
printf '%s' '{"visual_type":"vectors","title":"Vector addition","description":"a plus b equals resultant","spec":{"show_axes":true,"vectors":[{"coords":[2,1],"label":"a"},{"start":[2,1],"coords":[1,2],"label":"b"},{"coords":[3,3],"label":"a+b"}]}}' | LEARNING_VISUALS_PROJECT_ROOT="$ROOT" uv run python "$TOOL" > "$ROOT/vec.json"
printf '%s' '{"visual_type":"proof_diagram","title":"Proof structure","description":"Assumption to conclusion","spec":{"nodes":[{"id":"a","label":"Assumption"},{"id":"b","label":"Construct sequence"},{"id":"c","label":"Establish bound"},{"id":"d","label":"Show convergence"},{"id":"e","label":"Conclusion"}]}}' | LEARNING_VISUALS_PROJECT_ROOT="$ROOT" uv run python "$TOOL" > "$ROOT/proof.json"
uv run python - "$ROOT" <<'PY'
import json, pathlib, sys
root=pathlib.Path(sys.argv[1]).resolve()
for name in ['fn.json','vec.json','proof.json']:
    data=json.loads((root/name).read_text())
    p=pathlib.Path(data['path']).resolve()
    assert p.exists(), p
    assert str(p).startswith(str(root/'.learning'/'visuals')), p
    assert p.suffix == '.png'
print('paths verified under .learning/visuals with spaced root')
PY
LEARNING_VISUALS_PROJECT_ROOT="$ROOT" uv run python "$(dirname "$0")/../bin/learning_visuals.py" visuals >/tmp/learning-visuals-list.out
grep -q 'function_plot' "$ROOT/.learning/visuals/manifest.jsonl"
grep -q 'vectors' "$ROOT/.learning/visuals/manifest.jsonl"
grep -q 'proof_diagram' "$ROOT/.learning/visuals/manifest.jsonl"
rm -rf "$ROOT"
echo "learning-visuals test passed"
