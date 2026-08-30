---
name: brand-promo-video-generator
description: Plan brand-safe promotional videos with the official MiniMax workflow, adapted from Hub canvas into Codex truth sheets, provenance manifests, story spines, beat plans, prompts, and production handoffs. Use for launches, products, apps, websites, shops, and campaigns; do not invent claims or brand assets.
---

# Brand Promo Video Generator

Read [the vendored official workflow](references/official/SKILL.md) completely before acting.

## Adapt the official workflow to Codex

- Preserve its asset intake, brand truth sheet, provenance manifest, story-spine choice, exact beat plan, motion direction, hard pre-generation approval, and delivery checks.
- Replace Hub search or canvas operations with available read-only research and inline artifacts. Do not use unverified identity-bearing assets, invent product facts, or approximate logos.
- Never claim to call unavailable `hub_*` tools. When media tools are unavailable or execution is not explicit, return the pre-production package and H3-ready prompts.
- If called by `minimax-h3-drama:minimax-h3-adviser`, return a brand/style brief and asset-role map; do not load the adviser again.
- For an explicitly requested complete promo, pass the approved plan to `minimax-h3-drama:minimax-h3-drama-producer` when available. For one clip, return to the adviser.
- Apply `../h3-prompt-writing/SKILL.md` only when official structured H3 fields are the required target; do not force that schema onto an incompatible ComfyUI prompt field.

Keep official source material unchanged under `references/official/`.
