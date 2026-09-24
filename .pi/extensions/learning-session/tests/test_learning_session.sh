#!/usr/bin/env bash
set -euo pipefail
ROOT="$(mktemp -d)"
mkdir -p "$ROOT/curriculum" "$ROOT/learner" "$ROOT/.learning"
cat > "$ROOT/curriculum/concepts.json" <<'JSON'
{
  "version": 1,
  "concepts": {
    "algebra": {"id":"algebra","name":"Algebra","description":"","prerequisites":[],"learning_objectives":[],"importance":"core","source_refs":[],"status":"not_started"},
    "functions": {"id":"functions","name":"Functions","description":"","prerequisites":["algebra"],"learning_objectives":[],"importance":"core","source_refs":[],"status":"not_started"},
    "derivatives": {"id":"derivatives","name":"Derivatives","description":"","prerequisites":["functions"],"learning_objectives":[],"importance":"core","source_refs":[],"status":"not_started"}
  }
}
JSON
cat > "$ROOT/learner/mastery.json" <<'JSON'
{
  "concepts": {
    "Algebra": {
      "dimensions": {"recognition":0.9,"intuition":0.9,"formal_understanding":0.8,"application":0.8,"reasoning":0.7,"transfer":0.5},
      "evidence_counts": {"recognition":{"total":1},"intuition":{"total":1},"formal_understanding":{"total":1},"application":{"total":1},"reasoning":{"total":1},"transfer":{"total":0}},
      "active_misconceptions": []
    },
    "Functions": {
      "dimensions": {"recognition":0.7,"intuition":0.45,"formal_understanding":0.4,"application":0.25,"reasoning":0.0,"transfer":0.0},
      "evidence_counts": {"recognition":{"total":1},"intuition":{"total":1},"formal_understanding":{"total":1},"application":{"total":1}},
      "active_misconceptions": []
    }
  }
}
JSON
export LEARNING_SESSION_PROJECT_ROOT="$ROOT"
BRIEF=$(printf '{"topic":"derivatives","goal":"learn basics","available_time_minutes":20}' | uv run python .pi/extensions/learning-session/tools/start_learning_session.py)
echo "$BRIEF" | grep '"current_concept": "functions"' >/dev/null
# Wrong high-confidence answer -> misconception diagnosis recommendation.
REC=$(printf '{"recent_evidence":"Learner gave an incorrect answer with 95 confidence."}' | uv run python .pi/extensions/learning-session/tools/get_next_teaching_action.py)
echo "$REC" | grep 'DIAGNOSE_MISCONCEPTION' >/dev/null
# Strong performance -> transfer recommendation.
REC2=$(printf '{"recent_evidence":"Strong performance: correct without hints, high confidence correct."}' | uv run python .pi/extensions/learning-session/tools/get_next_teaching_action.py)
echo "$REC2" | grep 'ASK_TRANSFER' >/dev/null
# Event and status.
printf '{"event_type":"concept_introduced","concept":"functions","description":"Introduced function mapping intuition."}' | uv run python .pi/extensions/learning-session/tools/record_learning_event.py >/dev/null
uv run python .pi/extensions/learning-session/bin/learning_session.py lesson-status | grep 'Current concept: functions' >/dev/null
# End archive.
uv run python .pi/extensions/learning-session/bin/learning_session.py end-lesson | grep 'archive_path' >/dev/null
test ! -f "$ROOT/.learning/current-session.json"
ls "$ROOT/.learning/session-history"/*.json >/dev/null
echo "learning-session tests passed"
