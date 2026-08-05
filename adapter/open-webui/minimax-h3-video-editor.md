---
name: minimax-h3-video-editor
description: Create, enhance, or diagnose precise MiniMax H3 prompts for editing an existing video while preserving everything outside requested changes. Use for subject or object replacement, removal, wardrobe changes, background replacement, relighting, localized VFX, text or signage changes, dialogue or voice replacement, performance adjustment, and multi-element edits that need explicit change-and-preserve pairs and copy-ready prompts.
---

# MiniMax H3 Video Editor

Describe localized changes to a source video while locking every unaffected property. Stay prompt-only and never submit a generation job.

## Confirm the workflow

Use this workflow when at least one existing video is the source to modify. Route execution through reference-conditioned video generation; label the source as `Video 1` unless the user's existing ordering differs. Additional images, videos, or audio may supply replacement identity, design, environment, motion, or voice.

Recommend 5–15 seconds, `768P` for iteration or `2K` for a final pass when supported, and a fixed or `adaptive` aspect ratio. Preserve the source duration or aspect when that is important to the edit, and let the executor validate the installed workflow.

## Write change-and-preserve pairs

Create a short edit ledger before the prompt. For each operation, pair:

- **Change**: exact target, location or time, operation, and replacement source.
- **Preserve**: surrounding subjects, action, timing, framing, lighting, shadows, reflections, geometry, audio, text, or effects that must remain stable.

Examples of precise operations include replace, remove, add, relight, recolor, rewrite, retime, and overlay. Avoid broad restyling language unless broad restyling is the requested edit.

## Build the prompt

1. Identify the source video and all replacement references by modality and order.
2. State the requested edits in temporal or spatial order.
3. Bind each replacement to a source asset where applicable.
4. Explain integration: matching perspective, motion, occlusion, lighting, shadows, reflections, lip sync, or performance.
5. State the global invariant: everything not explicitly listed remains unchanged.
6. Add targeted failure constraints such as no source-camera drift, no identity change, no extra objects, no altered timing, or no compositing seams.

For dialogue replacement, provide the exact new line and identify the voice reference. Ask for subtle mouth, breath, expression, and gesture adaptation without changing unrelated performance. For relighting or background replacement, require subject light, shadow, reflection, and atmospheric integration.

## Enhance or diagnose

When enhancing, preserve the user's edit list and source ordering. Turn ambiguous nouns such as “that sign” into a spatial or temporal identifier when evidence permits.

When diagnosing, test for:

- edits with no preservation partner;
- unclear target instances when the object appears multiple times;
- a replacement asset with no role assignment;
- lighting, shadow, reflection, or occlusion mismatches;
- dialogue changes without lip-sync and performance adaptation;
- too many unrelated edits in one pass;
- global style directions that regenerate the entire shot.

Recommend splitting into passes only when edits compete or accurate targeting becomes implausible.

## Canonical template

```text
Use Video 1 as the source video. Preserve its duration, camera movement, framing, timing, subject motion, and all content not explicitly changed below.

REFERENCE ASSIGNMENTS
Use Image 1 only for [replacement identity/object/style/environment]. Preserve [defining details].
Use Audio 1 only for [replacement dialogue/voice/music].

EDITS
1. At [time/spatial location], [replace/remove/add/relight/rewrite] [exact target] with [replacement]. Preserve [local invariants].
2. At [time/spatial location], [operation]. Preserve [local invariants].

INTEGRATION
[Match motion, timing, perspective, scale, occlusion, focus, lighting, shadows, reflections, atmosphere, lip sync, and performance as relevant.]

GLOBAL PRESERVATION
Everything not explicitly listed remains unchanged. [Name especially fragile invariants.]

AVOID
[Targeted edit failures: seams, drift, extra objects, altered identity, retiming, source-camera change, unwanted text, etc.]
```

## Example: sign replacement and night relighting

Inputs: Video 1 is the source street clip; Image 1 supplies the replacement storefront sign design. Suggested settings: preserve source duration and aspect ratio, 2K, adaptive if needed.

```text
Use Video 1 as the source video. Preserve its duration, handheld camera path, pedestrian movement, vehicle timing, storefront geometry, and all content not explicitly changed below.

Use Image 1 only for the replacement sign's exact lettering, dark-blue panel, white border, and material finish. Do not copy its wall, lighting, or surrounding architecture.

Edits:
1. Replace only the illuminated rectangular sign above the corner storefront with the sign from Image 1. Track it to the existing sign plane through the whole shot and preserve its perspective, scale, partial occlusion by the tree, and reflections in the shop window.
2. Change the scene from overcast late afternoon to early night. Keep all geometry and motion unchanged. Introduce cool ambient sky light, warm storefront practicals, realistic headlight spill, and corresponding reflections on the damp pavement.

Relight people, vehicles, glass, and building surfaces consistently without changing their identity, clothing, position, or timing. Keep the new sign legible but naturally exposed for the scene.

Everything else in Video 1 remains unchanged, including the camera shake, walking pace, traffic sequence, shop contents, and source audio timing. No new shops, text, signs, vehicles, rain, lens flare, compositing seams, or camera stabilization.
```

## Example: dialogue and performance replacement

Inputs: Video 1 is the source conversation; Audio 1 contains the replacement line and target voice. Suggested settings: preserve source duration and aspect ratio, 2K, adaptive if needed.

```text
Use Video 1 as the source video. Preserve its shot order, camera movement, room, wardrobe, character identities, eyelines, background action, and all dialogue outside the specified line.

Use Audio 1 only for the woman's replacement voice, wording, cadence, and emotional timing.

At the woman's second speaking turn, replace her original line with Audio 1: “I came back because the truth matters more than being right.” Preserve the exact words and timing from Audio 1.

Adjust only the woman's mouth movement, breath, jaw, eye expression, and small hand gesture during that speaking turn so the performance fits the new line. Keep the reaction shot from the man in its original timing, but allow his existing expression to remain visible without adding new movement.

Match room acoustics, microphone distance, volume, and background ambience so the new line integrates naturally. Preserve all other source audio, including chair movement and distant traffic.

Everything not explicitly listed remains unchanged. No identity drift, altered wardrobe, changed camera timing, extra dialogue, subtitle, music, facial redesign, exaggerated gesture, or lip-sync lag.
```

## Return

Provide:

- an edit ledger and asset mapping;
- suggested duration, aspect ratio, resolution, and workflow route;
- material assumptions, if any;
- one copy-ready prompt;
- 2–4 preservation checks.

Do not return an API payload or submit a job.
