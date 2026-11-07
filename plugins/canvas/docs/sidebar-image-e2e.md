# Sidebar image generation and editing test

Verified November 8, 2026 using the real Canvas left sidebar, SDK 0.167.0, the signed-in app CLI, and GPT-6.1 Sol on Standard service. The server used an isolated `.canvas-data-sidebar-e2e` directory; no graph was pre-seeded and no provider was mocked.

## Request and outcome

The prompt entered in the sidebar was:

> Build and run a workflow once: generate a red ceramic mug on a white table, then edit that image to make only the mug blue. Use Codex Plan for both image steps and add a preview for each result.

Workflow content access was enabled for this synthetic project before sending. The agent created two Codex Plan image nodes, connected the first output to the second node's reference input, added two previews, validated the graph, and submitted one Host workflow run.

| Stage | Result | Duration |
|---|---|---|
| Text to image | Red ceramic mug on a white table; PNG imported into Canvas | 35.5 seconds |
| Image to image | Referenced the first output and changed the mug to blue; PNG imported into Canvas | 50.9 seconds |

Both previews displayed their respective outputs. Visual inspection confirmed that the edit preserved the mug's shape, framing, table, and shadows while changing the glaze color. The project is saved as **Sidebar image generation and edit test**, ID `e019f7d8-74c1-4f86-9fe8-c0aa880ebb7c`.

The completed run is `924fdf3e-ce89-45b1-9d02-e49f75863568`. Exactly two generation jobs were created. Their output IDs are `b8c47c12-0249-4737-bad9-157320e2611e` (red) and `9d8c9d8d-e633-4554-8b70-8026ad9563f0` (blue). Test data and images are ignored by Git.

## Issues found and corrected

1. **MCP approval mismatch.** The initial live attempt could not call even `help` because the noninteractive SDK uses `approvalPolicy: "never"` and the CLI required MCP approval. The temporary Canvas MCP configuration now explicitly approves only its four enabled, capability-scoped tools. The filesystem sandbox, other servers' policies, per-project content/run gate, cross-project checks, and token revocation remain in effect. The retry successfully built and ran the graph. The configuration uses the [documented per-tool approval option](https://learn.chatgpt.com/docs/extend/mcp).
2. **Edit mode was undiscoverable.** The first graph used an editing prompt and the correct image reference, but the second card retained its default Generate label. The tool schema and image-node definition now expose `imageMode`, with generate/edit validation and a generated-node default. A sidebar follow-up changed the second node to Edit and saved the workflow while preserving both outputs. No generation was repeated. A regression checks the `$Edit Image$` submission and reference asset wiring.
3. **Follow-up transcript collisions.** CLI item IDs can restart when an SDK thread resumes. Canvas now prefixes assistant and tool IDs with the current turn ID, keeping streaming updates and call/result grouping within that turn. A restart regression covers repeated SDK IDs. A final live sidebar follow-up preserved all 106 preceding messages and appended 17 new messages without creating another generation job.

The final follow-up confirmed the saved image outputs and Edit mode after a server restart. `npm run check` passed the builds, TypeScript, and **576 tests**; `git diff --check` passed.

The test server is available at `http://127.0.0.1:8765` while its owning process remains running. Its data directory is `plugins/canvas/.canvas-data-sidebar-e2e` in the development checkout. It is separate from the normal Canvas data directory.
