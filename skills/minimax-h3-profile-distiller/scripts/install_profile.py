#!/usr/bin/env python3
"""Install a validated custom profile into a project or personal registry."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
PRODUCER = SCRIPT_DIR.parent.parent / "minimax-h3-drama-producer"
sys.path.insert(0, str(PRODUCER / "scripts"))
import profile_tool  # noqa: E402


REQUIRED_FILES = {
    "profile.yaml",
    "storytelling.md",
    "shot-patterns.md",
    "audio-and-captions.md",
    "qc-rules.md",
    "evidence.json",
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("profile_dir", type=Path)
    parser.add_argument("--scope", choices=["project", "personal"], required=True)
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    args = parser.parse_args()

    temporary: Path | None = None
    try:
        source = args.profile_dir.expanduser().resolve()
        if not source.is_dir():
            raise RuntimeError(f"profile directory does not exist: {source}")
        missing = sorted(name for name in REQUIRED_FILES if not (source / name).is_file())
        if missing:
            raise RuntimeError("profile bundle is missing: " + ", ".join(missing))
        unexpected = sorted(item.name for item in source.iterdir() if item.name not in REQUIRED_FILES)
        if unexpected:
            raise RuntimeError("profile bundle contains unexpected entries: " + ", ".join(unexpected))
        if any(item.is_symlink() or not item.is_file() for item in source.iterdir()):
            raise RuntimeError("profile bundle entries must be regular files, not links or directories")
        evidence = profile_tool.load_data(source / "evidence.json")
        if not isinstance(evidence.get("sources"), list):
            raise RuntimeError("profile evidence must contain a sources array")
        profile = profile_tool.load_data(source / "profile.yaml")
        errors = profile_tool.validate_data(profile, profile_tool.load_data(profile_tool.DEFAULT_SCHEMA))
        if errors:
            raise RuntimeError("profile validation failed: " + "; ".join(errors))
        if profile.get("kind") != "custom":
            raise RuntimeError("only custom profiles may be installed into user registries")
        slug = str(profile["id"])

        if args.scope == "project":
            root = args.workspace.expanduser().resolve() / ".minimax-h3-drama" / "profiles"
        else:
            root = Path.home() / ".config" / "minimax-h3-drama" / "profiles"
        root.mkdir(parents=True, exist_ok=True)
        target = root / slug
        if target.exists():
            raise RuntimeError(
                f"profile {slug!r} is already installed at {target}; create a new version or remove it explicitly"
            )

        temporary = root / f".{slug}.installing-{os.getpid()}"
        if temporary.exists():
            raise RuntimeError(f"temporary install path already exists: {temporary}")
        shutil.copytree(source, temporary)
        if target.exists():
            raise RuntimeError(f"profile install target appeared during copy: {target}")
        os.replace(temporary, target)
        print(
            json.dumps(
                {
                    "ok": True,
                    "scope": args.scope,
                    "profile_id": slug,
                    "version": profile.get("version"),
                    "installed_at": str(target),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    except (OSError, RuntimeError, profile_tool.ProfileError) as exc:
        if temporary and temporary.exists():
            shutil.rmtree(temporary, ignore_errors=True)
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
