---
name: minimax-h3-profile-distiller
description: Distill one or more local reference videos into a safe, declarative MiniMax-H3 Drama production profile with evidence, confidence, storytelling grammar, shot patterns, audio and caption behavior, deliverables, and QC rules. Use when a user asks Codex to analyze, reverse-engineer, extract a reusable style or format from, or create a video profile based on uploaded or workspace video files.
---

# MiniMax-H3 Profile Distiller

Extract reusable production grammar from local videos without copying their characters, brands, dialogue, plot, music melody, or other source-specific content. Let explicit user instructions override the default exclusions.

## Accept and inspect inputs

Accept uploaded or workspace-local video files. Do not download a URL, sign into a platform, or bypass access controls. Record a supplied URL only as source provenance.

Inspect every input before asking questions. Ask one high-impact question at a time only when the intended reusable property is ambiguous. Multiple references should contribute shared rules; treat disagreements as optional variants rather than silently averaging incompatible patterns.

Run `scripts/analyze_video.py` for deterministic evidence:

```bash
python3 scripts/analyze_video.py \
  --input <video-1> --input <video-2> \
  --output-dir outputs/<project>/analysis
```

Read [references/distillation-method.md](references/distillation-method.md) before interpreting the evidence. Separate measured facts from visual inference and user preference.

## Build a declarative profile

Read the shared profile contract at `../minimax-h3-drama-producer/references/profile-spec.md` and validate against `../minimax-h3-drama-producer/references/profile.schema.json`.

Create a bundle containing exactly the useful files:

```text
profile/<slug>/
├── profile.yaml
├── storytelling.md
├── shot-patterns.md
├── audio-and-captions.md
├── qc-rules.md
└── evidence.json
```

Use `scripts/scaffold_profile.py` to create the bundle, then replace every placeholder with source-backed content. Keep `profile.yaml` data-only. Never embed commands, Python, shell, network requests, or installation instructions. Record each inferred rule with supporting source IDs, applicability, and confidence in `evidence.json`.

Read [references/profile-authoring.md](references/profile-authoring.md) for the authoring checklist. Resolve the profile on top of `base-video`, validate it with the producer's `scripts/profile_tool.py`, and perform a paper rehearsal against a fictional brief. Do not generate validation video by default.

## Save and optionally install

Save the first result inside `outputs/<project>/profile/<slug>/`. Do not mutate the plugin cache or a long-lived registry automatically.

Only on explicit install or import intent, use `scripts/install_profile.py`:

- project scope: `.minimax-h3-drama/profiles/<slug>/`;
- personal scope: `~/.config/minimax-h3-drama/profiles/<slug>/`.

Never overwrite an installed profile version without explicit approval. Profile lookup precedence is explicit path, project registry, personal registry, then built-ins.

## Hand off validation choices

After validation, list every generated file and summarize the strongest rules, variants, low-confidence areas, and paper-rehearsal result. Then ask the user to choose exactly one:

1. No validation.
2. Low-cost validation with 2–3 representative shots.
3. Full-video validation.

Wait for the choice. For option 2 or 3, load and apply `../minimax-h3-drama-producer/SKILL.md` with the distilled profile. Compare production grammar, not source-specific content similarity. Save revisions as a new version rather than overwriting the original profile.
