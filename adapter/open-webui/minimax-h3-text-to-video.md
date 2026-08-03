---
name: minimax-h3-text-to-video
description: Create, enhance, or diagnose MiniMax H3 text-to-video prompts when the entire video should be invented from language without image, video, or audio references. Use for prompt-only cinematic shots, ads, animation, motion design, social clips, UI demos, or other H3 concepts that need a timed action plan, camera direction, visual treatment, native audio direction, constraints, settings, templates, or copy-ready prompt output.
---

# MiniMax H3 Text to Video

Design a complete MiniMax H3 shot from text alone. Stay prompt-only and never submit a generation job.

## Confirm the workflow

Use this workflow only when no uploaded media is meant to control the result. If an image is the exact first frame, recommend the MiniMax H3 frame-to-video workflow. If any asset supplies identity, style, motion, voice, or editing rhythm, recommend the reference-to-video workflow.

For fal.ai, recommend endpoint `minimax/h3/text-to-video`, duration 5–15 seconds, resolution `768P` or `2K`, and one of these fixed aspect ratios: `21:9`, `16:9`, `4:3`, `1:1`, `3:4`, or `9:16`. Treat provider capabilities as changeable; verify them when the user requests current API accuracy.

## Build the prompt

1. State duration, aspect ratio, format, and whether the clip is one continuous shot or a short sequence.
2. Describe the subject and environment with only details that matter on screen.
3. For more than one beat, allocate timecoded actions whose durations add up correctly.
4. Choose one principal camera behavior per beat.
5. Describe lighting, palette, texture, and production language.
6. Direct dialogue, ambience, effects, and music with timing when relevant.
7. Finish with a short list of concrete continuity and exclusion constraints.

Prefer a single continuous shot for one simple transformation or performance. Use multiple shots only when the concept truly depends on editing. Do not cram a full narrative arc into a short clip.

## Enhance or diagnose

When enhancing, preserve the user's nouns, actions, order, exact copy, and style choices. Repair missing timing, ambiguous camera language, unsupported cause-and-effect, and vague constraints.

When diagnosing, test for:

- too many actions for the duration;
- conflicting camera or speed directions;
- unclear subject count or spatial relationships;
- audio events with no timing anchor;
- broad negative lists that hide the actual failure risk;
- a requested final composition that no preceding motion reaches.

## Canonical template

Use only sections that improve control. Remove unused placeholders before returning the prompt.

```text
Create a [duration]-second [aspect-ratio] [format/genre] video as [one continuous shot / a concise sequence of N shots].

SUBJECT AND SETTING
[Who or what appears, defining visual details, location, time, weather, and spatial layout.]

ACTION AND TIMING
[0–Xs]: [Opening composition and first action.]
[X–Ys]: [Main change, interaction, or reveal.]
[Y–end]: [Final action and precise ending composition.]

CAMERA
[Starting framing and lens feel.] The camera [one principal movement], [timing and purpose].

VISUAL TREATMENT
[Medium/production language, lighting, palette, material texture, depth of field, atmosphere.]

AUDIO
[Dialogue verbatim if any. Ambience, foley, effects, and music, including synchronization points.]

CONSTRAINTS
[Must-preserve continuity, exact counts, forbidden cuts/elements/text, physical plausibility, final-frame hold.]
```

## Example: premium product reveal

Suggested settings: 10 seconds, 16:9, 2K.

```text
Create a 10-second premium coffee-equipment commercial in 16:9 as one continuous shot.

A compact brushed-steel espresso machine stands alone on a dark walnut counter in a quiet studio kitchen before sunrise. Preserve its simple rectangular silhouette, black control dial, chrome steam wand, and small white ceramic cup.

[0–3s]: Begin in an extreme close-up as the control dial clicks into place and the indicator light warms from dark to amber.
[3–7s]: Track slowly along the machine while espresso streams into the cup; fine crema forms and a small ribbon of steam catches the backlight.
[7–10s]: Pull back into a centered three-quarter hero view. The stream stops, one final drop falls, and the shot holds steady for the last second.

Use clean commercial cinematography, long-lens compression, shallow depth of field, soft amber rim light, and controlled reflections on the steel. Keep the background minimal and low-key.

Audio: a tactile dial click, quiet pump vibration, close liquid pour, a faint ceramic resonance, and one restrained low musical tone that resolves as the hero frame settles.

Keep exactly one machine and one cup. Preserve product geometry throughout. No hands, people, logos, captions, sudden cuts, camera shake, or extra props.
```

## Example: phone-captured magical moment

Suggested settings: 12 seconds, 9:16, 2K.

```text
Create a 12-second vertical live-action clip that feels like an unexpected moment captured one-handed on a phone, presented as one continuous shot.

At night in a small apartment hallway, a folded paper crane rests on a shoe cabinet beneath a warm wall lamp. The hallway is ordinary and slightly cluttered, with worn paint, a hanging coat, and rain tapping a nearby window.

[0–4s]: Start in a loose medium shot. The camera hesitates and autofocus settles on the crane as one paper wing twitches.
[4–9s]: The crane unfolds its legs, stands, and takes two fragile steps. Its paper edges glow very faintly while the camera moves closer with natural hand tremor.
[9–12s]: It lifts a few centimeters, circles once near the lamp, then lands on the cabinet and becomes still.

Use realistic phone exposure breathing, soft sensor noise in the shadows, imperfect focus pulls, and warm practical light. Keep the paper texture physically convincing; the event should feel surprising but not polished or theatrical.

Audio: rain against glass, distant plumbing, the camera operator's quiet breath, dry paper creases, and a tiny bell-like tone only when the crane lifts. No music.

No cuts, extra creatures, giant glow effects, sparks, horror imagery, text, logos, or sudden camera moves. Keep the hallway and cabinet geometry stable.
```

## Return

Provide:

- suggested duration, aspect ratio, resolution, and endpoint;
- material assumptions, if any;
- one copy-ready prompt;
- 2–4 prompt-specific checks or a single alternative when it adds value.

Do not return an API payload or submit a job.
