---
name: visualizer
description: Create and iteratively improve interactive browser-based science, math, physics, and engineering visualizations for learning. Use when the learner asks to see, simulate, rotate, animate, highlight, label, or change parameters of physical or mathematical objects.
---
# Learning visualizer

## Purpose
Build explanatory, interactive scenes. Favor physical and mathematical correctness over decorative realism. Work inside the project `visualizer/` directory.

## Setup
1. From the repository root, run `cd visualizer && npm install` once.
2. Run `npm run dev` in `visualizer/` (use a terminal that remains open).
3. Open the local URL Vite prints, normally `http://127.0.0.1:5173`.

## Workflow
1. Check `visualizer/scenes/incline.json` and `visualizer/src.js` before changes.
2. If the requested lesson matches the inclined-plane example, edit `scenes/incline.json` for title, parameters, annotations, and highlighted component. Vite hot-reloads changes.
3. For a new kind of physical system, create an appropriate scene implementation. Reuse three.js, Rapier, lil-gui, CSS2DRenderer and KaTeX. Do not claim that changing just the `scene` field supports arbitrary systems: new scene types need code.
4. Give rigid bodies stable, named IDs; add informative labels anchored to objects; show force/velocity/acceleration vectors, with clear units and colors; supply pause, reset, and user-adjustable parameters.
5. Derive or verify the physical model. Clearly distinguish exact geometric vectors, model forces, and schematic annotations. Avoid plotting forces that do not exist in the current state.
6. After modifying any scene, run `npm run build` and fix errors. Invite the learner to open/refresh the local page and observe the result.
7. When the learner gives feedback, edit the scene, reload it and explain the changed feature in one or two sentences. No live agent-to-browser communication is necessary.
8. When the learner says they are done, asks to kill/close the simulation, or no longer needs a custom visualization, stop the dev server and clean up any temporary or lesson-specific files/scripts created for that visualization unless the learner explicitly asks to keep them. Do not delete reusable framework files, package files, or source materials.

## First test
Use `/skill:visualizer Show me a block on a 30-degree incline. Highlight the block, label the normal force, and let me change friction and gravity.`

## Design constraints
- Keep dependencies lightweight and avoid large frameworks.
- Do not embed arbitrary untrusted scripts in lessons.
- Use a local dev server rather than `file://` URLs, especially in sandboxed browsers.
- Browser rendering requires WebGL and JS enabled.
- If you need a new type of simulation, implement it explicitly and test, rather than inventing an unsupported scene config.
