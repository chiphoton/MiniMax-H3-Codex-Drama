# Canvas usage and local RPC

The project picker initially places a collapsible `examples/` folder above projects. Selecting a bundled example caches current drafts and imports an unsaved editable copy into the active data folder, with a new project, chat session, and copied assets. It does not start generation or commit edits. Templates live at `<plugin-root>/examples/*.video-director.json` and remain unchanged. The `/canvas-examples` channel supports `list` and `get` with an exact listed filename in `id`.

Create a Video Project, then double-click blank canvas to open the searchable node menu. Add load-text/media/sketch nodes, TEXT WORKFLOW, IMAGE WORKFLOW, or ComfyUI video/audio nodes. Connect outputs to compatible inputs; connect an output to Preview or Save Output to inspect/download results. New text/image nodes choose Codex Plan. Refresh its account-specific models and variants from Settings → Connections or a node’s refresh button; adviser chat uses the same list. Effort follows the model’s reported default. Fast (priority) is an optional Settings-only choice, off by default. Explicit settings on imported projects are preserved.

The existing controls support pan/zoom, selection, undo/redo, copy/paste/duplicate, masks/sketches, Freeze, run selected/all/descendants, batches, Jobs, and project export/import. Edits are cached automatically for recovery across switches and restarts. **Save** commits the current graph. **Discard changes** restores the last explicit save and clears undo/redo; for a never-saved project it removes that copy and owned assets, preserving its Canvas chat. The picker marks unsaved projects with italics and an asterisk, supports drag or Alt+Up/Down ordering, and provides actions on each row. **Run** freezes a submission snapshot, schedules dependencies, and retains job/run history without committing later edits. **Tasks** defaults to all workflows and supports filtering, artifact downloads, snapshot opening/export, and removal of finished history. Its **⋯ → Inspect Property** dialog shows details and cancellation. The Canvas server owns one global queue across workflows and tabs, including dependency stages, triggers, repeats, and batch cases. Switching or closing a tab affects observation only; accepted work continues while the server and computer remain running. On restart, queued snapshots resume and interrupted active runs fail conservatively. Orderly shutdown cancels the active run and retains the queue.

The picker supports nested virtual folders, drag/drop moves, sibling keyboard reordering, and Multi-Select operations. Folder changes use the current layout revision. Asset selection links retained inputs or outputs across workflows; duplicates have independent references and share stored bytes. Never edit asset files or folder metadata directly.

Add **Batch Input** and **Batch Output** for text-line, file, or folder cases. A submission captures its graph, selected inputs, inclusive one-based range, and seeds before execution. Batch Output browses cases, exports TAR archives, and retries unfinished cases; completed cases stay immutable. See [batch processing](../../../docs/batch-processing.md) for limits, freeze behavior, and cancellation recovery.

After rebuilding Canvas, reload an open tab to pick up the current client. During the first upgrade from Canvas 0.2.0, finish or cancel runs before restarting: those older clients own their multi-stage schedulers. New server-owned runs survive tab reloads. Cached edits survive reloads.

**Gallery** shows inputs and retained outputs across all workflows, including drafts, with workflow filtering and text search. It does not switch or save the active project. Inspect image, video, audio, and text cards; image inspection supports pan, zoom, reset, and metadata. Video details use optional `ffprobe` on the Canvas host for FPS and embedded metadata, with browser dimensions/duration as a fallback. Image/audio/video inputs support file drops, Replace, Choose from assets, and Inspect without losing connections; text inputs offer UTF-8 Import, Clear, and character counts. Input changes support Undo. Node status displays execution progress and completion time/duration. Audio inspection has a seekable waveform. **Media Editor** trims audio/video, crops video, and exports frames through host FFmpeg. Export downloads a copy; Save replaces the selected reference; Save a copy imports a new output, preserving original media bytes.

Canvas chat receives a graph summary and optional image attachments. It provides advice through a separate per-project Codex SDK conversation; it does not automatically act on the graph. The Chat settings menu can bind a new conversation without deleting the project. Text/image workflow nodes invoke Codex separately to produce outputs. The image agent model is the Codex agent doing the work, not a direct image API model name.

## Inspect or edit from Codex

Run `node <plugin-root>/scripts/canvas.mjs <endpoint> [--file payload.json]`. `CANVAS_URL` or `--url` selects a non-default local port. Keep payload JSON in a file so prompts and paths are not reinterpreted by a shell. Common endpoints:

| Endpoint | Payload |
|---|---|
| `health`, `projects/list`, `providers/list`, `workflows/list`, `nodes/list` | `{}` |
| `projects/get` | `{"projectId":"UUID"}` |
| `projects/create` | `{"name":"Title","sessionId":"UUID"}`; first create a session using the sessions channel |
| `projects/save` | `{"projectId":"UUID","expectedRevision":1,"project":{...}}` |
| `projects/draft` | `{"projectId":"UUID","draft":{"name":"Title","graph":{...},"settings":{...}}}`; cache edits without committing; `draft:null` clears the draft |
| `projects/discard` | `{"projectId":"UUID"}`; restore the last save or remove a never-saved copy |
| `projects/organize` | Inspect `src/project-folders.js`; include `expectedRevision` from `projects/list.projectFolders` for folder creation, moves, reordering, and batch operations |
| `projects/reorder` | `{"projectIds":["UUID",...]}`; unlisted projects follow in their existing order |
| `gallery/list` | `{}`; input/output summaries across projects, including drafts |
| `assets/properties` | `{"assetId":"UUID"}`; audio/video details; also served at the asset URL plus `/properties` |
| `providers/check` | `{"providerId":"codex-plan"}` or an inspected provider ID |
| `workflows/import` | Inspect `src/workflow-store.js` for the manifest/bindings schema; import trusted ComfyUI API JSON |
| `nodes/install` | `{"pack":{...}}`; use the plugin-root `docs/custom-node-protocol.md` |
| `vd-runs/list`, `jobs/list` | `{}` for all workflows, or `{"projectId":"UUID"}` |
| `vd-runs/submit` | Captured `snapshot`, unique `runIds`, `projectId`, and `options`; inspect `src/workflow-scheduler.js` and `src/client/controller.ts` before constructing a submission |
| `vd-runs/cancel`, `vd-runs/resume`, `vd-runs/jobs` | `{"projectId":"UUID","runId":"UUID"}`; resume is for unfinished cases in a terminal batch |
| `batch-cases/list` | `{"projectId":"UUID","runId":"UUID"}` |
| `assets/list` | Optional `kind` filter; search retained assets before uploading duplicates |
| `media/edit` | `projectId`, `assetId`, `action`, and numeric `edit`; inspect `src/media-editor.js` for trim/crop/frame fields |
| `tasks/list` | `{}` — all workflow names, node titles, jobs, and run summaries |
| `jobs/get`, `jobs/cancel` | `{"projectId":"UUID","jobId":"UUID"}` |

The helper's default channel is `/video-director`. Use `--channel /canvas-sessions` for `list`, `create`, `get`, `rename`, `model`, `start`, or `cancel`. Session `create` accepts `{}` and returns its UUID. This is a Canvas conversation identifier, not a Codex desktop task ID.

Use `--channel /canvas-storage` for `info` (active/default paths and whether they can change), `open` (open the active folder in the system file manager), `choose` (native folder chooser; cancellation returns a null `dataDir`), `change` with `{"dataDir":"/absolute/new/folder","expectedDataDir":"/current/folder"}`, or `reset` with `{"expectedDataDir":"/current/folder"}`. Prefer Settings → Storage for changes so browser drafts are flushed first. The server copies to a new or empty folder, retains the original data, and refuses a change during active jobs, chats, or vd-runs. Saved workflows, drafts, and project ordering survive the move. Reset copies the latest data back to the default folder, keeping any existing default-folder contents in a sibling `.backup-…` folder.

Settings → Language switches the interface between English and Chinese immediately and remembers the preference in this browser. It does not change project names, prompts, or generated content.

Before an RPC graph write, account for unsaved browser changes. `projects/get` returns the saved graph and revision plus an optional `draft` containing the edited name, graph, and settings. Draft writes do not advance the saved revision, so revision checks alone cannot protect newer browser edits. Reconcile the draft and pending browser changes, apply a narrow edit, and save with `expectedRevision` only when a commit is intended; saving clears the stored draft. Reload the browser only after its edits are reconciled. Do not use `force` to bypass a revision conflict. For a live graph run, prefer browser Run to capture the current edits and submit immutable execution snapshots to the server. Do not reconstruct `jobs/start` payloads from guesses; consult `src/rpc.js` and `src/client/controller.ts` if an automation needs that interface.

Project archives deliberately retain the upstream format marker for compatibility. They carry graph/settings/assets, but no credentials or Harness chat history. Import creates a new local conversation. Built-in ComfyUI workflow definitions retain their IDs; custom definitions must be installed before importing a graph that references them.

For troubleshooting, inspect the specific failed job, selected provider/model, workflow bindings, and required input ports. A failing ComfyUI job may already have a `prompt_id`; check its queue/history before resubmitting an uncertain request. Never substitute generated placeholders for failed media. Use existing project outputs and resumable jobs when continuing work.
