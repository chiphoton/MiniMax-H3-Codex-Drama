# Profile authoring checklist

## Authoring sequence

1. Choose a kebab-case ID and semantic version.
2. Set `inherits` to `base-video`.
3. Fill selection signals with outcome and platform cues, not copied titles.
4. Convert evidence into complete profile values; do not leave placeholder tokens.
5. Put concise machine-operational values in `profile.yaml`.
6. Put detailed narrative, shot, audio, caption, and QC guidance in the four Markdown files.
7. Copy the final evidence ledger to `evidence.json`.
8. Resolve and validate the profile.
9. Run a paper rehearsal.
10. List all generated files and ask the three validation choices.

## Rule quality

A useful rule states:

- what to do;
- when it applies;
- what it controls;
- what it must not change;
- evidence sources;
- confidence;
- whether it is required, recommended, or optional.

Avoid vague quality words without a visible or audible effect. Avoid instructions that can only be satisfied by copying the source content.

## Evidence shape

Use stable source IDs such as `video-01` and evidence IDs such as `video-01:scene-004` or `video-02:audio-summary`. Each inferred rule in `evidence.json` should contain:

```json
{
  "rule_id": "pace-ramp-before-payoff",
  "claim": "Shorten shots during the final setup, then hold the payoff.",
  "sources": ["video-01:scene-cuts", "video-02:scene-cuts"],
  "applies_when": "A reveal or CTA occupies the final quarter.",
  "confidence": 0.86,
  "status": "recommended"
}
```

Keep raw measurements in the evidence file rather than duplicating them in prose.

## Validation handoff

After a successful paper rehearsal ask exactly:

1. No validation.
2. Low-cost validation with 2–3 representative shots.
3. Full-video validation.

Do not start generation until the user chooses. For validation, compare formal grammar and production behavior, not character, plot, brand, or melody similarity.
