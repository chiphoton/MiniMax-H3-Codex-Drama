# Canvas agent workspace

Canvas 0.6.0 adapts the upstream v0.6.0 workspace to the local Codex SDK. The chatbox uses your signed-in **Codex Plan** account and its discovered model catalog. Select a model below the composer; the gear's **Model settings** opens **Settings → Connections**. Each model uses its default reasoning effort. Optional Fast (priority) stays in Connections and defaults off.

## Skills and canvas edits

Type `$` or select **$ Skills** to choose `canvas-builder`, `layout-optimizer`, or `sketch-to-h3`. Arrow keys and Enter select a suggestion; Escape closes it. Code examples and escaped dollars are literal. Unknown or ambiguous skill names block submission with an actionable error. **Auto skills**, enabled initially, lets Codex invoke a matching built-in from a plain-language request.

The gear's **Manage skills** creates, imports, edits, versions, duplicates, exports, archives, and shares instructions. **Load in chat** pins a version; a later edit never silently replaces it. Instructions load through `vd_library` only when needed. **Unload** stops future activation but cannot erase prior chat context. Supporting files stay with each immutable version. Stored scripts are text resources and are not executed by the library.

Try `$canvas-builder Add a Text Input with an invented scene and connect it to Preview.` Plan-only requests stay in chat. Build requests use a revision-checked edit batch on the draft. **Canvas changes** shows browser and agent receipts, offers Inspect, and can undo a change while rejecting newer conflicting edits. Undo does not reverse provider costs or delete generated outputs.

`plan-edit` simulates proposed nodes and connections. `ports` inspects typed input/output handles. `layout` previews by default; `apply:true` applies an independently undoable arrangement using measured card geometry when a matching view is connected. Layout preserves connections and provider choices.

`$sketch-to-h3` builds the specialized empty-canvas sketch → ComfyUI reference image → Ollama prompt → MiniMax H3 video recipe. It validates wiring, duration, and stage layout without running providers. Use `canvas-builder` to customize other workflows. Ordinary TEXT WORKFLOW and IMAGE WORKFLOW nodes default to Codex Plan.

## Media and content access

Image previews offer **Add to chat**. Video previews offer **Add frames to chat**, which creates a six-frame contact sheet on the host with FFmpeg. Neither action sends a message. Explicit image attachments are numbered within each message; stable aliases remain available for tool arguments and historical references. Chat displays Markdown, local media previews, model labels, and expandable tool calls/results.

The gear's **Workflow access** initially permits metadata only. Enable its content toggle before requesting node text/media inspection or configured provider execution. Prompts, scripts, complete graphs, and media are omitted from automatic workflow context. Explicit attachments are shared when you send the message. Image review requires an image-capable Codex model; a contact sheet provides visual evidence, without audio.

## Scoped tools

All tools accept `{projectId?, command, args}` in Canvas chat. The Codex capability supplies and enforces the actual workflow and linked conversation. In a desktop task using `scripts/canvas.mjs`, include the current `projectId`, linked `sessionId`, and `protocol:"vd/1"` yourself; see [RPC usage](../skills/canvas-adviser/references/usage.md).

| Tool | Main commands |
|---|---|
| `vd_canvas` | `help`, `summary`, `query`, `nodes`, `edges`, `catalog`, `definition`, `ports`, `plan-edit`, `edit`, `layout`, `recipe`, `history`, `inspect`, `undo`, `assets`, `references`, `image`, `media`, `validate`, `run`, `jobs`, `cancel`, `save`, `read-result` |
| `vd_library` | `list`, `create`, `save`, `get`, `bind`, `load`, `invoke`, `active`, `unload`, `resource`, `archive`, `publish`, `read-result` |
| `vd_workspace` | `manifest`, `describe`, `call`, `view`, `view-status`, `storage`, `read-result` |
| `vd_quality` | `create`, `list`, `get`, `step`, `revise`, `evaluate`, `stop`, `read-result` |

Start with `vd_canvas summary` or `vd_workspace manifest`. Request `describe {name}` for an operation's schema. View commands need a connected canvas and return an acknowledgement state. Persistent canvas/library operations continue without an open browser during the active turn. Storage changes use the existing local storage service and are blocked during active chats, jobs, runs, or quality plans.

Automatic workflow context has a 2 KiB ceiling. Ordinary tool results default to 8 KiB, configurable from 1–16 KiB. Oversized values return a scoped `vd-result-reference`; use `read-result` for a projection or page. References expire after five minutes, a draft revision change, or restart. Query cursors are bound to the workflow, session, selection, and draft revision. Image results have a separate size limit.

## Quality iterations

Ask Codex to create a quality plan with explicit criteria and budgets. The host records the plan and enforces limits; the current agent supplies revisions and evidence:

```text
create → step → inspect outputs
                 ├─ accepted
                 ├─ needs-revision → revise → step
                 ├─ inspecting → evaluate with evidence
                 └─ stopped with a reason
```

Defaults are three iterations, twenty execution jobs, and ten minutes; maxima are ten, one hundred, and sixty respectively. Execution jobs include executable control nodes. These are execution limits, not monetary estimates. Separate run/job submissions are blocked while a plan is active.

Criteria include graph validity, successful execution, node/artifact counts, text inclusion, and perceptual checks. Perceptual reports require a verdict, confidence, explanation, and evidence identifying the current or explicitly reused output. Missing evidence cannot establish success. Low confidence becomes `needs-human`.

Revisions rerun changed nodes and descendants. Unchanged results can be reused with provenance in execution snapshots. Quality outputs remain in history until explicitly attached; browser polling does not overwrite the editable canvas. The best measured run is retained. Exhausted budgets, external edits, changed skill/model choices, cancellation failures, and non-improving results produce explicit stops. Batch workflows use the existing batch controls separately. Quality plans do not start new Codex turns or run autonomous background reasoning.

## Data and recovery

Managed data stays in the configured Canvas data folder:

```text
library/skills/<id>/versions/<revision>/   bundle.json, SKILL.md, supporting files
projects/<id>/library-bindings.json       selected skill versions
projects/<id>/agent-access.json           workflow content access
projects/<id>/operations/                 browser/agent receipts and inverses
projects/<id>/quality/                    quality plans and evidence
sessions/                                independent Codex chats and transcript images
```

Skills are private to their workflow until shared. Other workflows may select shared versions or copy them, but cannot modify their owner's record. Eight skills may be selected per chat; instruction bodies are limited to 12 KiB, with up to twenty supporting text files and 512 KiB of resource JSON. Skill bundles export separately from workflow archives.

The existing storage move copies the complete library, journals, sessions, and media. Queued workflow snapshots recover after restart; interrupted work is reconciled without blindly resubmitting provider jobs. Rebuild and reload the client together when upgrading. Tests and the debug fixture use synthetic temporary data, with no paid model calls.
