# Canvas for Codex Drama

A local web canvas for planning and running video-production workflows. The engine is migrated from [chiphoton/DeepSeek-Harness-Video-Director](https://github.com/chiphoton/DeepSeek-Harness-Video-Director) (`dsh-video-director`) into this self-contained `plugins/canvas/` directory. It runs without DeepSeek Harness.

Canvas **0.4.0** follows the upstream release version and syncs v0.4.0 from the `uncensored` branch: a persistent server-owned workflow queue, Batch Input/Output, project folders, media editing, reusable assets, and an updated Tasks panel. See the [sync record](docs/upstream-sync.md) for the exact source commit and Codex adaptations.

**TEXT WORKFLOW** and **IMAGE WORKFLOW** default to **Codex Plan**, using the locally installed Codex CLI and its existing sign-in through the official Codex SDK. The model list is discovered from the signed-in CLI, including available variants. New selections use its reported default model and each model’s default reasoning effort. Existing projects retain their explicit provider and model selections. Video and audio use ComfyUI by default.

Native Codex images are imported from the current SDK thread's `generated_images/<thread-id>/` folder under the Codex home, even when no image payload appears in the SDK stream. The original Codex image stays in place; Canvas stores its own copy under the active data folder's `assets/` directory.

## Run from this checkout

Requires Node.js 22.19+ (22.x) or 24+, npm, and a signed-in Codex CLI. Image generation also requires native image generation and the `imagegen` skill in that CLI environment.

```bash
cd plugins/canvas
node scripts/setup.mjs
npm run doctor
npm start
```

Open **http://127.0.0.1:8765** in a browser or a Codex browser panel. `setup` installs the locked npm dependencies and builds the client. It does not install system packages, download model weights, alter Codex credentials, or start ComfyUI. If `codex` is absent from PATH, set `CANVAS_CODEX_PATH` to its executable. Use `codex login` interactively when needed.

Start the server in a normal terminal. When starting it from a Codex task, use an approved launch outside the task sandbox if `doctor` reports restricted runtime access. Codex needs access to its own local state and app server. An inherited task sandbox can prevent this despite a valid sign-in. If that happens, restart Canvas through the approved launch path with the same data directory; `/health` should report `codexRuntime.ok: true`.

## Codex plugin

The plugin manifest is [`plugins/canvas/.codex-plugin/plugin.json`](.codex-plugin/plugin.json); all engine sources and skill resources are inside this plugin root. The repository marketplace registers it as `canvas` alongside the existing production, style, and privacy plugins.

For an unpublished local checkout, install the marketplace **from the checkout root**:

```bash
codex plugin marketplace add /absolute/path/to/MiniMax-H3-Codex-Drama
codex plugin add canvas@chiphoton
```

If `chiphoton` is already configured from Git, adding the local checkout selects that local marketplace with the same name. Inspect `codex plugin marketplace list --json` first if you need to preserve the Git source. Once this change is published to the repository marketplace, the Git install path also supports `codex plugin add canvas@chiphoton`.

Start a new Codex task after installation, then ask:

```text
Use $canvas-adviser to check my environment, install the Canvas dependencies,
start the server, and open the canvas in Codex.
```

The adviser resolves paths relative to the installed skill. Plugin installation alone does not install npm dependencies; the adviser runs `scripts/setup.mjs` when setup is requested. It also explains node connections, imports trusted workflows, and diagnoses generation failures.

## First workflow

Open the project picker to find the collapsible **examples/** folder, initially above your projects. Choose **canvas-demo** to open an editable copy of the bundled sketch → image → text → video workflow. Current edits are cached as a draft before opening the example; each copy gets its own project, assets, and chat session. Opening an example does not run its generation nodes or commit unsaved edits.

Example archives live in [`examples/`](examples/). Add more `*.video-director.json` exports there to make them appear the next time the picker opens. The bundled files are never overwritten by project edits.

1. Create a Video Project. Double-click empty canvas to open the node menu.
2. Add **TEXT WORKFLOW** or **IMAGE WORKFLOW**. Its provider starts as **Codex Plan**. Enter a prompt and optionally connect image references.
3. Run the node, inspect its output, and connect it to another workflow or Preview / Save Output.
4. Press **Save** to commit canvas edits. Run captures the graph at submission without committing later edits. Export from the project menu to move a project with its assets.

Edits are cached automatically so drafts survive project switches and Canvas restarts. Unsaved projects appear in italics with an asterisk; new projects, imports, duplicates, and example copies remain unsaved until **Save**. **Discard changes** restores the last explicit save, keeping jobs and assets. Discarding a never-saved project removes that copy and its owned assets; its Canvas conversation remains. Create nested virtual folders from the picker toolbar, drag workflows between folders, or use **Alt+Up / Alt+Down** to reorder siblings. Multi-Select supports moving and deleting selected workflows/folders. Each row's **⋯** menu operates on that project without switching the active canvas. Folder edits use revision checks across tabs; they do not move media files.

All browser tabs on the same Canvas server share one workflow queue. Each submitted graph keeps its dependency stages, triggers, repetitions, and batch cases together. Switching projects, minimizing, reloading, or closing a tab does not stop an accepted run. Keep the Canvas server and computer running. **Run N** submits N separate snapshots; different workflows wait in submission order. On restart, queued snapshots resume, while interrupted active work is marked failed to avoid duplicate generation. An orderly server shutdown cancels the active run and preserves queued snapshots.

**Tasks** defaults to **All workflows**, with a workflow filter and compact run cards showing artifacts and elapsed time. The **⋯** menu downloads artifacts or an importable workflow snapshot, opens the submitted graph, removes finished history, or opens **Inspect Property**. Cancel active runs from the inspector. Actions always target the owning workflow.

**Batch Input → workflow nodes → Batch Output** runs one case per text line or selected file. Folder imports support filename regexes, subfolders, natural ordering, and an inclusive one-based range, up to 1,000 cases. Inputs, graphs, and per-case seeds are captured before submission. Batch Output browses retained cases, exports TAR archives, and resumes failed or pending cases without redoing completed cases. See [batch processing](docs/batch-processing.md) for frozen nodes, retry rules, and storage details.

**Gallery**, beside **Tasks**, shows inputs and retained outputs across **All workflows**, including drafts and results from deleted nodes. Filter by workflow or search filenames, node names, media types, and text. Inspect an item without losing the gallery's filters. Images support zoom, pan, reset, and metadata; video previews show dimensions, duration, frame rate, format, file size, and metadata. Detailed video properties require `ffprobe` from FFmpeg on the Canvas host; browser-readable dimensions and duration remain available without it.

Image, audio, and video inputs start empty and accept dropped files, **Replace**, or **Choose from assets**. The asset chooser searches retained inputs and outputs across workflows, creating an independent reference when media belongs to another workflow. Replacement retains connections and supports Undo. Duplicating a project shares stored bytes through independent asset references; deleting a copy preserves media still used elsewhere. Text inputs show a character count and offer UTF-8 **Import** and **Clear**.

Audio previews add a seekable waveform. Video and audio inspection open a **Media Editor** for trimming; video also supports crop presets and frame export. **Export** downloads a rendered copy, **Save** replaces the selected reference, and **Save a copy** adds a new output. Original stored media stays intact. These edits require `ffmpeg` and `ffprobe` on the Canvas host. Video Trim, Video Crop, and Extract Frame nodes also run locally through the workflow queue.

Running nodes display their stage or progress, then completion time and duration; queue wait is excluded from new job durations. Fresh outputs reopen cleared Preview chains without replaying cleared historical results or replacing frozen references.

The separate Codex adviser panel receives the current graph as context. It has its own resumable SDK conversation per Canvas project and provides advice; it does not directly edit the graph. It shares authentication with Codex, not the desktop task's conversation. Use workflow nodes for text/image generation, and the installed Drama skills in Codex for complete productions and finishing.

## Providers and storage

| Setting | Default / purpose |
|---|---|
| `CANVAS_PORT` | `8765`; server binds only `127.0.0.1` |
| `CANVAS_DATA_DIR` | Initial data directory: `$XDG_DATA_HOME/codex-canvas`, or `~/.local/share/codex-canvas`; saved Storage changes are followed on restart |
| `CANVAS_CODEX_PATH` | Optional executable override. Otherwise prefer the installed `codex` on PATH over npm’s bundled SDK CLI |
| `CANVAS_CODEX_MODEL` | Optional default model ID; must be present in the signed-in Codex catalog. Otherwise use the catalog default |
| `COMFYUI_URL` | `http://127.0.0.1:8188` |
| `OLLAMA_URL` / `OLLAMA_MODEL` | Optional Ollama connection; `http://127.0.0.1:11434` / `qwen3-vl` |
| `OPENAI_BASE_URL` / `OPENAI_API_KEY` | Optional API provider; separate from Codex Plan authentication |
| `OPENAI_MODEL` / `OPENAI_IMAGE_MODEL` | Optional API model overrides |
| `CANVAS_MINIMAX_H3_LICENSE_ACCEPTED` | Inherited `true`; set `false` to lock H3 generation |

**Settings → Connections → Codex Plan → Refresh models** queries the local CLI’s `app-server` `model/list` method, following all pages and excluding hidden entries. Text nodes, image nodes, and adviser chat share this catalog; image workflows and text nodes with image references exclude models that report text-only input. Models also refresh when Canvas loads and when a generation needs a catalog older than five minutes. The last successful list is stored in `codex-models.json` in the data folder for offline use; refresh failures are shown and never replaced with a built-in list. If a saved model is no longer available, choose another explicitly.

**Fast (priority)** appears only in **Settings → Connections → Codex Plan**, defaults **off**, and is remembered with connection settings. It applies to supporting models across text/image nodes and chat, with increased usage; other models keep Standard speed. Canvas explicitly overrides a personal Codex Fast default when this switch is off. Reasoning effort always follows the selected model’s catalog default, without a separate control.

Provider overrides entered in **Settings → Connections** are saved in `provider-settings.json` under the data directory with owner-only permissions. They override environment defaults. Secrets are stored locally in that file and never returned in the provider catalog. Keep the data directory outside the installed plugin cache so upgrades preserve projects, jobs, media, and conversations. Back up the entire data directory or export individual projects. Assets are organized under `assets/inputs/`, `assets/inputs/sketch/`, `assets/inputs/mask/`, and `assets/outputs/`. On first launch, legacy flat asset files are migrated with hash verification and a recovery journal; project asset IDs and URLs remain stable.

**Settings → Language** switches the interface between English and Chinese immediately. The preference is remembered in the current browser; the browser language is used initially. Project names, prompts, and generated content stay as written.

**Settings → Storage** puts **Open in Finder / File Explorer**, **Change folder**, and **Reset** beside the current data folder. **Change folder** opens the native folder chooser; select a new or empty folder. Canvas flushes cached drafts, copies the projects, folder layout, media, run snapshots and case records, chats, and connections, and switches to the copy immediately. It preserves the distinction between saved workflows and drafts. **Reset** copies the latest data back to the original default folder (the initial `CANVAS_DATA_DIR`, or the platform default). Existing contents of that default folder are retained in a sibling `.backup-…` folder. Previous data folders remain as backups. Active generations, chats, and canvas workflows must finish or be cancelled first. Linux folder selection requires Zenity or KDialog in a desktop session.

The original launch directory keeps a small `.canvas-storage.json` locator, so subsequent starts with the same `CANVAS_DATA_DIR` follow the new location. Keep that locator or launch directly with `CANVAS_DATA_DIR` pointing to the new folder. A missing destination drive produces an explicit startup error. To restore a backup, stop Canvas and remove its `.canvas-storage.json` locator if present before launching against the backup folder. `/health` and the Storage tab report the active `dataDir`.

`npm run doctor -- --probe` adds read-only checks of Canvas and ComfyUI, reporting Codex state access separately for the doctor and the running Canvas server. Refreshing Codex models verifies local runtime access and requests the account’s model catalog without starting a model turn; the first generation verifies actual account/model/image access. Missing Ollama or ComfyUI does not prevent Codex Plan text/image use.

The included [`custom_nodes/`](custom_nodes/) documents are declarative canvas node packs and ComfyUI workflow JSON, not Python extensions or model weights. The H3 video/audio and Qwen/Z-Image workflows need compatible models and ComfyUI node packages on your own server. See [environment guidance](skills/canvas-adviser/references/environment.md) and the [node protocol](docs/custom-node-protocol.md).

## Development and migration

```bash
npm run check
node scripts/canvas.mjs health
node scripts/canvas.mjs projects/list
```

The CLI helper accepts `--file payload.json` for an RPC payload. See [usage and RPC guidance](skills/canvas-adviser/references/usage.md) before editing saved graphs.

`src/client/` contains React/XYFlow canvas code. The build also emits `dist/workflow-execution.js`, sharing graph planning, request compilation, and output propagation with the server scheduler. Both generated bundles are required to start Canvas. `src/server.js`, `src/local-settings.js`, and `src/chat-sessions.js` replace Harness hosting, configuration, and sessions. The provider/runtime/store modules retain the original vd-workflow semantics and API names. The legacy `deepseek-harness-video-director-project` archive marker is intentionally preserved for import/export compatibility; exported graphs import without bringing across a Harness conversation or credentials.

The original checkout is unchanged. No user projects, generated media, caches, credentials, or `node_modules` were migrated. [`upstream-lock.json`](upstream-lock.json) records the synchronized source commit and upstream file hashes; Codex adaptations can differ from those hashes. [`LICENSE`](LICENSE) retains the upstream MIT notice. See [`NOTICE.md`](NOTICE.md) for provenance.
