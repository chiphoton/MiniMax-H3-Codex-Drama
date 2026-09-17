---
name: canvas-adviser
description: Set up, launch, troubleshoot, and use the local Codex Drama web canvas. Apply when the user asks about the Canvas plugin, its environment, vd-workflows, provider connections, project import/export, or Codex Plan text/image nodes. For full video production, use available Drama production skills.
---

# Canvas adviser

Help the user run and use the self-contained Canvas plugin. Resolve the plugin root as **two directories above this SKILL.md's containing directory**; it contains `package.json`, `scripts/`, and `src/`. Do not assume the current working directory or a fixed plugin-cache version.

For installation, launch, or environment failures, read [environment.md](references/environment.md). Run `node <plugin-root>/scripts/doctor.mjs --json` first; add `--probe` when checking existing services. Resolve missing prerequisites within the user's request, run the bundled setup helper when dependencies/build are absent, start the loopback server, verify `/health`, and open its URL in a Codex browser panel when available. Use an explicit stable data directory outside the plugin cache. Installation requests authorize the required npm dependency setup; do not repeatedly ask for permission already given.

For canvas operation, graph changes, workflow imports, or generation failures, read [usage.md](references/usage.md). Inspect the current project and provider/node catalogs before choosing IDs or editing it. Preserve explicit project and node model choices. New TEXT WORKFLOW and IMAGE WORKFLOW nodes use `codex-plan` by default, with the signed-in Codex catalog’s default model and the selected model’s default reasoning effort. Codex Plan uses the local Codex CLI sign-in and needs no Base URL or API key.

The browser adviser chat is a separate SDK conversation, not the current Codex app task. It advises on the graph and cannot directly mutate the live canvas. To change the canvas from this task, use the browser or the local JSON RPC helper. Edits are cached separately from the last explicit Save; `projects/get` may include a `draft`, and pending browser edits may be newer. Reconcile both before writing. New projects and example copies remain unsaved until Save; Discard restores the last save or removes a never-saved copy. Run generation when the user requests it; an environment check alone does not authorize a paid generation.

Distinguish a registered **vd-node**, its containing **vd-workflow**, and the executable **comfyui-workflow** selected by a ComfyUI provider. Importing a JSON node pack does not install Python custom nodes or model weights. Use available MiniMax H3 Drama skills for production planning, model/workflow setup, and finishing when the task needs them; Canvas setup and Codex Plan nodes do not require those companion plugins.

Report the usable URL, actual data directory, checks performed, and any specific remaining blocker. Never report generation capability as verified just because the model catalog is present. Do not read or print authentication files or API keys; `codex login status` is sufficient for sign-in diagnosis.
