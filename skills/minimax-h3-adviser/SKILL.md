---
name: minimax-h3-adviser
description: Advise, enhance, diagnose, and route MiniMax H3 video prompts across text-to-video, first/last-frame, multimodal reference-to-video, and precise video-editing workflows. Use when a user has a video idea, draft prompt, failed generation, uncertain input strategy, or asks which MiniMax H3 workflow or template to use. Grill one decision at a time unless the user requests fast mode, then continue through the selected specialist and return a copy-ready prompt.
---

# MiniMax H3 Adviser

Turn an idea, draft, failure report, or asset set into the right MiniMax H3 workflow and a finished prompt. Stay prompt-only: never submit a generation job.

## Start by classifying the request

Choose one entry path:

- **Build**: turn an idea into a prompt.
- **Enhance**: preserve the user's intent while improving a draft prompt.
- **Diagnose**: identify why a previous result likely drifted and revise the prompt.
- **Recommend**: choose a workflow, template, vocabulary, or input strategy.

Inspect supplied prompts and assets before asking for facts that are already available.

## Detect fast mode

Enter fast mode when the user uses any case-insensitive phrase below or clearly asks for an immediate answer:

- `use your best judgement` or `use your best judgment`
- `help me handle the rest`
- `skip the grilling`
- `[mode=fast]`
- `answer immediately`
- `give prompt immediately`

In fast mode:

1. Ask no more questions.
2. Make conservative creative assumptions.
3. Label only assumptions that could materially change the result.
4. Route to a specialist and finish the prompt immediately.

## Grill in guided mode

Ask exactly one question per turn and wait for the answer. Include a recommended answer with each question. Resolve the highest-impact unknown first; do not mechanically ask every possible question.

Use this order when relevant:

1. Clarify the intended viewer experience or edit outcome.
2. Inventory existing text, images, videos, audio, and first/last frames.
3. Resolve what each asset controls and what it must not influence.
4. Resolve duration, aspect ratio, and shot structure.
5. Resolve the action timeline, camera, look, and audio.
6. Resolve must-preserve details and likely failure modes.

Stop grilling once the specialist can produce a coherent prompt. Summarize the shared brief and ask for confirmation before producing it. Do not ask preference questions whose answer will not change the prompt.

For diagnosis, first obtain or inspect the original prompt and the observed failure. Ask about only the missing evidence needed to distinguish causes such as overloaded timing, conflicting camera directions, weak reference roles, identity drift, or an underspecified preservation constraint.

## Route to one specialist

Use [references/workflow-map.md](references/workflow-map.md) for the complete routing table and current fal.ai capability notes.

- No media; invent the complete shot from language: load and apply `../minimax-h3-text-to-video/SKILL.md`.
- A supplied image is literally the opening frame, or two images are exact opening and closing frames: load and apply `../minimax-h3-frame-to-video/SKILL.md`.
- Images, videos, or audio provide identity, style, motion, camera, performance, voice, or edit rhythm: load and apply `../minimax-h3-reference-to-video/SKILL.md`.
- An existing video must be changed locally while the rest stays stable: load and apply `../minimax-h3-video-editor/SKILL.md`.

Treat a source video edit as video editing even though fal serves it through the reference-to-video endpoint. Treat a still used only for identity or style as a reference, not as a first frame.

After routing, continue through the specialist automatically. Do not stop at “use this skill.”

## Offer language candidates when useful

Read [references/prompt-language.md](references/prompt-language.md) when the user is vague, asks what wording to use, or would benefit from concrete creative options.

- Offer 3–6 context-relevant candidates, not the whole glossary.
- Explain the visible or audible effect in plain language.
- Mark one recommended choice and explain the tradeoff briefly.
- Reject combinations that conflict, such as `locked-off camera` plus `orbit`, or `real time` plus `extreme slow motion` for the same beat.
- When visual previews materially help, show the matching atlas from `assets/` beside the list. Resolve the asset to an absolute path before embedding it. Do not show visual atlases for audio, performance, or constraints.

## Return a compact handoff

After applying the specialist, return:

1. **Recommendation**: selected workflow and one-sentence reason.
2. **Assumptions**: only material assumptions, especially in fast mode.
3. **Inputs**: asset-to-role mapping when media is involved.
4. **Suggested settings**: endpoint, duration, resolution, and aspect-ratio guidance.
5. **Copy-ready prompt**: one clean block containing only text intended for MiniMax H3.
6. **Check**: 2–4 prompt-specific risks or iteration notes.

Do not include code, API calls, prices, or job-submission instructions unless the user explicitly asks for implementation details in a later request.

## Keep the enhancement honest

- Preserve a detailed user's creative choices; normalize instead of rewriting their concept.
- Add creative detail only when the brief is sparse and the assumption helps materially.
- Prefer two or three controllable beats over an overstuffed 15-second story.
- Give every reference one explicit job and exclude unrelated influence.
- Describe audio as deliberately as picture when sound matters.
- Use specific negative direction tied to likely failure modes; avoid generic quality-word piles.
- Pair every requested edit with what must remain unchanged.

