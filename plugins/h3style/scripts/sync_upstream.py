#!/usr/bin/env python3
"""Refresh the vendored official MiniMax-H3 skills without replacing adapters."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parent.parent
SKILLS_ROOT = PLUGIN_ROOT / "skills"
LOCK_PATH = PLUGIN_ROOT / "upstream-lock.json"
MANIFEST_PATH = PLUGIN_ROOT / ".codex-plugin" / "plugin.json"
UPSTREAM_REPOSITORY = "https://github.com/MiniMax-AI/MiniMax-H3.git"
PORTABLE_SKILL = "h3-prompt-writing"
IGNORED_NAMES = {".DS_Store", "__pycache__"}


class SyncError(RuntimeError):
    pass


def run_git(repository: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repository), *args],
        check=False,
        text=True,
        capture_output=True,
    )
    if completed.returncode:
        raise SyncError(completed.stderr.strip() or "git command failed")
    return completed.stdout.strip()


def tree_digest(path: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    count = 0
    for file_path in sorted(path.rglob("*")):
        if not file_path.is_file() or any(part in IGNORED_NAMES for part in file_path.parts):
            continue
        relative = file_path.relative_to(path).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(file_path.read_bytes())
        digest.update(b"\0")
        count += 1
    return digest.hexdigest(), count


def replace_tree(source: Path, destination: Path) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(
        source,
        destination,
        ignore=shutil.ignore_patterns(".DS_Store", "__pycache__"),
    )


def generic_adapter(name: str) -> str:
    return f"""---
name: {name}
description: Apply the official MiniMax H3 {name} workflow in Codex as a planning and prompt adapter. Use when the user explicitly requests this official workflow or clearly matches its specialty; do not use for unrelated generic H3 prompts.
---

# {name}

Read [the vendored official workflow](references/official/SKILL.md) completely, plus only the official references it links for the current request. Preserve its creative decisions, facts, approval gates, style locks, and quality checks.

Adapt MiniMax Hub-only operations to Codex:

- Replace canvas nodes with concise inline artifacts or user-requested local files.
- Replace choice cards with ordinary concise questions or options.
- Never claim to call `hub_*` tools or to have generated media when those tools are unavailable.
- If called by `minimax-h3-drama:minimax-h3-adviser`, return a compact style brief to it and do not load the adviser again.
- For prompt-only work, load and apply `../h3-prompt-writing/SKILL.md` when official H3 field formatting is useful.
- For generation, continue only on explicit execution intent and hand the approved brief to an available MiniMax H3 execution skill; otherwise return production-ready prompts.

Keep upstream material under `references/official/` unchanged. This adapter owns only runtime translation.
"""


def ensure_new_adapter(name: str) -> None:
    skill_root = SKILLS_ROOT / name
    skill_root.mkdir(parents=True, exist_ok=True)
    entrypoint = skill_root / "SKILL.md"
    if not entrypoint.exists():
        entrypoint.write_text(generic_adapter(name), encoding="utf-8")


def vendored_matches(lock: dict[str, object]) -> bool:
    skills = lock.get("skills")
    if not isinstance(skills, dict):
        return False
    for name, metadata in skills.items():
        if not isinstance(metadata, dict):
            return False
        entrypoint = SKILLS_ROOT / name / "SKILL.md"
        vendored = SKILLS_ROOT / name / "references" / "official"
        if not entrypoint.is_file() or not vendored.is_dir():
            return False
        digest, file_count = tree_digest(vendored)
        if digest != metadata.get("sha256") or file_count != metadata.get("files"):
            return False
    return True


def manifest_matches(lock: dict[str, object]) -> bool:
    try:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return manifest.get("version") == lock.get("plugin_version")


def update_manifest_version(version: str) -> None:
    try:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except OSError as exc:
        raise SyncError(f"Unable to read {MANIFEST_PATH}") from exc
    except json.JSONDecodeError as exc:
        raise SyncError(f"Invalid JSON in {MANIFEST_PATH}") from exc
    manifest["version"] = version
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def build_lock(repository: Path) -> dict[str, object]:
    source_skills = repository / "skills"
    if not source_skills.is_dir():
        raise SyncError(f"No skills directory found under {repository}")

    skills: dict[str, object] = {}
    for source in sorted(source_skills.iterdir()):
        if not source.is_dir() or not (source / "SKILL.md").is_file():
            continue
        digest, file_count = tree_digest(source)
        skills[source.name] = {
            "path": f"skills/{source.name}",
            "files": file_count,
            "sha256": digest,
            "portable": source.name == PORTABLE_SKILL,
        }

    commit_date = run_git(repository, "show", "-s", "--format=%cI", "HEAD")
    parsed_date = datetime.fromisoformat(commit_date)
    official_update_date = parsed_date.strftime("%Y-%m-%d")
    plugin_version = f"{parsed_date.year}.{parsed_date.month}.{parsed_date.day}"

    return {
        "schema_version": 1,
        "repository": UPSTREAM_REPOSITORY,
        "commit": run_git(repository, "rev-parse", "HEAD"),
        "commit_date": commit_date,
        "official_update_date": official_update_date,
        "plugin_version": plugin_version,
        "synced_at": datetime.now(timezone.utc).isoformat(),
        "skills": skills,
    }


def sync(repository: Path, check: bool) -> bool:
    lock = build_lock(repository)
    comparable = dict(lock)
    comparable.pop("synced_at", None)
    current: dict[str, object] = {}
    if LOCK_PATH.is_file():
        current = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
        current.pop("synced_at", None)

    if check:
        clean = comparable == current and vendored_matches(lock) and manifest_matches(lock)
        print("up to date" if clean else "update available")
        return clean

    source_skills = repository / "skills"
    for name in lock["skills"]:
        source = source_skills / name
        ensure_new_adapter(name)
        replace_tree(source, SKILLS_ROOT / name / "references" / "official")

    update_manifest_version(str(lock["plugin_version"]))
    LOCK_PATH.write_text(json.dumps(lock, indent=2) + "\n", encoding="utf-8")
    print(
        f"synced {len(lock['skills'])} skills from {lock['commit']} "
        f"as h3style {lock['plugin_version']}"
    )
    return True


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        type=Path,
        help="Existing MiniMax-H3 Git checkout. Omit to clone the official repository.",
    )
    parser.add_argument("--check", action="store_true", help="Report drift without writing files.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.source:
            return 0 if sync(args.source.resolve(), args.check) else 1
        with tempfile.TemporaryDirectory(prefix="h3style-upstream-") as temporary:
            repository = Path(temporary) / "MiniMax-H3"
            completed = subprocess.run(
                ["git", "clone", "--depth", "1", UPSTREAM_REPOSITORY, str(repository)],
                check=False,
            )
            if completed.returncode:
                raise SyncError("Unable to clone the official MiniMax-H3 repository")
            return 0 if sync(repository, args.check) else 1
    except (OSError, ValueError, SyncError) as exc:
        print(f"error: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
