# Canvas 0.2.0: upstream v0.3.0 sync

Source: the local `DeepSeek-Harness-Video-Director` repository, registered in Codex as `deepseek-harness-dev`. Commit `0353b43c879b3f6bd13e2100320b4680bebca39e` is titled `v0.3.0: updated ui and added gallery`. Canvas's plugin and npm package versions are `0.2.0`; the upstream package manifest itself still says `0.1.2`, so the commit identifies this sync.

The previous migration recorded `3571ee801161e1870bc2ab49466f8d032fa869c2`. Upstream `d440c28` (v0.2.0) had already ported Canvas's language, storage, examples, and Codex model discovery changes back into Harness. This sync merges the subsequent feature changes and includes the v0.2.0 parameter-input keyboard/Safari focus fix.

| Upstream change | Codex integration |
|---|---|
| Gallery across all workflows | Input/output tabs, workflow and text filters, retained job results, draft inclusion, and nested inspectors use the local `/video-director` RPC channel. |
| Durable project drafts | Browser recovery is namespaced to `codex-canvas:draft:v1:`. Server drafts remain separate from explicit saves. New/imported/copied projects stay unsaved; Discard restores the last save or removes a never-saved copy. |
| Project picker and row actions | Persistent drag/keyboard ordering, unsaved count, shared actions, and background project operations retain local Canvas conversation bindings. |
| Image/video inspection and input replacement | Shared viewer, image pan/zoom, metadata, text import/clear, and undoable media replacement. The loopback server serves video `/properties` requests with existing origin checks, cancellation, and storage-move coordination. |
| Node status and timing | Execution stages, progress, finish time, and duration use job `startedAt` to exclude queue wait where available. Cached results and frozen nodes are preserved. |
| Storage changes | Drafts are flushed without becoming explicit saves. Saved graphs, drafts, project order, assets, chats, and connection settings travel together. |

Canvas retains its `.codex-plugin/plugin.json`, standalone HTTP host, local session store, Codex Plan text/image defaults, adviser chat, `CANVAS_*` settings, `.canvas-storage.json` locator, bilingual UI, and setup/doctor/CLI helpers. Harness's Cordis entry points, dependency injection, native chat transport, settings schemas, launcher, and close controls are not included. The existing archive marker remains unchanged for project import/export compatibility.

`upstream-lock.json` records hashes of the upstream originals for shared/adapted files at the exact commit. They are provenance hashes, not checksums of the Codex adaptations. No user projects, credentials, generated media, or dependency directories were copied from the source checkout. The original MIT license remains in place.

A subsequent Codex extension keeps workflow schedulers, queues, and job polling cached by project during canvas switches. Tasks now reads cross-project history through `tasks/list`, defaults to all workflows, filters by workflow, and routes actions back to the owning project. These changes extend the upstream v0.3.0 baseline.

Validation: `npm run check` builds the browser bundle, type-checks it, and runs 338 passing tests. The imported interaction tests use pinned `jsdom@29.1.1`; host-dependent tests run against Canvas. Coverage includes draft recovery and explicit saves, gallery filtering and accessibility, project ordering, media replacement, example isolation, Codex defaults/chat, storage moves, and MP4/WebM metadata over actual loopback HTTP. Browser checks use a temporary data directory, fixture model catalog, and simulated provider. They verify a workflow continues through its next stage while another canvas is selected, independent execution of another workflow, the global task list and filter, and restored results when returning to the first canvas.

A follow-up regression fix distinguishes new job results from history restoration. Clear Previews suppresses old output replay, while fresh results resume downstream Preview paths in both the editable canvas and execution snapshot, including Preview chains. This fixes `mediaInputs[0] contains no text or project asset` when an image feeds MiniMax H3 through a cleared Preview. Validation covers the image/prompt/video topology, frozen references, and a simulated replay of the original submitted graph.
