# Profile specification

## Resolution model

Resolve exactly one primary profile over `base-video`, then apply explicit project overrides. Deep-merge mappings, replace lists as complete values, and replace scalars. Never merge two primary profiles implicitly.

Profile precedence is:

1. current user instruction;
2. project override;
3. selected primary profile;
4. `base-video`;
5. built-in fallback.

Snapshot the base, primary, overrides, and fully resolved profile into the project before planning so later plugin updates cannot change an active production silently.

## Bundle format

```text
<profile-slug>/
├── profile.yaml
├── storytelling.md
├── shot-patterns.md
├── audio-and-captions.md
├── qc-rules.md
└── evidence.json          # required for distilled profiles only
```

`profile.yaml` must conform to [profile.schema.json](profile.schema.json). It is declarative data and may not contain commands, code, URLs to execute, environment mutation, or installation instructions. The bundled profiles use JSON-compatible YAML for dependency-free parsing; conventional YAML is accepted when PyYAML is available.

The Markdown files contain detailed guidance loaded only for their production stage. Do not duplicate the full YAML configuration in prose.

## Required concepts

Define:

- identity, display name, semantic version, schema version, kind, parent, and summary;
- selection signals and intended viewer outcome;
- platform format, duration, aspect ratio, resolution, and frame rate;
- story authority, expansion policy, required beats, and pacing;
- required and recommended asset roles;
- shot duration, key-shot classes, generation routes, takes, and retry ceiling;
- entity and scene master policy plus keyframe strategy;
- voice, captions, music, native audio, and loudness targets;
- edit rhythm, allowed transitions, safe areas, and cover strategy;
- required and optional deliverables;
- technical hard gates, visual hard gates, soft warnings, and numeric tolerances.

## Lookup order

Resolve profile identifiers in this order:

1. explicit path supplied by the user;
2. `<workspace>/.minimax-h3-drama/profiles/`;
3. `~/.config/minimax-h3-drama/profiles/`;
4. `references/profiles/` bundled with this skill.

Reject ambiguous duplicate IDs at the same precedence level. Never modify a bundled profile at runtime.

## Versioning and validation

Use semantic versions for profiles. A distilled revision must receive a new version. Run:

```bash
python3 scripts/profile_tool.py validate <profile.yaml>
python3 scripts/profile_tool.py resolve \
  --base references/profiles/base-video/profile.yaml \
  --profile <profile.yaml> \
  --output <resolved-profile.yaml>
```

Validation rejects unknown top-level keys, executable-looking keys, invalid types, missing hard gates, and values outside safe numeric ranges. Resolution validates both sources and the merged result.
