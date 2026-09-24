#!/usr/bin/env bash
set -euo pipefail
ROOT="$(mktemp -d)"
mkdir -p "$ROOT/learner"
printf '{"concepts":{}}\n' > "$ROOT/learner/mastery.json"
printf '{"concept":"Bernoulli equation","assessment_type":"checkpoint","correct":true,"confidence":80,"difficulty":"hard","dimension":"application","hint_level":0,"notes":"applied to pipe flow"}' \
  | LEARNER_STATE_PROJECT_ROOT="$ROOT" uv run python "$(dirname "$0")/../tools/record_assessment.py" >/tmp/learner-state-assess.out
grep -q '"new_mastery"' /tmp/learner-state-assess.out
printf '{"concept":"Bernoulli equation","misconception":"pressure always decreases when velocity increases","evidence":"stated as universal"}' \
  | LEARNER_STATE_PROJECT_ROOT="$ROOT" uv run python "$(dirname "$0")/../tools/record_misconception.py" >/tmp/learner-state-misc.out
printf '{"concept":"Bernoulli equation","misconception":"pressure always decreases when velocity increases","evidence":"correctly included elevation and losses"}' \
  | LEARNER_STATE_PROJECT_ROOT="$ROOT" uv run python "$(dirname "$0")/../tools/clear_misconception.py" >/tmp/learner-state-clear.out
LEARNER_STATE_PROJECT_ROOT="$ROOT" uv run python "$(dirname "$0")/../bin/learner_state.py" learner >/tmp/learner-state-overview.out
LEARNER_STATE_PROJECT_ROOT="$ROOT" uv run python "$(dirname "$0")/../bin/learner_state.py" history >/tmp/learner-state-history.out
test "$(wc -l < "$ROOT/learner/history.jsonl" | tr -d ' ')" = "3"
grep -q 'Bernoulli equation' /tmp/learner-state-overview.out
grep -q 'misconception resolved' /tmp/learner-state-history.out
rm -rf "$ROOT"
echo "learner-state test passed"
