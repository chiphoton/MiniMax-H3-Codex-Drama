# H3 Style

`h3style` packages all nine skills published under the official MiniMax-H3 repository's `skills/` directory:

- `h3style:h3-prompt-writing` preserves the portable official skill under `references/official/` and uses a thin entrypoint that removes its Codex-unsupported `compatibility` frontmatter key.
- The eight `h3style:<style-workflow>` skills likewise preserve the official workflow under `references/official/` and add a small Codex adapter that replaces MiniMax Hub-only canvas and `hub_*` operations with planning, prompt, and MiniMax-H3 Drama handoffs.

Refresh the pinned official snapshot with:

```bash
python3 plugins/h3style/scripts/sync_upstream.py
python3 plugins/h3style/scripts/sync_upstream.py --check
```

The sync replaces only vendored upstream trees, preserves maintained adapter entrypoints, and appends a conservative generic adapter if MiniMax publishes a new skill folder.

The plugin version follows the latest official commit date. The exact date is recorded as `YYYY-MM-DD` in `upstream-lock.json`; the manifest uses semver-safe `YYYY.M.D` because strict semantic versioning rejects zero-padded numeric components such as `08`.
