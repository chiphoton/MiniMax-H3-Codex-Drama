# Canvas 0.6.0: upstream v0.6.0 sync

Source: [chiphoton/DeepSeek-Harness-Video-Director](https://github.com/chiphoton/DeepSeek-Harness-Video-Director), `uncensored` branch at **`e17c2308666e595b09f094bd63615acaf3bdd00a`** (`v0.6.0: added text-to-canvas agent operations`). The previous source pin was v0.5.0 `dd33d909d21d4c525d2682af0254fb928ad4441c`.

The intervening DSH migration commits were reviewed. Linked workflow/session title synchronization from `caeb69a8dc9de085bb92313e80300bb5280c09d4` is adapted to Canvas's local session service. DSH rc.2 registration, workspaces, model directories, credentials, packaging, and native transport remain outside this standalone Codex plugin.

The npm package, lockfile, Codex plugin manifest, HTTP health response, MCP server identity, and Codex model-discovery client identity report **0.6.0**. The upstream package version `0.2.1-rc.2` describes Harness compatibility, not this release. `upstream-lock.json` records upstream SHA-256 hashes; files with Codex adaptations intentionally differ.

## Feature mapping

| Upstream change | Codex integration |
|---|---|
| Managed skills | Immutable versions, supporting files, import/export, duplicate, archive/restore, sharing, pinned selection, `$skill` completion, and optional automatic invocation of bundled skills. |
| Canvas construction | Typed `plan-edit`, `ports`, asset placement, switchable H3 video presets, a sketch-to-H3 recipe, measured/fallback layout, and stage titles. |
| Change history | Browser and agent changes have durable receipts, retry keys, Inspect, and revision-checked Undo. Existing local undo and draft-conflict recovery remain available. |
| Workspace operations | Discoverable operation schemas, filtered provider metadata, acknowledged select/frame/zoom/inspect/preview commands, and bounded results with scoped cursors. |
| Quality iterations | Criteria, version/model pins, job/time/iteration limits, evidence-backed perceptual reports, affected-branch reruns, best-run retention, deadline cancellation, and restart reconciliation. |
| Media review | Host FFmpeg contact sheets with sample times; image and video preview actions attach review images without sending a message. |
| Chat presentation | Markdown/GFM, literal skill mentions, model labels, local image previews, expandable tool activity, stop control, and refreshed composer/settings layout. |
| Linked titles | Workflow rename, save, discard, and undo/redo synchronize their local chat title. Rename failures preserve successful graph writes and can be retried. |

## Codex hosting and model choice

Chat uses the existing local Codex SDK and CLI sign-in. Its model picker lists **Codex Plan** models only. Fresh connections automatically discover the signed-in catalog; an explicit saved selection remains pinned. Reasoning effort follows the selected model's catalog default. Fast (priority) remains an optional Settings-only control, off by default. No DSH session/model service, API key, hard-coded fallback model, or alternate model backend is introduced for chat.

The chatbox's **Model settings** opens Canvas Settings → Connections. Three additional npm dependencies support the port: pinned `react-markdown` 10.1.0, `remark-gfm` 4.0.1, and `yaml` 2.9.1. The follow-up Codex integration update upgrades `@openai/codex-sdk` and its bundled CLI from 0.152.1 to **0.167.0**. React, XYFlow, and other previously locked dependency versions are retained. Canvas keeps its existing environment-based provider defaults; the API connection validation and setup hints are ported.

`CodexCanvasMcp` exposes `vd_canvas`, `vd_library`, `vd_workspace`, and `vd_quality` over the existing authenticated loopback connection. Each turn has a temporary capability bound to one project and session. The adapters enforce `protocol: "vd/1"`, derive the owning session from that capability, reject cross-project requests, and revoke access on completion/cancellation. Native DSH attachment handling is replaced with MCP image content and conversation-scoped local transcript images. Image inspection still requires a vision-capable Codex model.

Workflow content access is off initially, as upstream specifies. Metadata queries and reversible graph edits work; reading node text/media and running providers requires enabling **Workflow access** in chat settings. Explicitly sent attachments are shared separately. The Codex turn retains its read-only sandbox, no approval escalation, and disabled network access; instructions direct it to the scoped tools rather than filesystem workarounds.

The standalone server recovers quality journals with the persistent workflow scheduler, closes their observers on shutdown, and blocks storage relocation while a quality plan or Codex turn remains active. Existing same-origin checks, local credentials, data-directory relocation, Codex image imports, cleared-preview behavior, and archive compatibility are retained. The specialized sketch-to-H3 recipe still explicitly uses ComfyUI and Ollama; ordinary text/image nodes and chat retain Codex Plan defaults.

## Upgrade and verification

Finish or cancel active work, rebuild using `node scripts/setup.mjs`, restart Canvas with the existing data directory, and reload tabs. No eager project rewrite is needed: skill bindings, access settings, operation receipts, and quality journals are created as used. Keep managed data outside the plugin cache.

**Verified November 8, 2026:** `npm run check` passed the browser/shared execution builds, TypeScript, and all **574 tests**. `git diff --check` passed. Synthetic regressions cover tool scope, content access, skill pins, bounded queries, large graphs, atomic edits/undo, quality budgets and recovery, storage moves, contact sheets, local image transcripts, model defaults, and title synchronization. These checks do not call a paid model or operate on user projects.

Browser QA in the disposable fixture verified `$canvas-builder` selection, a chat-created Text Input, Inspect/Undo, the managed skills dialog, the Codex-only model picker, and Model settings opening Connections. No browser warnings or errors were observed.

For manual UI checks, `node scripts/debug/sidebar-chat.mjs` starts the standalone host with simulated Codex/providers and temporary synthetic data; Ctrl-C removes it. A live model generation is separate from these tests.

The Codex SDK update also passed all 574 tests. A separate signed-in live check used GPT-6.1 Sol and the native image tool once, then imported the generated PNG through `CodexPlanImageRuntime`. See [Codex runtime verification](codex-runtime.md) for the CLI versions, image-model evidence, and limits of this check.

The subsequent [live sidebar generation/editing test](sidebar-image-e2e.md) exposed three additional integration issues: noninteractive MCP approvals, undiscoverable image edit mode, and CLI item IDs reused across resumed turns. All three are corrected with regression coverage. The final build, typecheck, and **576 tests** passed; the live sidebar created and completed both image stages and retained them across restart.

The upstream checkout and the pre-existing untracked `docs/codex-sidebar-evaluation.md` are unchanged. Original MIT licensing is retained in `LICENSE` and `NOTICE.md`.
