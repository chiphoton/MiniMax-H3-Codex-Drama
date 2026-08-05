# Visual development contract

## Reference authority

Treat user-supplied identity, product, wardrobe, environment, and brand references as source evidence. A generated master normalizes those references for production; it does not supersede them. Record which source controls each visible property and what it must not influence.

When a supplied sheet is already complete and internally consistent, reuse it. Do not regenerate it merely to impose this layout.

## Character and identity sheet

Create one clean master per recurring person, mascot, animal, or stylized identity. Use a neutral studio background and consistent light. Include:

- full-body front, three-quarter, profile, and back views at matched scale;
- head-and-shoulder front and three-quarter close-ups;
- neutral expression plus only the story-critical expressions;
- stable face shape, age range, skin tone, hair silhouette, body proportions, and identifying features;
- canonical wardrobe layers, shoes, accessories, and carried props;
- color and material swatches when they prevent drift;
- a clear list of invariants and allowed shot-specific changes in the entity ledger.

Keep poses diagnostic rather than cinematic. Avoid duplicate people, cropped limbs, scene action, typography baked into the image, or conflicting wardrobe variants. Add exact labels later in a deterministic overlay if labels are useful.

## Product sheet

For recurring products, vehicles, devices, or packages, include front, rear, side, three-quarter, top, and scale/detail views as applicable. Lock silhouette, proportions, controls, openings, seams, materials, finish, color, logo placement, and any state changes the story requires. Preserve approved claims and exact brand text outside generative imagery whenever possible.

## Scene master

Create one master per recurring environment. Establish:

- a readable wide view and the principal camera axis;
- doorway, window, furniture, workstation, and hero-prop positions;
- foreground, subject, and background depth zones;
- time of day, key-light direction, practical lights, palette, and surface materials;
- legal character positions, screen direction, and continuity-sensitive object states.

Use a simple overhead layout or annotated deterministic companion image when spatial continuity is complex.

## Storyboard and keyframes

Generate the storyboard only after entity and scene masters exist. Cover every planned shot in timeline order and show shot ID, framing, action, camera direction, transition intent, and expected end state in accompanying structured data.

Generate keyframes at the final delivery aspect ratio and derive them from the approved masters. A frame-to-video opening keyframe must be a usable literal first frame, not a collage or labeled sheet. Generate a closing keyframe only when the continuous bridge must land on an exact composition.

## Visual lock review

Before batch video generation, compare every recurring entity and environment across the storyboard and keyframes. Reject the lock when identity, product geometry, wardrobe, scene layout, prop state, light direction, or screen direction already conflicts; H3 generation should not be expected to repair inconsistent sources.
