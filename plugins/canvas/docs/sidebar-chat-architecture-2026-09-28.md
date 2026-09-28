# Canvas chat and Codex workflow tools

Adapted from upstream `uncensored` v0.5.0. The standalone Canvas server replaces Harness tool registration and native conversation transport with local Codex SDK sessions and a temporary MCP connection.

`DirectorController.currentContext()` supplies a small project/revision/count envelope instead of serializing every script and prompt on every message. Selected reference aliases add metadata. Newly attached or explicitly used small images can enter the turn directly; audio/video/folder bytes remain in project storage for tool queries. Text and filenames are treated as data.

`ChatReferences` allocates aliases under a serialized per-project/session operation queue. Unsent aliases compact when a tile is removed; sent aliases retain their meaning for conversation history. Upload acknowledgements are separate from message delivery so failed sends can retry uploaded references. Reloading before a local file has uploaded requires reattaching that file. Manifests allow 5,000 files; Batch Input retains its 1,000-case limit. Original names stay separate from aliases.

The composer offers Image, Audio, Video, Folder and Node references, inline alias tokens, preview/removal, clipboard operations and folder search. Double-click a node title, drag it to chat, or choose **Add to Chat References**. The sidebar owns drag/drop events across its entire panel.

The `vd_canvas` MCP tool exposes `help`, `summary`, scoped/paged graph and catalog queries, references, text excerpts, assets, providers, properties, explicit images, transcription, media edits, atomic graph edits, validation, runs, job queries, cancellation and saving. For example:

```json
{"command":"edit","args":{"expectedDraftRevision":7,"edits":[{"op":"add","id":"reference","alias":"<Image 1>","position":{"x":0,"y":0}},{"op":"add","id":"preview","type":"core.preview","position":{"x":400,"y":0}},{"op":"connect","source":"reference","target":"preview"}]}}
```

Each active SDK turn receives a unique bearer capability through Codex's per-instance MCP configuration. It is scoped to the linked project and session, never returned by the browser's session view, never written into Canvas's session JSON, and revoked on completion/cancellation. The server overwrites identity supplied in tool arguments, validates the current project binding, checks asset ownership, and returns image content only for image-capable models. Shell access remains read-only; graph changes use the validated server commands. The adapter supports MCP initialization, tool discovery/calls, ping and cancellation notifications over JSON Streamable HTTP. See the [official Codex MCP configuration](https://developers.openai.com/codex/mcp).

Browser drafts and agent edits compare `expectedDraftRevision` under the same project write lock. Failed edit batches leave the graph unchanged. Send first flushes local drafts; observation adopts newer server drafts without overwriting unacknowledged local work. A conflict offers **Export local draft** and **Use Host version**. Recovery exports contain graph/configuration and asset references, not a portable media archive. Clients predating draft revisions remain compatible but require reload to gain concurrency protection.

Commands continue while the SDK turn is active even when the browser closes. Accepted runs remain with `WorkflowScheduler`. There is no new daemon that starts subsequent LLM turns. Generation still requires the user's request and configured providers; explicit transcription is limited to 25 MiB and 16,000 returned characters, text inspection to 2 MiB with bounded excerpts, and tool image inspection to 8 MiB. Visual quality control depends on the selected model; transcription alone cannot assess acoustic quality.

`test/codex-canvas-mcp.test.js` exercises the actual HTTP bridge with simulated SDK calls. `test/canvas-agent.test.js` covers scoped commands/references, atomic rollback, concurrent revisions, original filenames, image gating and browser-independent workflow execution. `scripts/debug/sidebar-chat.mjs` supplies a temporary browser fixture with simulated providers and a scripted MCP edit. Live paid model planning and generation quality are not covered by these tests.
