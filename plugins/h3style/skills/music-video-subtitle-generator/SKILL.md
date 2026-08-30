---
name: music-video-subtitle-generator
description: Plan music videos and emotional shorts where music, locked lyrics, beat timing, spatial typography, references, performance, and camera language work together, using the official MiniMax workflow adapted for Codex. Use for lyric-led or typography-led MVs, not ordinary subtitle transcription.
---

# Music Video Subtitle Generator

Read [the vendored official workflow](references/official/SKILL.md) completely before acting.

## Adapt the official workflow to Codex

- Preserve the duration and music-window lock, immutable user lyrics, creative contract, separate reference roles, typography packaging, beat grid, shot list, continuity strategy, prompt audit, and assembly plan.
- Replace Hub canvas nodes with inline locked artifacts. Do not claim parallel Hub generation or editing when unavailable.
- If the user wants only prompts, stop after the locked MV prompt package. Generate or assemble media only on explicit intent through available execution skills.
- If called by `minimax-h3-drama:minimax-h3-adviser`, return the music/style brief, reference-role map, timing grid, and relevant shot prompt; do not load the adviser again.
- For a complete multi-shot MV, pass the approved plan to `minimax-h3-drama:minimax-h3-drama-producer` when available. Use the adviser for one shot.
- Use `../h3-prompt-writing/SKILL.md` when official H3 prompt fields materially help the selected shot or reference mode.

Keep official source material unchanged under `references/official/`.
