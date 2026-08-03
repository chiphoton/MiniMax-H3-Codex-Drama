# Frame-to-video template and examples

## Canonical template

```text
Use Image 1 as the exact opening frame. [Use Image 2 as the exact closing frame.]

PRESERVE
[Identity, product design, layout, typography, environment geometry, lighting direction, palette, or other invariants visible in the supplied frame(s).]

MOTION PATH
[0–Xs]: [First motivated movement beginning from Image 1.]
[X–Ys]: [Intermediate action and camera path.]
[Y–end]: [How motion settles naturally into Image 2 or the intended final composition.]

CAMERA AND LOOK
[Camera behavior, depth/focus changes, exposure, texture, and transition mechanics.]

AUDIO
[Ambience, effects, dialogue, and timed accents.]

CONSTRAINTS
[No abrupt morphing/cuts, no layout or identity drift, no duplicate elements, no invented text, and any exact ending hold.]
```

For one-frame animation, remove references to Image 2 and define the ending composition. For a first/last pair, describe the bridge rather than two separate scenes.

## Example 1: animate a static exhibition poster

Inputs: Image 1 is the exact opening poster.

Suggested settings: 8 seconds, aspect ratio inherited from Image 1, 2K.

```text
Use Image 1 as the exact opening frame and preserve its cream gallery border, central cobalt sculpture, black grid, red date block, and every printed word exactly.

[0–2s]: Hold the full poster steady. A thin black grid line draws outward from the center while the printed layout remains locked.
[2–6s]: The cobalt sculpture rotates subtly within its own panel as two red blocks slide along existing grid tracks. Bring the title into focus from a slight optical blur without changing its spelling, size, or position.
[6–8s]: All movement decelerates and returns to the original balanced layout, except the sculpture remains turned slightly toward camera. Hold the final composition for one second.

Use crisp graphic motion design with restrained paper texture and very slight depth between layers. The camera remains locked; only elements inside the poster animate.

Audio: soft paper friction, one quiet mechanical tick as each red block stops, and a short clean tone when the title becomes sharp.

No camera movement, border drift, new typography, misspellings, elastic warping, 3D room, extra logos, or scene cut.
```

## Example 2: controlled transition between two keyframes

Inputs: Image 1 is an empty dining table at dusk; Image 2 is the same composition with a lit celebration cake and gathered friends.

Suggested settings: 10 seconds, aspect ratio inherited from Image 1, 2K.

```text
Begin exactly from Image 1 and conclude exactly at Image 2. Preserve the room geometry, fixed camera position, table shape, window placement, and dusk lighting direction throughout.

[0–3s]: The empty room remains still as the camera begins an almost imperceptible push forward. Small warm reflections appear on the table as lights switch on outside frame.
[3–7s]: Friends enter naturally from both sides, place the cake at the center, and settle into the exact positions visible in Image 2. Their movement stays continuous and never crosses through furniture.
[7–10s]: The cake candles ignite one after another. Everyone finishes moving, their faces and hands settle into Image 2, and the camera arrives precisely at its closing composition for a one-second hold.

Let the room tone grow from quiet evening air to soft footsteps, chair movement, clothing rustle, and restrained laughter. Synchronize a gentle musical lift with the candle ignition.

No cut, dissolve, abrupt morph, duplicated person, sliding furniture, camera-direction change, or geometry drift. Do not introduce decorations or objects absent from Image 2.
```

