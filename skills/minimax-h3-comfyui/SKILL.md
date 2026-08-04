---
name: minimax-h3-comfyui
description: Prepare, validate, submit, monitor, and retrieve MiniMax H3 text-to-video, first/last-frame image-to-video, and reference-to-video workflows on a local or self-hosted ComfyUI instance. Use when a user explicitly asks to run, generate, execute, queue, preview, or fetch MiniMax H3 work through ComfyUI. Uses pinned official Comfy-Org templates and patches known fields deterministically; it does not adapt arbitrary custom workflows.
---

# MiniMax H3 ComfyUI

Run a finished MiniMax H3 prompt through ComfyUI using bundled official T2V, I2V, or R2V workflows. Preserve the pinned graph unless the user explicitly overrides a declared field.

## Interpret control flags

Recognize these case-insensitive controls anywhere in the request:

- `[return=true]`, `[return=1]`: wait for completion and fetch results. This is the default.
- `[return=false]`, `[return=0]`: submit and return the `prompt_id` immediately.
- `[prompt_enhance=true]`, `[pe=1]`: improve the prompt through the matching MiniMax H3 prompt specialist before execution.
- `[prompt_enhance=false]`, `[pe=0]`: preserve the supplied prompt. This is the default.
- `[preview=true|false]`: show or hide the ComfyUI browser after loading the prepared workflow. This has no effect when `load_workflow=false`.
- `[load_workflow=true|false]`: replace the live canvas with the prepared workflow only when true. Default false. When false, stay headless: do not initialize or open a browser, and do not announce preview or canvas behavior.

Strip control flags before sending text to MiniMax H3.

Without an enhancement flag, treat the prompt as finished: do not silently rewrite, expand, translate, or “improve” it. If enhancement is enabled, load and apply exactly one matching specialist:

- T2V: `../minimax-h3-text-to-video/SKILL.md`
- I2V: `../minimax-h3-frame-to-video/SKILL.md`
- R2V: `../minimax-h3-reference-to-video/SKILL.md`

## Select the bundled workflow

- No controlling media: `assets/workflows/t2v.api.json`.
- One literal first frame, or literal first and last frames: `assets/workflows/i2v.api.json`.
- Media used for identity, style, motion, camera, performance, voice, music, or rhythm: `assets/workflows/r2v.api.json`.

Use the `.api.json` files for validation and execution. The matching untouched `.ui.json` files are provenance and browser-preview assets. Reject arbitrary attached workflow JSON in this version; custom-workflow adaptation is intentionally deferred.

## Execute the workflow

Read [references/runtime.md](references/runtime.md) before using ComfyUI. Follow it in order:

1. Resolve configuration and test reachability. A successful default connection check is silent.
2. Inspect uploaded assets and upload them through the matching ComfyUI media tool.
3. Resolve installed models conservatively; never download a model without explicit permission.
4. Run `scripts/prepare_workflow.py` to patch only the manifest-declared fields.
5. Validate the prepared API graph before submission.
6. Submit once. Respect the return behavior above. For awaited runs, prefer the live sampler ETA from ComfyUI's log stream to fixed-interval polling, while binding completion and errors to the exact `prompt_id`.
7. On completion, fetch the output video to a temporary or user-selected directory and return it with the `prompt_id`.

Do not submit a workflow while required media, a compatible model choice, or validation errors remain unresolved.

## Preserve official defaults

Unless explicitly supplied by the user or non-empty configuration, preserve the workflow's prompt-independent defaults for resolution, seed, sampler, scheduler, steps, denoise, reference sizing, model filenames, and output prefix.

Allowed deterministic patches are:

- prompt
- uploaded media filenames and reference connections
- width and height together
- duration, converted to the H3 `17k+5` frame grid at 24 fps
- seed
- compatible model filenames
- output filename prefix
- named sampler, scheduler, steps, denoise, and R2V reference-size overrides

Never patch fields by searching for example text or relying on UI coordinates. Use `assets/workflows/manifest.json` and the preparer script.

## Return a concise execution report

For completed jobs, return the selected mode, relevant settings, `prompt_id`, and fetched video. For asynchronous jobs, return the mode and `prompt_id` plus how to request status or results later. For failures, return the failed node/error, what was checked, and the smallest next action.

Do not claim the job completed merely because it left the queue; confirm its exact history entry or fresh output file.
