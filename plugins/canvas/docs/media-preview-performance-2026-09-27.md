# Media preview and task performance

Ported from upstream `uncensored` v0.4.1 and v0.5.0. This document describes the Codex adaptation; upstream's historical Safari timings are not presented as measurements of this build.

- Submitted runs and drawers share one 1,400 ms observation loop. Unchanged rows retain identity and do not republish the canvas. Job-only updates avoid rewriting drafts; elapsed clocks update in small components.
- A shared IntersectionObserver attaches video sources near the viewport and detaches them when hidden. Full previews remain independent. Stable media identity prevents repeated metadata requests when equivalent asset objects are recreated.
- Satisfiable ranges extending past EOF return a clamped `206`; invalid ranges remain `416`. Abandoned media responses abort file reads.
- Task history starts with ten grouped records, loads ten more on scroll or button activation, and retains pages per workflow filter for the tab's lifetime. A timestamp/ID cursor avoids offset drift. Modern cards use preview summaries and fetch full receipts only for inspection/download.
- Active observation is separate from historical paging. Asset selection uses server-side search/source filters and fifteen-item pages. Numeric fields retain incomplete edits until commit.

The imported tests exercise duplicate-observer prevention, unchanged snapshots, cancellation/retry/disposal, player stability, byte ranges, pagination, retained pages, search races and metadata effects. Run them with:

```sh
npm run check
node scripts/debug/media-preview.mjs
```

The fixture generates FFmpeg color bars and tones in a fresh temporary directory and exposes request counters at `/metrics`. Browser-side counters include RPCs, notifications and React commits. It prints the URL and removes its synthetic data on SIGINT/SIGTERM. From the plugin root, `VD_SMOKE_BASELINE=<Canvas repository commit>` can compare a committed `plugins/canvas/src/client` against the same fixture. It never starts generation or reads the user's data directory.

Codex in-app browser QA observed 40 thumbnail video elements with only 2 attached sources at the initial viewport. Task history loaded 10 then 20 records, and reopening retained 20. The browser reported no console errors. These observations establish lazy loading and paging behavior, not a production performance benchmark or a claim that a specific Safari hang is resolved.
