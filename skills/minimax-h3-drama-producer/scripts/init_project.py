#!/usr/bin/env python3
"""Create or resume a non-destructive MiniMax-H3 Drama project."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import profile_tool


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
BUILTIN_PROFILES = SKILL_DIR / "references" / "profiles"
SCHEMA_VERSION = "1.0"

DIRECTORIES = [
    "inputs/brief",
    "inputs/references/images",
    "inputs/references/video",
    "inputs/references/audio",
    "planning",
    "profile/base",
    "profile/primary",
    "prompts/gpt-image",
    "prompts/minimax-h3",
    "prompts/tts",
    "images/entity-sheets",
    "images/scenes",
    "images/storyboards",
    "images/keyframes",
    "workflows",
    "clips/raw",
    "clips/selected",
    "audio/dialogue",
    "audio/music",
    "audio/sfx",
    "audio/mix",
    "subtitles",
    "edit",
    "qc",
    "final",
    "logs",
]

IMAGE_EXTENSIONS = {".avif", ".bmp", ".gif", ".heic", ".jpeg", ".jpg", ".png", ".tif", ".tiff", ".webp"}
VIDEO_EXTENSIONS = {".avi", ".m4v", ".mkv", ".mov", ".mp4", ".mpeg", ".mpg", ".webm"}
AUDIO_EXTENSIONS = {".aac", ".aiff", ".flac", ".m4a", ".mp3", ".ogg", ".opus", ".wav"}


class ProjectError(Exception):
    """Raised when project initialization would be unsafe or ambiguous."""


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def slugify(value: str) -> str:
    original = value.strip()
    normalized = re.sub(r"[^a-z0-9]+", "-", original.lower())
    normalized = re.sub(r"-+", "-", normalized).strip("-")
    digest = hashlib.sha256(original.encode("utf-8")).hexdigest()[:8]
    if not normalized:
        normalized = f"video-project-{digest}"
    elif any(ord(char) > 127 and char.isalnum() for char in original):
        normalized = f"{normalized[:55].rstrip('-')}-{digest}"
    return normalized[:64].rstrip("-")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_write(path: Path, data: dict[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def load_state(path: Path) -> dict[str, Any]:
    state = profile_tool.load_data(path)
    if state.get("schema_version") != SCHEMA_VERSION:
        raise ProjectError(
            f"unsupported project schema {state.get('schema_version')!r} in {path}"
        )
    if not isinstance(state.get("project"), dict) or not state["project"].get("slug"):
        raise ProjectError(f"invalid project state in {path}")
    return state


def find_profile(identifier: str, workspace: Path) -> Path:
    direct = Path(identifier).expanduser()
    if direct.exists():
        candidate = direct / "profile.yaml" if direct.is_dir() else direct
        return candidate.resolve()

    registries = [
        workspace / ".minimax-h3-drama" / "profiles" / identifier / "profile.yaml",
        Path.home() / ".config" / "minimax-h3-drama" / "profiles" / identifier / "profile.yaml",
        BUILTIN_PROFILES / identifier / "profile.yaml",
    ]
    matches = [path.resolve() for path in registries if path.exists()]
    if not matches:
        raise ProjectError(f"profile {identifier!r} was not found")
    return matches[0]


def copy_profile_bundle(profile_file: Path, destination: Path) -> None:
    source_dir = profile_file.parent
    destination.mkdir(parents=True, exist_ok=True)
    for source in sorted(source_dir.iterdir()):
        if source.is_file():
            shutil.copy2(source, destination / source.name)


def modality_for(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in IMAGE_EXTENSIONS:
        return "images"
    if suffix in VIDEO_EXTENSIONS:
        return "video"
    if suffix in AUDIO_EXTENSIONS:
        return "audio"
    return "other"


def unique_destination(directory: Path, source_name: str, digest: str) -> Path:
    safe_stem = slugify(Path(source_name).stem)
    suffix = Path(source_name).suffix.lower()
    candidate = directory / f"{safe_stem}{suffix}"
    if not candidate.exists():
        return candidate
    return directory / f"{safe_stem}-{digest[:8]}{suffix}"


def ingest_file(
    source: Path,
    project_dir: Path,
    *,
    category: str,
    copy_mode: str,
    threshold_bytes: int,
    known_hashes: set[str] | None = None,
) -> dict[str, Any] | None:
    source = source.expanduser().resolve()
    if not source.is_file():
        raise ProjectError(f"input is not a file: {source}")
    size = source.stat().st_size
    modality = modality_for(source)
    if category == "reference" and modality == "other":
        raise ProjectError(
            f"unsupported reference type for {source}; use --brief for text or provide image, video, or audio"
        )

    effective_mode = copy_mode
    if copy_mode == "auto" and size > threshold_bytes:
        raise ProjectError(
            f"{source} is {size} bytes, above the copy threshold; rerun with "
            "--large-input-mode copy or --large-input-mode reference"
        )
    if copy_mode == "auto":
        effective_mode = "copy"

    digest = sha256_file(source)
    if known_hashes is not None and digest in known_hashes:
        return None

    copied_path: str | None = None
    portable = effective_mode == "copy"
    if effective_mode == "copy":
        if category == "brief":
            destination_dir = project_dir / "inputs" / "brief"
        else:
            destination_dir = project_dir / "inputs" / "references" / modality
        destination = unique_destination(destination_dir, source.name, digest)
        if not destination.exists():
            shutil.copy2(source, destination)
        copied_path = str(destination.relative_to(project_dir))

    return {
        "id": f"input-{digest[:12]}",
        "category": category,
        "modality": modality,
        "original_path": str(source),
        "project_path": copied_path,
        "sha256": digest,
        "size_bytes": size,
        "ingest_mode": effective_mode,
        "portable": portable,
        "roles": ["unassigned"],
        "forbidden_influence": [],
        "provenance": "user-provided",
        "license_note": "unreviewed",
    }


def initial_state(
    *,
    project_dir: Path,
    slug: str,
    title: str,
    mode: str,
    language: str,
    workspace: Path,
    profile_source: Path,
    base_source: Path,
) -> dict[str, Any]:
    now = utc_now()
    stages = {
        name: {"status": "pending", "updated_at": now, "note": None}
        for name in [
            "preflight",
            "ingest",
            "planning",
            "production-approval",
            "visual-development",
            "visual-lock",
            "shot-generation",
            "post-production",
            "qc",
            "delivery",
        ]
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "project": {
            "slug": slug,
            "title": title,
            "mode": mode,
            "language": language,
            "workspace": str(workspace.resolve()),
            "created_at": now,
            "updated_at": now,
            "status": "active",
        },
        "profile": {
            "base_source": str(base_source),
            "primary_source": str(profile_source),
            "base_snapshot": "profile/base/profile.yaml",
            "primary_snapshot": "profile/primary/profile.yaml",
            "resolved_snapshot": "profile/resolved-profile.yaml",
            "override": None,
        },
        "inputs": [],
        "stages": stages,
        "shots": [],
        "artifacts": [],
        "jobs": [],
        "assumptions": [],
        "history": [
            {"at": now, "event": "project-created", "detail": {"project_dir": str(project_dir)}}
        ],
    }


def create_project(args: argparse.Namespace) -> tuple[Path, dict[str, Any], bool]:
    workspace = args.workspace.expanduser().resolve()
    outputs_dir = args.outputs_dir
    if not outputs_dir.is_absolute():
        outputs_dir = workspace / outputs_dir
    slug = slugify(args.project)
    project_dir = outputs_dir / slug
    state_path = project_dir / "project.yaml"

    if project_dir.exists():
        if not state_path.is_file():
            raise ProjectError(
                f"{project_dir} already exists without a valid project.yaml; choose another project name"
            )
        state = load_state(state_path)
        if args.profile:
            requested_profile = find_profile(args.profile, workspace)
            active_profile = Path(state["profile"]["primary_source"]).resolve()
            if requested_profile != active_profile:
                raise ProjectError(
                    "the existing project uses a different primary profile; create a new project "
                    "or record an explicit profile migration"
                )
        return project_dir, state, True

    profile_source = find_profile(args.profile or "base-video", workspace)
    profile_data = profile_tool.load_data(profile_source)
    errors = profile_tool.validate_data(
        profile_data, profile_tool.load_data(profile_tool.DEFAULT_SCHEMA)
    )
    if errors:
        raise ProjectError("invalid primary profile: " + "; ".join(errors))

    base_source = BUILTIN_PROFILES / "base-video" / "profile.yaml"
    resolved = profile_tool.deep_merge(
        profile_tool.load_data(base_source), profile_data
    )
    resolved_errors = profile_tool.validate_data(
        resolved, profile_tool.load_data(profile_tool.DEFAULT_SCHEMA)
    )
    if resolved_errors:
        raise ProjectError("invalid resolved profile: " + "; ".join(resolved_errors))

    state = initial_state(
        project_dir=project_dir,
        slug=slug,
        title=args.title or args.project,
        mode=args.mode,
        language=args.language,
        workspace=workspace,
        profile_source=profile_source,
        base_source=base_source.resolve(),
    )

    outputs_dir.mkdir(parents=True, exist_ok=True)
    staging_dir = outputs_dir / f".{slug}.initializing-{os.getpid()}"
    if staging_dir.exists():
        raise ProjectError(f"staging directory already exists: {staging_dir}")
    try:
        for relative in DIRECTORIES:
            (staging_dir / relative).mkdir(parents=True, exist_ok=True)
        copy_profile_bundle(base_source, staging_dir / "profile" / "base")
        copy_profile_bundle(profile_source, staging_dir / "profile" / "primary")
        profile_tool.dump_data(staging_dir / "profile" / "resolved-profile.yaml", resolved)
        atomic_write(staging_dir / "project.yaml", state)
        if project_dir.exists():
            raise ProjectError(
                f"{project_dir} appeared during initialization; rerun to inspect it safely"
            )
        os.replace(staging_dir, project_dir)
    except Exception:
        if staging_dir.exists():
            shutil.rmtree(staging_dir)
        raise
    return project_dir, state, False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    parser.add_argument("--outputs-dir", type=Path, default=Path("outputs"))
    parser.add_argument("--project", required=True, help="project title or kebab-case slug")
    parser.add_argument("--title")
    parser.add_argument("--profile")
    parser.add_argument("--mode", choices=["guided", "fast"], default="guided")
    parser.add_argument("--language", default="auto")
    parser.add_argument("--brief", type=Path, action="append", default=[])
    parser.add_argument("--input", type=Path, action="append", default=[])
    parser.add_argument("--copy-threshold-mb", type=int, default=1024)
    parser.add_argument(
        "--large-input-mode", choices=["auto", "copy", "reference"], default="auto"
    )
    args = parser.parse_args()

    try:
        project_dir, state, resumed = create_project(args)
        threshold = args.copy_threshold_mb * 1024 * 1024
        known_hashes = {str(item.get("sha256")) for item in state.get("inputs", []) if item.get("sha256")}
        new_input_count = 0
        for category, paths in (("brief", args.brief), ("reference", args.input)):
            for path in paths:
                item = ingest_file(
                    path,
                    project_dir,
                    category=category,
                    copy_mode=args.large_input_mode,
                    threshold_bytes=threshold,
                    known_hashes=known_hashes,
                )
                if item is not None:
                    state["inputs"].append(item)
                    known_hashes.add(item["sha256"])
                    new_input_count += 1

        now = utc_now()
        state["project"]["updated_at"] = now
        if args.brief or args.input:
            state["stages"]["ingest"] = {
                "status": "in_progress",
                "updated_at": now,
                "note": "Inputs ingested; asset roles still require review.",
            }
        state["history"].append(
            {
                "at": now,
                "event": "project-resumed" if resumed else "project-initialized",
                "detail": {"new_inputs": new_input_count},
            }
        )
        atomic_write(project_dir / "project.yaml", state)
        print(
            json.dumps(
                {
                    "project_dir": str(project_dir),
                    "state": str(project_dir / "project.yaml"),
                    "resumed": resumed,
                    "profile": state["profile"]["resolved_snapshot"],
                    "inputs": len(state["inputs"]),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    except (ProjectError, profile_tool.ProfileError, OSError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
