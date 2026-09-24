# learning-visuals Pi extension

Generates disposable educational PNG visuals under `.learning/visuals/` using matplotlib and numpy from the project-root uv environment.

Run scripts with `uv run python ...`. Do not install packages globally.

## Commands

- `/visuals` — show recently generated visuals
- `/clear-visuals` — requires typing `CLEAR`; deletes files only under `.learning/visuals/`

## Tool

`create_learning_visual` accepts structured JSON:

```json
{
  "visual_type": "function_plot",
  "title": "Example",
  "description": "Short explanation",
  "spec": {}
}
```

Supported types: `function_plot`, `vectors`, `geometry`, `sequence`, `mapping`, `proof_diagram`.

The tool returns the PNG path, content type, and display guidance.

For this project environment, Pi is running in the VS Code integrated terminal, which does not support the needed inline image protocol. When `show_image` from `pi-imgview` is available, the teacher should display generated visuals immediately with:

```json
{
  "source": "<generated PNG path>",
  "mode": "browser"
}
```

Do not force Kitty or iTerm2 terminal graphics protocols in VS Code.
