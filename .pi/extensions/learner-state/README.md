# learner-state Pi extension

Maintains persistent, evidence-based learner state in the existing `learner/` directory.

- Append-only raw evidence: `learner/history.jsonl`
- Current derived state: `learner/mastery.json`

## Commands

- `/learner` → concise mastery overview and active misconceptions
- `/learner-history` → recent assessment/misconception evidence

## Tools

Tool wrappers read JSON from stdin and return JSON on stdout:

- `get_learner_state`
- `record_assessment`
- `record_misconception`
- `clear_misconception`

No extra dependencies are required.
