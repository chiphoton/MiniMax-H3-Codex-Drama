# Runtime procedure

Use the plugin's pinned `comfyui-mcp@0.49.3` connection. It may expose direct operations or compact `list_tools`, `describe_tool`, and `call_tool` meta-tools.

## 1. Resolve shared configuration

Read the same files as `minimax-h3-comfyui`, with later non-empty values winning:

1. Built-in defaults.
2. `~/.config/minimax-h3-comfyui/comfy-config.json`.
3. `<project-root>/.config/comfy-config.json`.
4. Explicit invocation flags.

Use `connection.address`, the complete `runtime` section, `generation.seed`, `models.qwen_checkpoint`, and `models.qwen_lora`. Defaults are `localhost:8188`, the model filenames pinned in the workflow, `return=true`, `preview=true`, `load_workflow=false`, and a 60-minute wait ceiling. When workflow loading is false, force effective preview to false and remain headless.

## 2. Preflight the instance

Test reachability with `get_system_stats` or an equivalent operation. Inspect node information for:

- `TextEncodeQwenImageEditPlusAdvance_lrzjason`
- `CheckpointLoaderSimple`
- `LoraLoaderModelOnly`
- `KSampler`
- `VAEDecode`
- `PreviewImage`
- `ConditioningZeroOut`
- `Image Comparer (rgthree)` only when loading the UI workflow

List local models and confirm the effective checkpoint under `checkpoints` and LoRA under `loras`. Prefer an explicit user setting, then shared config, then the pinned filenames. Do not substitute a similarly named model automatically.

If the instance is unreachable or a dependency is absent, stop before upload/enqueue and show the matching section of `comfyui-workflow-install.md`.

## 3. Upload images

Resolve one or two attachments to absolute local paths. Upload each with `upload_image` in attachment order. Use only the returned ComfyUI filenames in the workflow; never write local paths into `LoadImage`.

## 4. Prepare reproducible workflows

Create a unique result directory outside the skill, preferably `<project-root>/outputs/qwen-image-edit/<timestamp>/`, or a temporary directory when the user did not request project output. Write the effective prompt to `prompt.txt` without a BOM or an added newline. On the default pass-through path, the file contents must exactly match the prompt payload defined in `SKILL.md`; do not normalize whitespace or Unicode.

Run:

```bash
python3 <skill>/scripts/prepare_workflow.py \
  --project-root <project-root> \
  --image <uploaded-image-1> \
  [--image <uploaded-image-2>] \
  --prompt-file <result-dir>/prompt.txt \
  --output-api <result-dir>/workflow.api.json \
  --output-ui <result-dir>/workflow.ui.json
```

Add explicit `--checkpoint`, `--lora`, or `--seed` only when selected by the user or resolved config. Do not patch target size, VL size, crop, sampler, scheduler, steps, CFG, denoise, LoRA strength, or the system instruction. After preparation, verify that both workflow prompt fields equal `prompt.txt` exactly before enqueueing.

## 5. Validate and optionally load

Validate the prepared API workflow. Treat missing filenames as model-resolution failures and missing class types as node-installation failures.

When `[load_workflow=true]`, warn that the current canvas may be replaced, then load `workflow.ui.json` with the available live-canvas operation. If only saved-workflow operations exist, save under a unique name and open that workflow. Present the ComfyUI browser only when effective preview is true; otherwise keep required browser work in the background.

## 6. Enqueue and monitor

Enqueue the validated API workflow exactly once and retain its `prompt_id`.

- With `[return=false]`, return immediately with the ID and prepared workflow paths.
- Otherwise, monitor that exact ID using execution events, queue state, and history. Prefer scoped live progress. Never block for more than 60 seconds without a user update.
- On failure, call `diagnose_run`, inspect exact history, and read logs only as needed. Include a link to `comfyui-workflow-install.md`; quote its relevant corrective section when the failure is environmental. Never submit a second attempt silently.

The configured wait ceiling is capped at 60 minutes. On timeout, leave the job running and return the ID.

## 7. Fetch and return the result

Read the exact history entry and fetch the generated image produced by API node `16` (`PreviewImage`). Save it to the result directory. Return the rendered image, `prompt_id`, effective prompt, whether enhancement was enabled, model filenames, and links to both prepared workflows.

If no output is registered, diagnose the exact job and include the installation-guide link in the failure report.
