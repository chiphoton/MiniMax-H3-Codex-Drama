#!/usr/bin/env python3
"""Create a valid custom profile bundle ready for evidence-backed distillation."""

from __future__ import annotations

import argparse
import copy
import json
import os
import re
import shutil
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
PRODUCER = SCRIPT_DIR.parent.parent / "minimax-h3-drama-producer"
sys.path.insert(0, str(PRODUCER / "scripts"))
import profile_tool  # noqa: E402


BASE_PROFILE = PRODUCER / "references" / "profiles" / "base-video" / "profile.yaml"


def valid_slug(value: str) -> str:
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", value):
        raise RuntimeError("slug must contain lowercase letters, digits, and single hyphens")
    if len(value) > 64:
        raise RuntimeError("slug must be 64 characters or fewer")
    return value


def write_text(path: Path, text: str) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(text.rstrip() + "\n", encoding="utf-8")
    os.replace(temporary, path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--slug", required=True)
    parser.add_argument("--display-name", required=True)
    parser.add_argument("--summary", required=True)
    parser.add_argument("--version", default="0.1.0")
    parser.add_argument("--evidence", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    staging: Path | None = None
    try:
        slug = valid_slug(args.slug)
        output_root = args.output_dir.expanduser().resolve()
        target = output_root / slug
        if target.exists():
            raise RuntimeError(f"profile bundle already exists: {target}")

        evidence: Path | None = None
        if args.evidence:
            evidence = args.evidence.expanduser().resolve()
            if not evidence.is_file():
                raise RuntimeError(f"evidence file does not exist: {evidence}")
            evidence_data = profile_tool.load_data(evidence)
            if not isinstance(evidence_data.get("sources"), list):
                raise RuntimeError("evidence file must contain a sources array")

        output_root.mkdir(parents=True, exist_ok=True)
        staging = output_root / f".{slug}.scaffolding-{os.getpid()}"
        if staging.exists():
            raise RuntimeError(f"staging directory already exists: {staging}")
        staging.mkdir()

        profile = copy.deepcopy(profile_tool.load_data(BASE_PROFILE))
        profile.update(
            {
                "id": slug,
                "display_name": args.display_name,
                "version": args.version,
                "kind": "custom",
                "inherits": "base-video",
                "summary": args.summary,
            }
        )
        profile["selection"] = {
            "viewer_outcomes": ["to be distilled from the supplied evidence"],
            "platforms": ["to be distilled from the supplied evidence"],
            "signals": [slug],
            "exclusions": ["source-specific identity", "exact dialogue", "brand marks", "music melody"],
        }
        errors = profile_tool.validate_data(profile, profile_tool.load_data(profile_tool.DEFAULT_SCHEMA))
        if errors:
            raise RuntimeError("generated scaffold is invalid: " + "; ".join(errors))
        profile_tool.dump_data(staging / "profile.yaml", profile)

        write_text(
            staging / "storytelling.md",
            "# Storytelling\n\nReplace this scaffold with evidence-backed viewer outcome, beat topology, pacing, applicability, and exclusions. Preserve user-authored content authority.",
        )
        write_text(
            staging / "shot-patterns.md",
            "# Shot patterns\n\nReplace this scaffold with evidence-backed duration ranges, framing, camera, lighting, transition, end-state, and reference-role patterns.",
        )
        write_text(
            staging / "audio-and-captions.md",
            "# Audio and captions\n\nReplace this scaffold with evidence-backed voice, native sound, effects, music, silence, caption layout, emphasis, and safe-area behavior.",
        )
        write_text(
            staging / "qc-rules.md",
            "# QC rules\n\nReplace this scaffold with format checks, content hard gates, visual continuity checks, numeric tolerances, and allowed soft warnings.",
        )

        if evidence:
            shutil.copy2(evidence, staging / "evidence.json")
        else:
            write_text(
                staging / "evidence.json",
                json.dumps(
                    {
                        "schema_version": "1.0",
                        "sources": [],
                        "inferred_rules": [],
                        "variants": [],
                        "excluded_source_specific_content": [],
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
            )

        os.replace(staging, target)
        staging = None
        files = [str(path) for path in sorted(target.iterdir()) if path.is_file()]
        print(json.dumps({"ok": True, "profile_dir": str(target), "files": files}, ensure_ascii=False, indent=2))
        return 0
    except (OSError, RuntimeError, profile_tool.ProfileError) as exc:
        if staging is not None and staging.exists():
            shutil.rmtree(staging)
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
