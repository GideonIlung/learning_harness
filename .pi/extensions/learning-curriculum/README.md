# learning-curriculum Pi extension

Maintains a simple project-local concept map in `curriculum/concepts.json`.

## Data model

Each concept supports:

- `id`
- `name`
- `description`
- `prerequisites`
- `learning_objectives`
- `importance`
- `source_refs`
- `status`

## Commands

- `/curriculum` — concise overview with learner-state mastery when available
- `/learning-path <topic>` — dependency-aware path that skips strongly understood prerequisites
- `/build-curriculum` — creates `curriculum/proposed_curriculum*.json` from indexed sources; does not overwrite `concepts.json`

## Tools

Wrappers read JSON from stdin and return JSON on stdout:

- `get_curriculum`
- `get_learning_path`
- `update_curriculum`

V1 intentionally uses JSON only; no graph DB, embeddings, or ontology framework.
