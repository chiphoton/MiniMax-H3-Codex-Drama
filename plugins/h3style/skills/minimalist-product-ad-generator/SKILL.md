---
name: minimalist-product-ad-generator
description: Plan premium minimalist product-ad shorts with the official MiniMax workflow, adapted from Hub canvas into Codex product facts, narrative spine, copy, independent visual anchors, beat storyboards, H3 prompts, and production handoffs. Not for talking-head ads, generic editing, or complex demos.
---

# Minimalist Product Ad Generator

Read [the vendored official workflow](references/official/SKILL.md) completely before acting.

## Adapt the official workflow to Codex

- Preserve the start gate, main-variant lock, aspect ratio and duration, product facts, minimalist narrative spine, motion language, confirmed copy, three independent anchor concept, precise beat table, audio policy, and verification rules.
- Do not approximate packaging, logos, copy, geometry, or product claims. If actual anchor generation is unavailable or not requested, provide separate anchor prompts and keep approval gates explicit.
- Never claim Hub canvas, image, music, or video operations. Deliver prompts and specifications until the user explicitly requests execution.
- If called by `minimax-h3-drama:minimax-h3-adviser`, return the product/style brief, anchor roles, and beat plan; do not load the adviser again.
- For a complete executed ad, pass the approved plan to `minimax-h3-drama:minimax-h3-drama-producer` when available; use the adviser for a single clip.
- Use `../h3-prompt-writing/SKILL.md` only when official H3 structured fields are required by the target runtime.

Keep official source material unchanged under `references/official/`.
