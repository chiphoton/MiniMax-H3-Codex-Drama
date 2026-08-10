#!/usr/bin/env python3
"""Inventory, diff, and update the Codex skills shipped by this plugin."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = PROJECT_ROOT / "skills"
IGNORED_NAMES = {".DS_Store", "__pycache__"}


class ManagerError(RuntimeError):
    pass


def skill_digest(path: Path) -> tuple[str, int]:
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


def inventory() -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for path in sorted(SKILLS_DIR.iterdir()):
        if not path.is_dir() or not (path / "SKILL.md").is_file():
            continue
        digest, file_count = skill_digest(path)
        result.append({"name": path.name, "files": file_count, "sha256": digest})
    return result


def run_git(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args], cwd=PROJECT_ROOT, check=False, text=True, capture_output=True
    )


def validate_ref(ref: str) -> None:
    completed = run_git(["rev-parse", "--verify", f"{ref}^{{commit}}"])
    if completed.returncode:
        raise ManagerError(f"Unknown Git ref {ref!r}: {completed.stderr.strip()}")


def diff_skills(old_ref: str, new_ref: str) -> list[dict[str, str]]:
    validate_ref(old_ref)
    validate_ref(new_ref)
    completed = run_git(
        ["diff", "--no-ext-diff", "--name-status", old_ref, new_ref, "--", "skills/"]
    )
    if completed.returncode:
        raise ManagerError(completed.stderr.strip() or "git diff failed")
    changes: list[dict[str, str]] = []
    for line in completed.stdout.splitlines():
        fields = line.split("\t")
        if fields:
            changes.append({"status": fields[0], "path": " -> ".join(fields[1:])})
    return changes


def print_inventory(as_json: bool) -> None:
    items = inventory()
    if as_json:
        print(json.dumps(items, indent=2))
        return
    print(f"{'SKILL':36} {'FILES':>5}  SHA256")
    for item in items:
        print(f"{item['name']:36} {item['files']:5d}  {item['sha256']}")


def print_diff(old_ref: str, new_ref: str, as_json: bool) -> None:
    changes = diff_skills(old_ref, new_ref)
    if as_json:
        print(json.dumps({"old_ref": old_ref, "new_ref": new_ref, "changes": changes}, indent=2))
        return
    print(f"Skill changes: {old_ref}..{new_ref}")
    if not changes:
        print("No skill changes.")
        return
    for change in changes:
        print(f"{change['status']:8} {change['path']}")


def update_plugin(marketplace: str, plugin: str, apply: bool) -> None:
    selector = f"{plugin}@{marketplace}"
    commands = [
        ["codex", "plugin", "marketplace", "upgrade", marketplace],
        ["codex", "plugin", "remove", selector],
        ["codex", "plugin", "add", selector],
    ]
    if not apply:
        print("Dry run; no installation changes were made.")
        for command in commands:
            print(" ".join(command))
        print("Re-run with --apply after reviewing the commands.")
        return

    for command in commands:
        print(f"Running: {' '.join(command)}", flush=True)
        completed = subprocess.run(command, check=False)
        if completed.returncode:
            raise ManagerError(
                f"Command failed with exit code {completed.returncode}: {' '.join(command)}"
            )
    print("Plugin updated. Start a new Codex task to load the refreshed skills.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="List project skills and content hashes")
    list_parser.add_argument("--json", action="store_true")

    diff_parser = subparsers.add_parser("diff", help="Compare project skills between Git refs")
    diff_parser.add_argument("old_ref")
    diff_parser.add_argument("new_ref")
    diff_parser.add_argument("--json", action="store_true")

    update_parser = subparsers.add_parser("update", help="Refresh and reinstall the Codex plugin")
    update_parser.add_argument("--marketplace", default="chiphoton")
    update_parser.add_argument("--plugin", default="minimax-h3-drama")
    update_parser.add_argument("--apply", action="store_true", help="Execute displayed commands")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.command == "list":
            print_inventory(args.json)
        elif args.command == "diff":
            print_diff(args.old_ref, args.new_ref, args.json)
        elif args.command == "update":
            update_plugin(args.marketplace, args.plugin, args.apply)
        return 0
    except (OSError, ManagerError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
