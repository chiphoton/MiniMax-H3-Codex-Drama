# Project contract

## Directory layout

```text
outputs/<project>/
├── project.yaml
├── inputs/
│   ├── brief/
│   └── references/{images,video,audio}/
├── planning/
│   ├── production-brief.md
│   ├── story.md
│   ├── entities.md
│   ├── asset-ledger.yaml
│   ├── continuity.yaml
│   └── shot-list.yaml
├── profile/
├── prompts/{gpt-image,minimax-h3,tts}/
├── images/{entity-sheets,scenes,storyboards,keyframes}/
├── workflows/
├── clips/{raw,selected}/
├── audio/{dialogue,music,sfx,mix}/
├── subtitles/
├── edit/
├── qc/
├── final/
└── logs/
```

Use `scripts/init_project.py` to create this layout. A user-supplied project name wins. Otherwise derive a short kebab-case slug from the subject. Append a timestamp only on a collision.

## State file

Treat `project.yaml` as the single state ledger. The bundled scripts write JSON-compatible YAML so they remain usable with the Python standard library. A full YAML parser may edit the same file. Prefer `scripts/project_state.py` for routine stage, job, artifact, and take-selection updates.

Record:

- schema version, project title, slug, mode, language, timestamps, and workspace;
- active base, primary, and resolved profile snapshots;
- input path, copied path, hash, byte size, modality, assigned roles, provenance, and license note;
- stage status: `pending`, `in_progress`, `blocked`, `failed`, or `completed`;
- shot IDs, key-shot flag, route, prompts, workflow, takes, prompt IDs, selected take, and QC;
- artifacts with role, version, path, and source dependencies;
- material assumptions and an append-only event history.

Do not mark a stage complete until its required artifacts exist. Do not infer completion solely from a directory name.

## Resume and version rules

- If the project directory contains a valid state file, resume it by default.
- If the directory exists without a valid state file, stop instead of adopting unknown files.
- Skip artifacts whose state is completed, whose file still exists, and whose dependencies have not changed.
- Add attempts and versions; do not overwrite previous generated media.
- Keep stable selected copies or links in `clips/selected/` and `final/master.mp4` while retaining versioned originals.
- Rebuild only the requested stage and downstream dependents.
- Preserve failed attempts for diagnosis. Never clean them without explicit intent.

## Input ingestion

Copy normal-sized user inputs into the project and never modify the originals. Use content hashes to avoid duplicate copies. Ask before copying unusually large files; an external reference must be marked `portable: false` and rechecked during QC.

Every reference needs at least one bounded role such as identity, wardrobe, product geometry, environment, style, first frame, last frame, motion, camera, performance, voice, music, or edit rhythm. Record what it must not influence when cross-reference leakage is plausible.
