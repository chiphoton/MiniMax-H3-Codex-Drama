# ComfyUI runtime procedure

The companion MCP is pinned in the plugin to `artokun/comfyui-mcp` 0.49.3. It may expose either direct tools or compact meta-tools. When only `list_tools`, `describe_tool`, and `call_tool` are visible, discover and invoke the named operation through those meta-tools.

## 1. Resolve configuration

Layer configuration in this order; later non-empty values win:

1. Built-in defaults.
2. User config: `~/.config/minimax-h3-comfyui/comfy-config.json`.
3. Project config: `<project-root>/.config/comfy-config.json`.
4. Explicit request flags and settings.

The built-in address is `localhost:8188`; normalize a bare host and port to `http://localhost:8188`. Empty strings and `null` preserve workflow defaults. See `assets/comfy-config.example.json` and `references/comfy-config.schema.json`.

Use `scripts/inspect_instance.py --mode <t2v|i2v|r2v> --project-root <project-root>` or the MCP `get_system_stats` operation to test reachability. If the default is reachable, continue without asking about configuration. If unreachable, warn once and offer only two choices: retry or update the applicable config address. Do not create a config file unless the user chooses to update it.

The bundled MCP entry targets `http://localhost:8188`. When a non-default address is configured, the MCP client's `COMFYUI_URL` must target that same normalized address; report a mismatch instead of sending work to the wrong server.

## 2. Load or preview the workflow

Treat `[load_workflow=false]` as a fully headless run. Do not initialize or open a browser, do not inspect browser state, and do not mention preview or canvas behavior in progress updates. Ignore `[preview]` while workflow loading is disabled.

Only handle browser preview when `[load_workflow=true]` is explicit. Warn that unsaved canvas changes may be replaced, then use an available live-canvas operation to load the prepared workflow. When preview is enabled and the Codex Desktop in-app browser is available, open the normalized address after loading; use picture-in-picture presentation when supported, otherwise use a normal in-app browser view. Outside Codex Desktop, return the URL instead of treating preview as an error.

When workflow loading is enabled but only headless tools exist, save a uniquely named UI copy with `save_workflow` and use the browser to open it; do not overwrite an existing saved workflow. When preview is explicitly disabled, keep any required browser work in the background and do not present the browser to the user.

## 3. Upload media

Inspect chat attachments before routing. Resolve each local attachment to an absolute path, then use:

- `upload_image` for I2V frames and R2V images
- `upload_video` for R2V videos
- `upload_audio` for R2V standalone audio

Use the returned ComfyUI filename in the preparer. I2V requires a first frame and accepts one optional last frame. R2V accepts at most 9 images, 3 videos, and 3 standalone audio files. The preparer connects a reference video's frames and its paired audio from `GetVideoComponents`.

Never guess the remote input directory or insert the chat attachment's local path into `LoadImage`, `LoadVideo`, or `LoadAudio`.

## 4. Resolve models conservatively

Required model roles are:

- T2V/I2V diffusion: `fl2va`
- R2V diffusion: `ref2va`
- all modes: `text_encoder`, `video_vae`, and `audio_vae`

Use `list_local_models` and verbose `get_node_info` for `UNETLoader`, `CLIPLoader`, and `VAELoader`, or use `scripts/inspect_instance.py`. Resolve each role in this order:

1. Explicit user choice.
2. Non-empty config choice.
3. Pinned official filename, when installed.
4. Exactly one installed filename compatible by role.
5. Ask the user when multiple compatible candidates remain.
6. Report the missing role when none exist.

Do not substitute an FL2VA model for REF2VA or vice versa. Do not download models, install nodes, restart ComfyUI, or change the user's installation without explicit permission.

## 5. Prepare and validate

Create the patched graph in a temporary directory or a user-requested output location:

```bash
python3 <skill>/scripts/prepare_workflow.py \
  --mode t2v \
  --project-root <project-root> \
  --prompt-file <prompt.txt> \
  --output <temporary-workflow.json>
```

Pass uploaded filenames with `--first-frame`, `--last-frame`, repeated `--reference-image`, repeated `--reference-video`, or repeated `--reference-audio`. Pass resolved filenames with `--fl2va`, `--ref2va`, `--text-encoder`, `--video-vae`, and `--audio-vae`.

Use `validate_workflow` on the resulting API graph. If it reports missing models, re-run the resolution procedure. If it reports a missing core H3 node, report that the connected ComfyUI version lacks MiniMax H3 support. Do not enqueue until validation has no errors.

## 6. Submit and wait

Call `enqueue_workflow` exactly once and retain its `prompt_id`.

For `[return=false]`, stop after successful submission and return the `prompt_id`. Do not wait, poll, fetch, or infer future success. If the user later asks about that ID, use `get_history`; on failure use `diagnose_run` and then `get_logs` only if needed.

For the default `[return=true]`, monitor the exact ID using queue status and `get_history`. The wait ceiling is the configured value, capped at 60 minutes. Keep the user updated during long runs and do not perform a single blocking wait longer than 60 seconds. On timeout, leave the job running and return the `prompt_id`.

On a failed or rejected run:

1. Call `diagnose_run` with the exact `prompt_id` when one exists.
2. Check `get_history` for the recorded traceback and node.
3. Use `get_logs` only for missing context.
4. Correct a deterministic filename or graph patch only when the intended choice is unambiguous; otherwise ask.

Never enqueue a second attempt silently.

## 7. Fetch results

Read the exact history entry. If `SaveVideo` does not register a media output, use `list_output_images` and match a fresh file by filename prefix and modification time. Fetch the video with `get_image`, setting `save_dir` to a temporary directory or a user-selected directory rather than the repository root.

In Codex Desktop, return the absolute local video path in a rendered media link together with the `prompt_id`. Outside Codex Desktop, return the saved absolute path and ComfyUI output reference.
