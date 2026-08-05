# Distillation method

## Evidence layers

Keep three layers separate:

1. **Measured** — duration, dimensions, frame rate, stream layout, scene-cut candidates, estimated average shot length, loudness, true peak, black frames, freezes, and sampled color statistics.
2. **Observed** — recurring framing, lens feel, camera movement, lighting, transition grammar, caption placement, performance, sound hierarchy, narrative topology, and CTA behavior.
3. **Chosen** — rules the user explicitly wants in the reusable profile, including exceptions to the default exclusions.

Never present a visual inference as a measured fact. Attach a confidence value from 0 to 1 and source evidence IDs to every distilled rule.

## Default exclusions

Do not distill these into reusable instructions unless the user explicitly requests them and has the right to do so:

- character identity or likeness;
- exact dialogue, narration, slogan, or plot;
- brand name, logo, product trademark, or unique package design;
- a recognizable music melody or source recording;
- source-specific locations, text, watermarks, or creator signatures.

Translate them into functions instead. For example, turn a specific reveal line into “identity reveal at 70–80% with a reaction beat,” or a branded end card into “centered product lockup plus concise CTA.”

## Multiple references

Compute measured evidence for every source separately. Mark a rule as shared only when it appears consistently across enough sources to justify the claim. Record disagreements as named variants with their own applicability and confidence.

Do not average incompatible formats. A 6-second bumper and a 60-second narrative may belong to different variants or different profiles.

## Distillation dimensions

Review:

- intended viewer experience and platform behavior;
- message or story beat topology and payoff timing;
- shot-count range, average shot length, pace changes, and holds;
- recurring shot sizes, camera height, movement, and screen direction;
- palette, contrast, lighting, texture, and environment density;
- transition frequency and sound bridges;
- voice, dialogue density, music role, effects, silence, and loudness;
- caption location, line count, emphasis, safe area, and CTA treatment;
- deliverable formats and technical thresholds;
- likely failure modes the profile must prevent.

## Paper rehearsal

Create a fictional brief in the same content class but with unrelated subjects and branding. Apply the draft profile to produce a compact beat sheet, asset plan, shot list, and QC checklist. A profile fails paper rehearsal when it lacks enough information to make these artifacts, contains source-specific content, or yields contradictory instructions.
