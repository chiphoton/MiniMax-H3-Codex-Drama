# Canvas 0.4.0: upstream v0.4.0 sync

Source: [chiphoton/DeepSeek-Harness-Video-Director](https://github.com/chiphoton/DeepSeek-Harness-Video-Director) (`dsh-video-director`). This sync uses **`uncensored` commit `4964977426229c2760cf519197b40a0ec6181825`**, titled `v0.4.0: updated job queue mechanism, media editor, and ui panel`.

Canvas's plugin and npm versions follow the upstream release version, starting with this aligned `0.4.0` release. Upstream's npm manifest still says `0.1.2`, so the release commit identifies the version being synced. `upstream-lock.json` pins the repository, branch, commit, and file hashes for each sync.

The previous source was v0.3.0 commit `0353b43c879b3f6bd13e2100320b4680bebca39e`. The intervening v0.3.1 UI changes are included.

| Upstream change | Codex integration |
|---|---|
| Persistent global workflow queue | `WorkflowScheduler` and `RunQueue` run in the standalone Canvas server. Graph stages, triggers, repetitions, and case batches continue after tabs close. Queued snapshots recover on server startup; interrupted active runs are not resubmitted. Shutdown closes the scheduler before providers, and storage changes attach a new scheduler to the copied store. |
| Shared execution semantics | `scripts/build-client.mjs` emits `dist/workflow-execution.js` for Node alongside the browser bundle. Doctor checks both builds; no Harness bundle or runtime is required. |
| Batch Input and Batch Output | Text/file/folder cases, regex filtering, one-based ranges, fixed per-case seeds, durable receipts, retry/resume, and TAR export. Canvas's browser policy permits the blob worker used to bound regex evaluation. |
| Tasks panel | Compact global run cards, workflow filtering, elapsed timing, artifact/workflow downloads, submitted graph opening, history removal, and a properties/cancellation dialog. Global `jobs/list` and `vd-runs/list` drive the client; the existing `tasks/list` RPC remains available for integrations. |
| Folders and selection | Nested virtual folders, drag/keyboard ordering, Multi-Select move/delete, revision conflicts, and draft-aware project operations retain Canvas conversation bindings. |
| Asset chooser and storage layout | Empty media inputs, file drops, reusable cross-workflow assets, independent duplicate references, and input/output folders with recoverable legacy migration. Native Codex image imports are explicitly marked as outputs; original Codex files stay in place. |
| Audio/video editing | Waveform audio playback, trim/crop selection, frame export, save/copy/export actions, and local FFmpeg workflow nodes use loopback RPC and media metadata routes. Errors and doctor guidance name the Canvas host. |
| H3 reference workflow | Expanded typed references and Turbo workflow controls come from the exact `uncensored` node manifest. Existing workflow IDs and archive markers remain compatible. |

Canvas retains `.codex-plugin/plugin.json`, its standalone HTTP host and origin checks, local sessions, Codex Plan text/image defaults, account model discovery, adviser chat, `CANVAS_*` settings, `.canvas-storage.json`, bilingual UI, and setup/doctor/CLI helpers. Harness's Cordis entry points, injected dependencies, native chat transport, settings schema, launcher, and close controls are excluded. Package dependencies remain locked to Canvas's existing versions.

The previous Canvas browser scheduler is superseded by the server queue. Cross-project execution remains supported, with complete workflows now serialized globally. The Canvas fix for fresh outputs passing through cleared Preview chains is retained in the shared execution helpers and applied by both the server and browser. Historical output restoration remains suppressed after Clear Previews; frozen references remain unchanged. Batch Output waits for the submission receipt before loading case records, preventing a transient run-not-found error. Its bilingual help text reflects server-owned execution.

`upstream-lock.json` records SHA-256 hashes of upstream originals for each shared/adapted file at the exact commit. These are provenance hashes, not checksums of the Codex adaptations. Codex-only hosting files and packaging are outside that list. No user projects, credentials, generated media, caches, or dependency directories were copied from the source checkout. The original MIT license remains in place.

## Upgrade

Finish or cancel runs in the old Canvas 0.2.0 client before stopping its server. Run `node scripts/setup.mjs`, start the updated server with the same data directory, and reload tabs. Back up the data directory before upgrading. First startup verifies and migrates legacy flat asset files into `assets/inputs/` and `assets/outputs/`, recording a recovery journal while retaining asset IDs and URLs. New accepted runs survive tab reloads and closures; the server and computer must stay running.

## Validation

`npm run check` builds both bundles, type-checks the client, and passes 471 tests. Coverage includes global queue order, browser disconnection, cancellation, shutdown/restart recovery, batch case receipts/retry/export, project folders, asset migration and sharing, media editing, and cleared/frozen Preview propagation. Codex host integration checks use temporary storage and simulated providers over real loopback HTTP, including scheduling after a storage move and placing generated Codex images in the output folder. No paid provider generation is needed for these checks.

Browser QA used a temporary data directory and simulated Codex providers. It verified regex workers, a two-case batch before and after client reload, completed case previews, Tasks, project folders, and the asset chooser. Real FFmpeg editing trimmed a generated two-second clip to 1.25 seconds and cropped it from 480 × 270 to 270 × 270; the rendered result was inspected in the browser.
