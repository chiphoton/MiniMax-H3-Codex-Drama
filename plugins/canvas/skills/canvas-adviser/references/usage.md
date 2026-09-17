# Canvas usage and local RPC

The project picker pins a collapsible `examples/` folder above projects. Selecting a bundled example caches current drafts and imports an unsaved editable copy into the active data folder, with a new project, chat session, and copied assets. It does not start generation or commit edits. Templates live at `<plugin-root>/examples/*.video-director.json` and remain unchanged. The `/canvas-examples` channel supports `list` and `get` with an exact listed filename in `id`.

Create a Video Project, then double-click blank canvas to open the searchable node menu. Add load-text/media/sketch nodes, TEXT WORKFLOW, IMAGE WORKFLOW, or ComfyUI video/audio nodes. Connect outputs to compatible inputs; connect an output to Preview or Save Output to inspect/download results. New text/image nodes choose Codex Plan. Refresh its account-specific models and variants from Settings → Connections or a node’s refresh button; adviser chat uses the same list. Effort follows the model’s reported default. Fast (priority) is an optional Settings-only choice, off by default. Explicit settings on imported projects are preserved.

The existing controls support pan/zoom, selection, undo/redo, copy/paste/duplicate, masks/sketches, Freeze, run selected/all/descendants, batches, Jobs, and project export/import. Edits are cached automatically for recovery across switches and restarts. **Save** commits the current graph. **Discard changes** restores the last explicit save and clears undo/redo; for a never-saved project it removes that copy and owned assets, preserving its Canvas chat. The picker marks unsaved projects with italics and an asterisk, supports drag or Alt+Up/Down ordering, and provides actions on each row. **Run** freezes a submission snapshot, schedules dependencies, and retains job/run history without committing later edits. **Tasks** lists runs and jobs across all workflows by default, with a workflow filter. Switching, creating, importing, or opening an example keeps background schedulers and job polling alive; outputs and drafts update their owning workflow. Different workflows can run concurrently while submissions within one workflow stay ordered. Task cancellation, retry, opening, export, and deletion use the owning workflow. Keep the browser tab open without reloading while its multi-node run scheduler is active. Already submitted jobs are owned by the server; closing the page stops further stages from being submitted.

After rebuilding or restarting Canvas, an already-open tab keeps its previous client until it is reloaded. Wait for active runs to finish, then reload; the workflow filter in **Tasks** confirms the current client is loaded. Cached edits survive the reload.

**Gallery** shows inputs and retained outputs across all workflows, including drafts, with workflow filtering and text search. It does not switch or save the active project. Inspect image, video, audio, and text cards; image inspection supports pan, zoom, reset, and metadata. Video details use optional `ffprobe` on the Canvas host for FPS and embedded metadata, with browser dimensions/duration as a fallback. Image/video inputs support Replace and Inspect without losing connections; text inputs offer UTF-8 Import, Clear, and character counts. Input changes support Undo. Node status displays execution progress and completion time/duration.

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
| `projects/reorder` | `{"projectIds":["UUID",...]}`; unlisted projects follow in their existing order |
| `gallery/list` | `{}`; input/output summaries across projects, including drafts |
| `assets/properties` | `{"assetId":"UUID"}`; video details; also served at the video's asset URL plus `/properties` |
| `providers/check` | `{"providerId":"codex-plan"}` or an inspected provider ID |
| `workflows/import` | Inspect `src/workflow-store.js` for the manifest/bindings schema; import trusted ComfyUI API JSON |
| `nodes/install` | `{"pack":{...}}`; use the plugin-root `docs/custom-node-protocol.md` |
| `vd-runs/list` | `{"projectId":"UUID"}` |
| `tasks/list` | `{}` — all workflow names, node titles, jobs, and run summaries |
| `jobs/get`, `jobs/cancel` | `{"projectId":"UUID","jobId":"UUID"}` |

The helper's default channel is `/video-director`. Use `--channel /canvas-sessions` for `list`, `create`, `get`, `rename`, `model`, `start`, or `cancel`. Session `create` accepts `{}` and returns its UUID. This is a Canvas conversation identifier, not a Codex desktop task ID.

Use `--channel /canvas-storage` for `info` (active/default paths and whether they can change), `open` (open the active folder in the system file manager), `choose` (native folder chooser; cancellation returns a null `dataDir`), `change` with `{"dataDir":"/absolute/new/folder","expectedDataDir":"/current/folder"}`, or `reset` with `{"expectedDataDir":"/current/folder"}`. Prefer Settings → Storage for changes so browser drafts are flushed first. The server copies to a new or empty folder, retains the original data, and refuses a change during active jobs, chats, or vd-runs. Saved workflows, drafts, and project ordering survive the move. Reset copies the latest data back to the default folder, keeping any existing default-folder contents in a sibling `.backup-…` folder.

Settings → Language switches the interface between English and Chinese immediately and remembers the preference in this browser. It does not change project names, prompts, or generated content.

Before an RPC graph write, account for unsaved browser changes. `projects/get` returns the saved graph and revision plus an optional `draft` containing the edited name, graph, and settings. Draft writes do not advance the saved revision, so revision checks alone cannot protect newer browser edits. Reconcile the draft and pending browser changes, apply a narrow edit, and save with `expectedRevision` only when a commit is intended; saving clears the stored draft. Reload the browser only after its edits are reconciled. Do not use `force` to bypass a revision conflict. For a live graph run, prefer browser Run so the existing dependency scheduler builds its immutable execution snapshots. Do not reconstruct `jobs/start` payloads from guesses; consult `src/rpc.js` and `src/client/controller.ts` if an automation needs that interface.

Project archives deliberately retain the upstream format marker for compatibility. They carry graph/settings/assets, but no credentials or Harness chat history. Import creates a new local conversation. Built-in ComfyUI workflow definitions retain their IDs; custom definitions must be installed before importing a graph that references them.

For troubleshooting, inspect the specific failed job, selected provider/model, workflow bindings, and required input ports. A failing ComfyUI job may already have a `prompt_id`; check its queue/history before resubmitting an uncertain request. Never substitute generated placeholders for failed media. Use existing project outputs and resumable jobs when continuing work.
