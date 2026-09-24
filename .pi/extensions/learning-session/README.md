# learning-session Pi extension

Coordinates existing project-local learning capabilities without replacing them:

- `source-library`
- `learner-state`
- `learning-curriculum`
- `learning-visuals`

The LLM remains responsible for teaching, explanations, question generation, reasoning, and pedagogical judgment. This extension only manages structured session state and action recommendations.

## State

Active state is stored in:

- `.learning/current-session.json`

Finished sessions are archived under:

- `.learning/session-history/`

Only structured metadata is saved; not the full conversation.

## Commands

- `/learn <topic>` — start an adaptive session
- `/lesson-status` — concise status overview
- `/end-lesson` — archive structured summary and remove active session

## Tools

- `start_learning_session`
- `get_next_teaching_action`
- `record_learning_event`
- `advance_learning_concept`

## Design limits

V1 is intentionally simple and topic-agnostic. It does not generate lessons, diagnostics, explanations, visuals, or assessment content. It recommends actions such as `ASK_DIAGNOSTIC`, `DRAW_DIAGRAM`, `REVIEW_PREREQUISITE`, or `ASK_TRANSFER`.
