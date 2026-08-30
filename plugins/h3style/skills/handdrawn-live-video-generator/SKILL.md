---
name: handdrawn-live-video-generator
description: Write surreal single-scene H3 video concepts that blend rough glowing hand-drawn animation with live-action spaces, using the official MiniMax workflow adapted for Codex. Use for continuous physical contact, morphing, escape, and delayed handheld chase motion; not polished CG, horror, or multi-scene edits.
---

# Hand-drawn Live Video Generator

Read [the vendored official workflow](references/official/SKILL.md) completely before writing the prompt.

## Adapt the official workflow to Codex

- Preserve the user's dominant language, 15-second 16:9 target, contact realism, continuous morphing, escape route, delayed camera chase, rough glowing stroke texture, and non-horror boundary.
- Follow the official output shape for prompt-only requests.
- Do not claim to generate media or call MiniMax Hub. Wait for explicit execution intent after the prompt is approved.
- If called by `minimax-h3-drama:minimax-h3-adviser`, return the official concept constraints and prompt brief; do not load the adviser again.
- On explicit execution intent, return control to the adviser so it can choose text, frame, reference, or edit mode and optionally hand off to ComfyUI.
- Use `../h3-prompt-writing/SKILL.md` only when the user requests official fielded prompt syntax; otherwise preserve the official same-language prose prompt.

Keep official source material unchanged under `references/official/`.
