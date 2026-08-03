# Video-editing template and examples

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

## Example 1: sign replacement and night relighting

Inputs: Video 1 is the source street clip; Image 1 supplies the replacement storefront sign design.

Suggested settings: preserve source duration and aspect ratio, 2K, adaptive if needed.

```text
Use Video 1 as the source video. Preserve its duration, handheld camera path, pedestrian movement, vehicle timing, storefront geometry, and all content not explicitly changed below.

Use Image 1 only for the replacement sign's exact lettering, dark-blue panel, white border, and material finish. Do not copy its wall, lighting, or surrounding architecture.

Edits:
1. Replace only the illuminated rectangular sign above the corner storefront with the sign from Image 1. Track it to the existing sign plane through the whole shot and preserve its perspective, scale, partial occlusion by the tree, and reflections in the shop window.
2. Change the scene from overcast late afternoon to early night. Keep all geometry and motion unchanged. Introduce cool ambient sky light, warm storefront practicals, realistic headlight spill, and corresponding reflections on the damp pavement.

Relight people, vehicles, glass, and building surfaces consistently without changing their identity, clothing, position, or timing. Keep the new sign legible but naturally exposed for the scene.

Everything else in Video 1 remains unchanged, including the camera shake, walking pace, traffic sequence, shop contents, and source audio timing. No new shops, text, signs, vehicles, rain, lens flare, compositing seams, or camera stabilization.
```

## Example 2: dialogue and performance replacement

Inputs: Video 1 is the source conversation; Audio 1 contains the replacement line and target voice.

Suggested settings: preserve source duration and aspect ratio, 2K, adaptive if needed.

```text
Use Video 1 as the source video. Preserve its shot order, camera movement, room, wardrobe, character identities, eyelines, background action, and all dialogue outside the specified line.

Use Audio 1 only for the woman's replacement voice, wording, cadence, and emotional timing.

At the woman's second speaking turn, replace her original line with Audio 1: “I came back because the truth matters more than being right.” Preserve the exact words and timing from Audio 1.

Adjust only the woman's mouth movement, breath, jaw, eye expression, and small hand gesture during that speaking turn so the performance fits the new line. Keep the reaction shot from the man in its original timing, but allow his existing expression to remain visible without adding new movement.

Match room acoustics, microphone distance, volume, and background ambience so the new line integrates naturally. Preserve all other source audio, including chair movement and distant traffic.

Everything not explicitly listed remains unchanged. No identity drift, altered wardrobe, changed camera timing, extra dialogue, subtitle, music, facial redesign, exaggerated gesture, or lip-sync lag.
```

