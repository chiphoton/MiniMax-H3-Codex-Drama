---
name: co-op-game-intro-generator
description: Design two-player co-op game menu or opening animations with the official MiniMax workflow, adapted into Codex confirmation-image prompts, identity and UI locks, event timing, and an H3 video handoff. Not for playable game development or multi-page interfaces.
---

# Co-op Game Intro Generator

Read [the vendored official workflow](references/official/SKILL.md) completely and load both official prompt templates it references.

## Adapt the official workflow to Codex

- Preserve the fixed menu framework, style fill, palette linkage, two-player identity cues, exact names and UI copy, confirmation-image gate, event timing, and negative constraints.
- Use an available image-generation skill only when the user requests an actual preview; otherwise return the filled confirmation-image prompt and wait for approval.
- Do not claim Hub canvas or media generation. Replace its approval step with an ordinary concise question.
- If called by `minimax-h3-drama:minimax-h3-adviser`, return the approved UI/style brief and final event timeline; do not load the adviser again.
- On explicit video execution intent, pass the approved final prompt to the adviser for H3 input-mode routing and ComfyUI execution when available.
- Use `../h3-prompt-writing/SKILL.md` if the delivery target requires the official structured H3 schema.

Keep official source material unchanged under `references/official/`.
