# Canvas 0.5.0: upstream v0.4.1 and v0.5.0 sync

Source: [chiphoton/DeepSeek-Harness-Video-Director](https://github.com/chiphoton/DeepSeek-Harness-Video-Director), `uncensored` branch. Canvas was previously pinned to v0.4.0 `4964977426229c2760cf519197b40a0ec6181825`. This sync includes both subsequent release commits:

| Release | Exact commit | Changes |
|---|---|---|
| v0.4.1 | `a7cd2ea3e882c173c63e5d0db4260237c249fdbb` | Media preview performance, shared observation, task pagination and timing, HTTP range fixes |
| v0.5.0 | `dd33d909d21d4c525d2682af0254fb928ad4441c` | Multimodal chat references, canvas commands and draft conflicts, provider settings, asset pagination, numeric inputs |

Canvas's npm manifest, lockfile, plugin manifest and health endpoint now report **0.5.0**. The upstream npm manifest still reports 0.1.2; the release commits identify the synchronized versions. `upstream-lock.json` records hashes of upstream originals at the exact v0.5.0 commit. Adapted files intentionally differ from those hashes.

## Feature mapping

| Upstream change | Codex integration |
|---|---|
| Media performance | One workflow observation loop; unchanged snapshots retain identity; elapsed clocks update separately; offscreen video thumbnails detach sources; stable media metadata effects; satisfiable byte ranges clamp to EOF and abandoned streams stop reading. |
| Task history | `jobs/history` pages ten grouped records with a stable timestamp/ID cursor. Per-filter pages stay in controller memory until reload. Active observation is separate from historical paging; card cancellation, fixed completion durations, receipts and artifact downloads remain available. |
| Asset chooser | Server-side text/source filtering and fifteen-result pages, independent preview/selection, lazy thumbnails and retryable loading. |
| Chat references | Persistent Image/Audio/Video/Folder/Node aliases, token-aware editor and clipboard handling, title/context-menu node references, searchable folder preview, sequential uploads, historical alias preservation. Reservation calls are serialized before asynchronous project reads to keep concurrent numbering deterministic. |
| Canvas agent | Shared `editVdCanvas` graph operations and `createCanvasAgent` run in the standalone server. Queries are scoped/paged; edit batches are atomic; media, validation, queue execution, cancellation and saving reuse existing services. New text/image nodes retain Codex Plan defaults. |
| Codex transport | `CodexCanvasMcp` exposes `vd_canvas` over authenticated loopback Streamable HTTP. Each SDK turn gets a fresh project/session capability; cancellation or completion revokes it. Image results use MCP image content and the selected model's vision capability. Tool progress appears in the local transcript. |
| Concurrent editing | A separate `draftRevision` protects browser writes, agent edits, discard and save. Send flushes browser edits. The shared observer adopts newer remote drafts only when there are no unacknowledged local changes. Conflict recovery offers an export and explicit selection of the server version. |
| Connections | Autosave on blur/Enter, immediate Fast toggle, one refresh action, categorized ComfyUI model inventory, and Ollama/ComfyUI unloading. Keep Codex Plan naming, live account catalog, default effort and Settings-only Fast control. |
| Numeric controls | Partial/empty numeric drafts remain editable; valid values commit on blur or Enter with bounds and integer normalization. |

The original Harness `canvasTool` wrapper is replaced by the Codex MCP adapter, and native DSH chat transport remains excluded. Cordis registration, Harness entry points, dependency injection, launcher and packaging are not copied. The local HTTP host, same-origin checks, sessions, `CANVAS_*` environment settings, persistent storage migration, plugin skill, Codex image imports and cleared Preview propagation are retained. No dependency versions changed.

The SDK accepts per-instance Codex configuration overrides; its `mcp_servers.canvas` entry uses a loopback URL, a temporary authorization header, the `vd_canvas` tool allowlist and a bounded tool timeout. This follows [Codex MCP configuration](https://developers.openai.com/codex/mcp). No persistent user Codex config or plugin-wide MCP registration is necessary. The bridge overrides caller-supplied project/session identity with the owning turn's scope and rechecks the project's current binding on each command. Expired tokens fail authorization, and cross-origin requests still fail the HTTP host's existing checks.

Legacy unbound SDK conversations remain usable for advice without canvas tools. Bound chat can keep operating while its turn is active after the tab closes; this does not start autonomous new turns or install a daemon. Accepted workflow runs continue on the existing server queue.

## Upgrade and development

Finish or cancel active work, rebuild with `node scripts/setup.mjs`, restart Canvas with the existing data directory, and reload open tabs. Reloading matters because old clients that omit draft revisions cannot protect concurrent edits. For upgrades from Canvas 0.2.0 or earlier, the existing asset-layout migration and switch to server-owned workflow execution still apply. Keep the data directory outside the plugin installation and back it up before upgrading.

`npm run check` passed: browser/shared server builds, TypeScript and all **534 tests**. `git diff --check` verifies patch formatting. New and ported coverage includes references, atomic edits, draft conflict recovery, pagination, observation stability, numeric inputs, provider autosave/inventories and Codex MCP HTTP integration. The latter uses a simulated SDK client over real loopback HTTP to verify tool discovery, edits, project isolation, stale revisions, cancellation, token expiry, vision checks and thread resumption. It does not call a paid model.

Two synthetic browser fixtures remain available, both requiring FFmpeg:

```sh
node scripts/debug/sidebar-chat.mjs
node scripts/debug/media-preview.mjs
```

The sidebar fixture uses the actual standalone server and local chat adapter with simulated Codex/providers; sending a message creates a synthetic Text node through MCP. The performance fixture supplies a large synthetic canvas and paged task history. Both print their temporary URL/data root and remove that data on shutdown. Neither accesses user projects or sends paid generation requests.

Browser QA confirmed node-title references, chat-created nodes arriving on the canvas, provider autosave and categorized model lists, asset paging from 15 to 30 and filtered selection, and task paging from 10 to 20 with 20 retained after reopening. In the performance fixture, 40 video thumbnail elements had only 2 attached sources at the initial viewport. Neither fixture logged browser errors during these checks. These are integration checks, not a live model quality or production Safari performance benchmark. See [chat architecture](sidebar-chat-architecture-2026-09-28.md) and [media performance notes](media-preview-performance-2026-09-27.md).

The source checkout and existing user data were not changed. The original MIT license remains in place. The pre-existing untracked `docs/codex-sidebar-evaluation.md` was left untouched.
