---
name: paper-collage-explainer-generator
description: Plan tactile halftone paper-collage explainers with the official MiniMax workflow, adapted from Hub canvas into Codex production plans, visual metaphors, still prompts, stop-motion shot prompts, audio policy, QC, and assembly handoffs. Not for presenter ads, editable layers, or generic prompt-only shots.
---

# Paper Collage Explainer Generator

Read [the vendored official workflow](references/official/SKILL.md) completely before acting.

## Adapt the official workflow to Codex

- Preserve the learning/message extraction, production-plan gate, visual metaphor, polished layered 16:9 default, still-frame specifications, still approval gate, stop-motion plan, tactile SFX default, optional audio policy, QC, and assembly order.
- Do not silently add BGM, voiceover, or subtitles. Do not claim Hub image, video, audio, canvas, or assembly actions.
- Return actual media only through an available skill and explicit execution intent; otherwise return production-ready still and video prompts.
- If called by `minimax-h3-drama:minimax-h3-adviser`, return the collage style brief, approved still roles, shot plan, and audio constraints; do not load the adviser again.
- For a multi-shot executed explainer, pass the approved plan to `minimax-h3-drama:minimax-h3-drama-producer` when available. Use the adviser for a single B-roll clip.
- Use `../h3-prompt-writing/SKILL.md` when the target requires official structured H3 syntax.

Keep official source material unchanged under `references/official/`.
