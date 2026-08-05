# MiniMax-H3 Drama skill configuration

[← English README](../README.md) · [中文 README](../README_zh.md)

This is the canonical user-facing reference for MiniMax-H3 Drama controls. It covers prompt-time flags, production behavior, ComfyUI configuration files, model and generation overrides, workflow routing, and production profiles.

## 1. Prompt-time controls

### Control flag summary

| Control | Applies to | Default | Effect |
|---|---|---|---|
| `[mode=fast]` | Drama Producer, Adviser | Guided | Make conservative assumptions and continue without questions or approval gates |
| `[return=true]` or `[return=1]` | ComfyUI execution | `true` | Wait for the exact job to finish, fetch its output, and return the video |
| `[return=false]` or `[return=0]` | ComfyUI execution | `true` | Submit once and immediately return the `prompt_id`; do not monitor or fetch |
| `[prompt_enhance=true]` or `[pe=1]` | ComfyUI execution | `false` | Improve the prompt through exactly one matching H3 prompt specialist before submission |
| `[prompt_enhance=false]` or `[pe=0]` | ComfyUI execution | `false` | Preserve the supplied prompt exactly apart from removing control flags |
| `[load_workflow=true]` | ComfyUI execution | `false` | Replace the live ComfyUI canvas with the prepared official workflow |
| `[load_workflow=false]` | ComfyUI execution | `false` | Stay fully headless; do not initialize or open a browser |
| `[preview=true]` | ComfyUI execution | `true`* | Show the ComfyUI browser after loading the workflow |
| `[preview=false]` | ComfyUI execution | `true`* | Keep any browser work in the background after loading the workflow |

`*` Preview is only meaningful when `load_workflow=true`. With workflow loading disabled, preview is forced off.

ComfyUI control flags are case-insensitive and may appear anywhere in the request. They are removed before the final text is sent to MiniMax H3. A ComfyUI control flag also counts as explicit execution intent when used through `minimax-h3-adviser`.

Do not invent bracket flags for other settings. State duration, dimensions, seed, profile, voice, captions, and deliverables in normal language, or use the JSON configuration described below.

### Guided mode vs fast mode

`minimax-h3-drama-producer` and `minimax-h3-adviser` start in guided mode.

| Skill | Guided behavior | Fast behavior |
|---|---|---|
| Drama Producer | Approve the compact production plan, then approve the visual lock before batch H3 generation | Record conservative assumptions and skip both approval gates |
| Adviser | Ask one high-impact question at a time, then confirm the shared brief | Ask no questions, route immediately, and label only material assumptions |

Natural-language fast-mode triggers also include:

- `use your best judgment` / `use your best judgement`;
- `help me handle the rest`;
- `skip the grilling`;
- `answer immediately`;
- `give prompt immediately`.

If a user approves the Drama Producer plan and explicitly says later confirmation is unnecessary, the producer may also skip the visual-lock gate.

### Return behavior

- `[return=true]` is synchronous from the user's perspective. The skill monitors the retained `prompt_id`, confirms the exact history entry, fetches the result, and returns the local video.
- `[return=false]` is asynchronous. The skill submits exactly once, returns the `prompt_id`, and stops. It does not poll, fetch, or infer future success.
- The wait ceiling comes from `runtime.wait_timeout_minutes` and cannot exceed 60 minutes. A timeout leaves the ComfyUI job running and returns its `prompt_id`.
- To resume an asynchronous job, ask Codex to check or fetch that exact `prompt_id`; the skill must not silently resubmit it.

### Prompt enhancement

Prompt enhancement is opt-in. With `[prompt_enhance=true]`, the execution skill chooses exactly one specialist:

| Workflow | Specialist |
|---|---|
| T2V | `minimax-h3-text-to-video` |
| I2V / first-last frame | `minimax-h3-frame-to-video` |
| R2V / multimodal references | `minimax-h3-reference-to-video` |

Without the flag, a supplied prompt is treated as finished and is not silently rewritten, expanded, translated, or "improved." If the Adviser has already created the final prompt, enhancement is not applied a second time.

### Workflow loading and preview matrix

| Request | Canvas | Browser | Typical use |
|---|---|---|---|
| `[load_workflow=false]` | Unchanged | Not opened | Default headless production |
| `[load_workflow=false] [preview=true]` | Unchanged | Not opened; preview is ignored | Same as default |
| `[load_workflow=true] [preview=true]` | Replaced with prepared workflow | Shown after load | Inspect or adjust the live graph |
| `[load_workflow=true] [preview=false]` | Replaced with prepared workflow | Kept in background | Load the graph without presenting the browser |

> `load_workflow=true` may replace unsaved changes on the live ComfyUI canvas. The skill warns before loading it.

### Ready-to-copy combinations

Default headless run that waits and returns the video:

```text
$minimax-h3-comfyui
Run this finished prompt with the attached first frame. [return=true]
```

Submit now and fetch later:

```text
$minimax-h3-comfyui
Queue this prompt and return the job ID. [return=false]
```

Enhance the prompt, load the graph, and show ComfyUI:

```text
$minimax-h3-comfyui
Generate this attached reference-led shot.
[prompt_enhance=true] [load_workflow=true] [preview=true]
```

Run a complete production without approval pauses:

```text
$minimax-h3-drama-producer
Use the tiktok-short-drama profile, keep voice and captions on, and deliver the
finished vertical master. [mode=fast]
```

## 2. Production behavior

Except for `[mode=fast]`, Drama Producer controls are expressed in normal language rather than bracket syntax.

| Setting | Accepted behavior | Notes |
|---|---|---|
| Primary profile | Built-in name or explicit profile path | Exactly one primary profile is resolved on top of `base-video` |
| Voice | `auto`, `on`, or `off` | User instruction overrides the selected profile; no paid voice service is called silently |
| Captions | `auto`, `on`, or `off` | Required captions make caption support a critical preflight check |
| Completion | Synchronous by default; asynchronous on explicit request | Asynchronous productions store prompt IDs and resume those exact jobs |
| Story expansion | Preserve by default | User story, dialogue, characters, product facts, claims, and brand facts are authoritative |
| Takes | One valid ordinary take; up to two valid key-shot takes | More than two valid takes per shot requires user approval |
| Delivery | Local only | The producer does not publish or upload the result |

Example:

```text
$minimax-h3-drama-producer
Use the commercial-ad profile and these approved product photos. Voice off,
captions on, 15-second 16:9 master plus cover. Do not invent product claims.
Use your best judgment.
```

## 3. ComfyUI JSON configuration

### Files and precedence

Configuration is optional. Later **non-empty** values win:

1. Built-in defaults.
2. User config: `~/.config/minimax-h3-comfyui/comfy-config.json`.
3. Project config: `<project-root>/.config/comfy-config.json`.
4. Explicit request flags and settings.

An empty string or `null` preserves the previous layer—normally the pinned official workflow default. `false` and `0` are real values and are not treated as empty.

Start from [`comfy-config.example.json`](../skills/minimax-h3-comfyui/assets/comfy-config.example.json). The exact schema is [`comfy-config.schema.json`](../skills/minimax-h3-comfyui/references/comfy-config.schema.json).

```json
{
  "connection": {
    "address": "localhost:8188"
  },
  "runtime": {
    "return": true,
    "preview": true,
    "load_workflow": false,
    "wait_timeout_minutes": 60
  },
  "models": {
    "fl2va": "",
    "ref2va": "",
    "text_encoder": "",
    "video_vae": "",
    "audio_vae": ""
  },
  "generation": {
    "width": null,
    "height": null,
    "duration_seconds": null,
    "seed": null,
    "filename_prefix": "",
    "sampler": "",
    "scheduler": "",
    "steps": null,
    "denoise": null,
    "ref_image_size": ""
  }
}
```

Unknown sections or fields are rejected instead of being ignored silently.

### `connection`

| Field | Type | Default | Meaning |
|---|---|---|---|
| `address` | string | `localhost:8188` | ComfyUI host and port or full HTTP(S) URL; a bare host is normalized to `http://...` |

The plugin's bundled [`.mcp.json`](../.mcp.json) also targets `http://localhost:8188`. If `connection.address` changes, the active MCP client's `COMFYUI_URL`/`--comfyui-url` target must be changed to the same normalized address. A mismatch is reported rather than sending work to the wrong server.

### `runtime`

| Field | Type / range | Default | Meaning |
|---|---|---|---|
| `return` | boolean | `true` | Wait and fetch (`true`) or submit and return the ID (`false`) |
| `preview` | boolean | `true` | Present the browser after loading; forced off when `load_workflow=false` |
| `load_workflow` | boolean | `false` | Load the prepared UI graph onto the live canvas |
| `wait_timeout_minutes` | number, `0 < n ≤ 60` | `60` | Maximum awaited monitoring time; timeout does not cancel the job |

Prompt-time flags override these values for the current request.

### `models`

| Field | Used by | Role |
|---|---|---|
| `fl2va` | T2V, I2V | MiniMax H3 FL2VA diffusion model |
| `ref2va` | R2V | MiniMax H3 REF2VA diffusion model |
| `text_encoder` | All modes | Compatible text encoder |
| `video_vae` | All modes | MiniMax H3 video VAE |
| `audio_vae` | All modes | MiniMax H3 audio VAE |

Each model is resolved in this order:

1. Explicit user choice.
2. Non-empty config value.
3. Pinned official filename, when installed.
4. The only installed compatible candidate.
5. Ask when multiple compatible candidates remain.
6. Report the missing role when none exist.

FL2VA and REF2VA are not interchangeable. The skill never downloads a model, installs a node, or restarts ComfyUI without explicit permission.

### `generation`

| Field | Type / range | Applies to | Meaning |
|---|---|---|---|
| `width` | integer ≥ 32, multiple of 32 | All | Output width; must be supplied together with `height` |
| `height` | integer ≥ 32, multiple of 32 | All | Output height; must be supplied together with `width` |
| `duration_seconds` | number, `0 < n ≤ 15` | All | Requested clip duration; converted to H3's `17k+5` frame grid at 24 fps |
| `seed` | integer ≥ 0 | All | Noise seed |
| `filename_prefix` | string | All | ComfyUI output filename prefix |
| `sampler` | string | All | Named sampler available in the connected workflow/runtime |
| `scheduler` | string | All | Named scheduler available in the connected workflow/runtime |
| `steps` | integer ≥ 1 | All | Sampling step count |
| `denoise` | number, `0 ≤ n ≤ 1` | All | Denoise strength |
| `ref_image_size` | `""`, `"match"`, or `"max"` | R2V only | Reference-image sizing policy; empty preserves the official default |

If a field remains empty or `null`, the pinned workflow value is preserved. Width and height are atomic: setting only one is a configuration error.

Explicit settings can also be stated naturally for one request:

```text
$minimax-h3-comfyui
Run this prompt at 768 × 1344 for 6 seconds with seed 42.
[return=true] [load_workflow=false]
```

## 4. Automatic workflow routing

The execution skill selects a bundled official workflow from the role of the supplied media:

| Route | Select when | Media contract |
|---|---|---|
| T2V | No media controls the result | Prompt only |
| I2V | An image is the literal first frame, optionally with an exact last frame | One first frame; optional one last frame |
| R2V | Media controls identity, style, design, motion, camera, performance, voice, music, or rhythm | Up to 9 images, 3 videos, and 3 standalone audio files |

For R2V, a reference video's frames and its paired audio are connected together. Give every reference a bounded role and state what it must not influence.

The plugin executes bundled `.api.json` graphs and retains untouched `.ui.json` graphs for provenance and canvas loading. Arbitrary attached workflow JSON is rejected in this version.

## 5. Production profiles

A production resolves:

```text
base-video + one primary profile + explicit user overrides
```

Built-in profiles:

| Profile | Defaults |
|---|---|
| `tiktok-short-drama` | 9:16, 15–90 seconds (45 target), 3–7 second shots, hook-first beats, captions required |
| `commercial-ad` | 16:9, 6–30 seconds (15 target), 2–6 second shots, product geometry locks, deterministic brand text |

Profile resolution order:

1. Explicit profile directory/path.
2. `<workspace>/.minimax-h3-drama/profiles/<slug>/`.
3. `~/.config/minimax-h3-drama/profiles/<slug>/`.
4. Built-in profiles.

Within a production, precedence is:

```text
current user instruction
> project override
> selected primary profile
> base-video
> built-in default
```

Never merge two primary profiles. Custom profiles are declarative data and must validate against [`profile.schema.json`](../skills/minimax-h3-drama-producer/references/profile.schema.json). See the [profile specification](../skills/minimax-h3-drama-producer/references/profile-spec.md) for every field and bundle requirement.

`minimax-h3-profile-distiller` saves a new profile under `outputs/<project>/profile/<slug>/` first. It installs into a project or personal registry only after explicit install/import intent, and it never overwrites an installed version without approval.

## 6. Specialist settings

The prompt specialists do not define additional bracket flags. State their creative controls directly in the request:

| Skill | Useful settings to state |
|---|---|
| `minimax-h3-text-to-video` | Duration, aspect ratio, shot count, timed action, camera, look, dialogue/audio, constraints |
| `minimax-h3-frame-to-video` | Exact first frame, optional exact last frame, allowed motion, locked composition/identity, duration |
| `minimax-h3-reference-to-video` | Asset-to-role mapping, forbidden influence, synchronization points, duration, aspect ratio |
| `minimax-h3-video-editor` | Every requested change paired with what must remain unchanged |

As a starting point, specialists recommend 5–15 second H3 clips, `768P` for iteration or `2K` for a final pass when the active workflow and hardware support it. T2V can use a fixed aspect ratio; I2V inherits the opening frame unless explicitly and compatibly handled by the executor.

## 7. Common problems

| Symptom | Check |
|---|---|
| `[preview=true]` does nothing | Add `[load_workflow=true]`; preview is ignored in headless mode |
| The wrong ComfyUI server is contacted | Make `connection.address` and the active MCP target identical |
| Width/height configuration fails | Supply both; each must be a multiple of 32 |
| Awaited run times out | The job is still running; keep and resume the returned `prompt_id` |
| Prompt changed unexpectedly | Use `[prompt_enhance=false]` or `[pe=0]`; enhancement is opt-in by default |
| R2V media is rejected | Stay within 9 images, 3 videos, and 3 standalone audio files |
| Attached custom workflow is rejected | This version executes only the pinned official T2V/I2V/R2V graphs |
| A URL reference is not downloaded | Supply a local file; URL downloading and sign-in are intentionally not automatic |

For runtime procedure and diagnostic behavior, see [`references/runtime.md`](../skills/minimax-h3-comfyui/references/runtime.md).
