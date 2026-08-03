---
name: minimax-h3-reference-to-video
description: Create, enhance, or diagnose MiniMax H3 multimodal reference-to-video prompts using images, videos, and audio for identity, product design, style, location, storyboard, motion, camera, editing rhythm, performance, music, or voice. Use when multiple assets need explicit jobs, unwanted cross-reference influence must be blocked, or users need an asset ledger, timed shot plan, preservation constraints, settings, template, or copy-ready H3 prompt.
---

# MiniMax H3 Reference to Video

Turn multimodal assets into one coherent MiniMax H3 direction by giving every asset an explicit, bounded job. Stay prompt-only and never submit a generation job.

## Confirm the workflow

Use this workflow when media acts as a reference rather than an exact first or last frame. If the only visual input is the literal opening frame, recommend the MiniMax H3 frame-to-video workflow. If an existing video is being changed locally while the rest stays stable, recommend the MiniMax H3 video-editor workflow.

For fal.ai, recommend endpoint `minimax/h3/reference-to-video`, duration 5–15 seconds, resolution `768P` or `2K`, and a fixed or `adaptive` aspect ratio. The current fal schema allows up to 9 images, 3 videos, and 3 audio clips with no more than 12 files total. Reference video and audio clips are 2–15 seconds each with no more than 15 seconds combined per modality; audio cannot be the only reference type. Treat provider capabilities as changeable; verify them when the user requests current API accuracy.

## Create an asset ledger first

For every supplied asset, record:

- exact label: `Image 1`, `Video 1`, `Audio 1`, and so on;
- positive job: identity, wardrobe, product geometry, environment, style, storyboard, motion, camera, edit rhythm, voice, music, or sound design;
- preservation details that define success;
- excluded influence: what must not be copied from that asset.

Never say only “use these references.” Use bounded language such as “Use Video 1 only for the slow clockwise camera orbit; do not copy its subject, location, palette, or wardrobe.”

## Build the prompt

1. State format, duration, aspect ratio, and shot structure.
2. Assign every reference before describing the new scene.
3. Describe the subject, action, environment, and timecoded beats.
4. Direct camera, look, and audio.
5. Restate identity, product, layout, or source-video invariants at the end.
6. Resolve conflicts explicitly; do not let two references own the same property unless their relationship is explained.

When identity matters, name the defining facial, hair, wardrobe, or product details to preserve. When audio matters, align mouth movement, breathing, gesture, edits, and camera emphasis to specific audio moments.

## Enhance or diagnose

When enhancing, retain the user's asset ordering. Never silently renumber references.

When diagnosing, test for:

- assets with no declared job;
- two assets competing for identity, style, or camera control;
- missing exclusions that allow unrelated elements to leak across;
- motion transfer with no spatial adaptation instructions;
- voice reference without performance or synchronization direction;
- more beats or files than the workflow can use coherently;
- preservation details that are too generic to lock identity or product design.

## Canonical template

```text
Create a [duration]-second [aspect-ratio] [format/genre] video as [one continuous shot / N concise shots].

REFERENCE ASSIGNMENTS
Use Image 1 only for [identity/product/style/location/storyboard role]. Preserve [defining details]. Do not copy [unrelated influence].
Use Video 1 only for [motion/camera/edit rhythm/performance role]. Adapt it to [new subject/space]. Do not copy [unrelated influence].
Use Audio 1 for [voice/music/sound role]. Synchronize [mouth/breath/gesture/cuts/camera] to [specific moments].

SUBJECT, SETTING, AND ACTION
[New scene and spatial relationships.]
[0–Xs]: [Opening beat.]
[X–Ys]: [Main beat.]
[Y–end]: [Ending beat and final composition.]

CAMERA AND VISUAL TREATMENT
[Framing, principal movement, lighting, palette, texture, atmosphere.]

AUDIO
[Dialogue, ambience, foley, effects, and music not already assigned.]

CONSTRAINTS
[Identity/design/source-motion invariants, exact counts, exclusions, continuity, likely failure modes.]
```

Remove unused reference lines. Keep the user's original modality ordering.

## Example: identity, camera, and vocal performance

Inputs: Image 1 is the singer's identity and wardrobe; Video 1 is a camera reference; Audio 1 is the vocal performance. Suggested settings: 12 seconds, 16:9, 2K.

```text
Create a 12-second cinematic music-performance video in 16:9 as one continuous shot.

Use Image 1 only for the singer's facial identity, short curled hair, silver jacket, black shirt, and understated makeup. Preserve these details throughout; do not copy its background or lighting.
Use Video 1 only for the slow lateral track that becomes a gentle push-in near the end. Adapt the movement to the new stage; do not copy its performer, location, wardrobe, or color palette.
Use Audio 1 as the exact vocal performance. Synchronize lip movement, breath, jaw tension, eye expression, and the final camera push to the strongest sustained note.

Place the singer alone on a narrow theater stage surrounded by darkness, with one cool overhead spotlight and faint haze. Begin in a medium profile view.

[0–5s]: Track slowly from the singer's left toward a frontal angle while the performance remains restrained.
[5–9s]: The singer turns toward camera and raises one hand slightly as the vocal intensity grows.
[9–12s]: Begin the referenced push-in on the sustained note and settle in a close-up as the phrase ends.

Keep the lighting minimal, cool, and cinematic with soft highlight halation and a dark uncluttered background. Add only quiet room ambience beneath Audio 1.

Preserve facial identity, wardrobe, and microphone-free staging. Exactly one performer. No cuts, audience, captions, logos, extra instruments, or visual elements from Video 1.
```

## Example: multi-asset product campaign

Inputs: Image 1 is a shoe; Image 2 is the athlete; Image 3 is the location mood; Video 1 supplies running motion and edit rhythm. Suggested settings: 15 seconds, 9:16, 2K.

```text
Create a 15-second vertical performance-footwear campaign with three concise shots.

Use Image 1 only for the exact shoe silhouette, sole geometry, knit pattern, laces, and charcoal-lime colorway. Do not invent logos or alter materials.
Use Image 2 only for the athlete's identity, hairstyle, body proportions, and black training kit. Do not copy its studio background or pose.
Use Image 3 only for the wet dawn-city palette, reflective pavement, and blue-gray atmosphere. Do not copy its people or signage.
Use Video 1 only for the athlete's stride mechanics, footfall timing, and accelerating cut rhythm. Adapt the movement to the city route; do not copy its athlete, clothing, camera location, or branding.

[0–4s]: Macro side view of Image 1's shoe landing on wet pavement; droplets compress outward on impact.
[4–10s]: Cut to a low tracking shot beside the athlete from Image 2 as the stride follows Video 1 and speed builds through the street from Image 3.
[10–15s]: Cut to a frontal medium shot, then arc slightly as the athlete stops beneath an overpass. End on a stable close product detail with the shoe fully readable.

Use crisp premium sports cinematography, hard dawn backlight, cool reflected color, realistic water, and controlled motion blur. Audio: synchronized footfalls, breath, distant city ambience, and a sparse pulse that accelerates with the referenced rhythm then stops on the final frame.

Preserve athlete identity and exact shoe design in every shot. Exactly one athlete and one shoe pair. No added text, logos, spectators, impossible foot deformation, or location elements from Video 1.
```

## Return

Provide:

- a compact asset ledger;
- suggested duration, aspect ratio, resolution, and endpoint;
- material assumptions, if any;
- one copy-ready prompt;
- 2–4 reference-conflict or continuity checks.

Do not return an API payload or submit a job.
