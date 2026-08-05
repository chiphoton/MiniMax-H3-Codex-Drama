# Production workflow

## Stage map

1. **Preflight** — inspect local capability and write the environment report.
2. **Initialize** — create or resume the project and snapshot the active profile.
3. **Ingest** — copy or reference inputs, hash them, and assign bounded roles.
4. **Plan** — create the production brief, story/message beats, entity ledger, asset ledger, continuity plan, shot list, and budget.
5. **Production approval** — required in guided mode.
6. **Visual development** — create missing entity masters, scene masters, storyboard, and keyframes.
7. **Visual-lock approval** — required in guided mode unless explicitly waived.
8. **Shot generation** — route, prepare, submit, monitor, fetch, and score takes.
9. **Post-production** — voice, captions, effects, music, picture edit, mix, and encodes.
10. **QC** — technical probes, full decode, contact sheets, visual continuity review, and fixes.
11. **Delivery** — select the canonical master, write media metadata, and return local links.

Update project state at every boundary. A blocked later stage must not erase completed earlier work.

## Planning rules

Preserve detailed user choices. Do not invent a main character, product claim, brand fact, or plot turn merely to make the brief feel complete. Ask about an execution-blocking omission; otherwise record a conservative production assumption.

Design each shot as an atomic, controllable action. A short generative clip should normally contain two or three timed beats, not an entire sequence. Mark shots whose ending must bridge continuously into the next shot.

For each shot record:

- narrative or message purpose;
- exact duration and timeline position;
- subjects, action order, performance, and screen direction;
- framing, camera height, lens feel, movement, lighting, and texture;
- dialogue, native sound, effects, music cue, and silence;
- incoming and outgoing transition;
- reference-to-role mapping and preservation constraints;
- T2V, frame-to-video, first/last-frame, reference-to-video, or edit route;
- ordinary or key-shot take budget;
- expected end state and shot-specific hard gates.

## Visual sources of truth

Create canonical masters only for recurring visual entities. Use the source type that matches the entity:

- character sheet for people;
- product sheet for product geometry and materials;
- identity sheet for mascots, animals, and stylized subjects;
- scene master for environment layout, fixed props, light direction, and axis.

When source references are loose, generate a normalized derivative sheet while retaining the original references as authority. Generate keyframes from approved entity and scene masters rather than regenerating identity independently per shot.

Follow [visual-development.md](visual-development.md) for the standard diagnostic views, environment layout requirements, storyboard metadata, and visual-lock review.

## Take selection

Score valid takes against:

- identity or product fidelity;
- required action completion and timing;
- composition and camera intent;
- scene, prop, light, and screen-direction continuity;
- audio usefulness;
- absence of hard-gate defects.

Select the best take using the profile rubric. Do not regenerate for vague improvement after the take budget is exhausted. Ask the user whether an additional attempt is worth the cost.
