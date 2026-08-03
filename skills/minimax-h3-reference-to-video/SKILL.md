---
name: minimax-h3-reference-to-video
description: Create, enhance, or diagnose MiniMax H3 multimodal reference-to-video prompts using images, videos, and audio for identity, product design, style, location, storyboard, motion, camera, editing rhythm, performance, music, or voice. Use when multiple assets need explicit jobs, unwanted cross-reference influence must be blocked, or users need an asset ledger, timed shot plan, preservation constraints, settings, template, or copy-ready H3 prompt.
---

# MiniMax H3 Reference to Video

Turn multimodal assets into one coherent MiniMax H3 direction by giving every asset an explicit, bounded job. Stay prompt-only and never submit a generation job.

## Confirm this workflow

Use this skill when media acts as a reference rather than an exact first or last frame. If the only visual input is the literal opening frame, use `../minimax-h3-frame-to-video/SKILL.md`. If an existing video is being changed locally while the rest stays stable, use `../minimax-h3-video-editor/SKILL.md`.

For current fal.ai settings, recommend endpoint `minimax/h3/reference-to-video`, duration 5–15 seconds, resolution `768P` or `2K`, and a fixed or `adaptive` aspect ratio. The current fal schema allows up to 9 images, 3 videos, and 3 audio clips with no more than 12 files total. Reference video and audio clips are 2–15 seconds each with no more than 15 seconds combined per modality; audio cannot be the only reference type.

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

## Use the template and examples

Read [references/template-and-examples.md](references/template-and-examples.md) for the canonical fill-in template and two representative examples. Adapt their asset-assignment syntax, not their subject matter.

## Return

Provide:

- a compact asset ledger;
- suggested duration, aspect ratio, resolution, and endpoint;
- material assumptions, if any;
- one copy-ready prompt;
- 2–4 reference-conflict or continuity checks.

Do not return an API payload or submit a job.

