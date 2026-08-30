---
name: 3d-animation-short-generator
description: Plan stylized 3D animated shorts with the official MiniMax workflow, adapted from Hub canvas into Codex briefs, character and scene locks, shot tables, storyboards, H3 prompts, and production handoffs. Use for complete animated narratives, not a single generic shot or photorealistic live action.
---

# 3D Animation Short Generator

Read [the vendored official workflow](references/official/SKILL.md) completely. Read its model-selection, shot-table, storyboard, fallback, and QC references when the current phase calls for them.

## Adapt the official workflow to Codex

- Preserve story-first planning, format and duration decisions, character and environment locks, the six-column shot table, storyboard logic, model choice, audio plan, and final QC.
- Replace Hub canvas nodes with concise inline artifacts or user-requested local files. Replace choice cards with ordinary concise questions or options.
- Do not claim to call `hub_generate_image`, `hub_generate_video`, or a canvas tool. If those operations are unavailable, deliver the corresponding prompt, specification, or approval artifact.
- If called by `minimax-h3-drama:minimax-h3-adviser`, return a style brief and shot plan to the adviser; do not load the adviser again.
- If the user wants a complete multi-shot film and explicitly authorizes execution, hand the approved official plan to `minimax-h3-drama:minimax-h3-drama-producer` when available. A single shot can return to the adviser.
- Use `../h3-prompt-writing/SKILL.md` only when the target needs the official structured H3 schema. Keep the local specialist's prompt form for a confirmed ComfyUI graph that expects it.

Keep official source material unchanged under `references/official/`. The adapter changes runtime mechanics, not the creative workflow.
