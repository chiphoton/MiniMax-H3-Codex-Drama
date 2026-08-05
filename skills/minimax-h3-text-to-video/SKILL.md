---
name: minimax-h3-text-to-video
description: Create, enhance, or diagnose MiniMax H3 text-to-video prompts when the entire video should be invented from language without image, video, or audio references. Use for prompt-only cinematic shots, ads, animation, motion design, social clips, UI demos, or other H3 concepts that need a timed action plan, camera direction, visual treatment, native audio direction, constraints, settings, templates, or copy-ready prompt output.
---

# MiniMax H3 Text to Video

Design a complete MiniMax H3 shot from text alone. Stay prompt-only and never submit a generation job.

## Confirm this workflow

Use this skill only when no uploaded media is meant to control the result. If an image is an exact first frame, use `../minimax-h3-frame-to-video/SKILL.md`. If any asset supplies identity, style, motion, voice, or editing rhythm, use `../minimax-h3-reference-to-video/SKILL.md`.

Recommend a 5–15 second clip, `768P` for iteration or `2K` for a final pass when the active workflow and hardware support it, and a fixed aspect ratio such as `21:9`, `16:9`, `4:3`, `1:1`, `3:4`, or `9:16`. Treat these as starting settings and let the executor validate the installed workflow.

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

## Use the template and examples

Read [references/template-and-examples.md](references/template-and-examples.md) for the canonical fill-in template and two representative examples. Adapt their structure, not their subject matter.

## Return

Provide:

- suggested duration, aspect ratio, resolution, and workflow route;
- material assumptions, if any;
- one copy-ready prompt;
- 2–4 prompt-specific checks or a single alternative when it adds value.

Do not return an API payload or submit a job.
