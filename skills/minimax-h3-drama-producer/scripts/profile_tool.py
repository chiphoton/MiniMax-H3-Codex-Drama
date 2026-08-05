#!/usr/bin/env python3
"""Validate and resolve declarative MiniMax-H3 Drama profiles.

The bundled profiles are JSON-compatible YAML, so the standard library is enough.
Conventional YAML is accepted when PyYAML is already installed; this script never
installs it.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_SCHEMA = SCRIPT_DIR.parent / "references" / "profile.schema.json"
FORBIDDEN_KEYS = {
    "command",
    "commands",
    "exec",
    "executable",
    "install",
    "installer",
    "network_request",
    "script",
    "scripts",
    "shell",
    "url_to_execute",
}


class ProfileError(Exception):
    """Raised for a malformed, unsafe, or unresolvable profile."""


def load_data(path: Path) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ProfileError(f"cannot read {path}: {exc}") from exc

    try:
        data = json.loads(text)
    except json.JSONDecodeError as json_exc:
        try:
            import yaml  # type: ignore
        except ImportError as exc:
            raise ProfileError(
                f"{path} is not JSON-compatible YAML and PyYAML is unavailable: {json_exc}"
            ) from exc
        try:
            data = yaml.safe_load(text)
        except Exception as exc:  # PyYAML exposes several parser exception types.
            raise ProfileError(f"cannot parse {path}: {exc}") from exc

    if not isinstance(data, dict):
        raise ProfileError(f"{path} must contain a top-level mapping")
    return data


def dump_data(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    os.replace(temporary, path)


def _type_matches(value: Any, expected: str) -> bool:
    if expected == "null":
        return value is None
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    return True


def _validate_node(
    value: Any,
    schema: dict[str, Any],
    path: str,
    errors: list[str],
    *,
    require_required: bool,
) -> None:
    if "const" in schema and value != schema["const"]:
        errors.append(f"{path}: must equal {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: must be one of {schema['enum']!r}")

    expected = schema.get("type")
    if expected is not None:
        expected_types = expected if isinstance(expected, list) else [expected]
        if not any(_type_matches(value, item) for item in expected_types):
            errors.append(f"{path}: expected {expected_types}, got {type(value).__name__}")
            return

    if isinstance(value, dict):
        properties = schema.get("properties", {})
        if require_required:
            for key in schema.get("required", []):
                if key not in value:
                    errors.append(f"{path}: missing required key {key!r}")
        if schema.get("additionalProperties") is False:
            for key in value:
                if key not in properties:
                    errors.append(f"{path}: unknown key {key!r}")
        for key, child in value.items():
            if key in properties:
                _validate_node(
                    child,
                    properties[key],
                    f"{path}.{key}",
                    errors,
                    require_required=require_required,
                )

    if isinstance(value, list):
        if "minItems" in schema and len(value) < schema["minItems"]:
            errors.append(f"{path}: requires at least {schema['minItems']} items")
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            errors.append(f"{path}: allows at most {schema['maxItems']} items")
        if schema.get("uniqueItems"):
            encoded = [json.dumps(item, sort_keys=True, ensure_ascii=False) for item in value]
            if len(encoded) != len(set(encoded)):
                errors.append(f"{path}: items must be unique")
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, child in enumerate(value):
                _validate_node(
                    child,
                    item_schema,
                    f"{path}[{index}]",
                    errors,
                    require_required=require_required,
                )

    if isinstance(value, str):
        if "minLength" in schema and len(value) < schema["minLength"]:
            errors.append(f"{path}: is shorter than {schema['minLength']} characters")
        if "maxLength" in schema and len(value) > schema["maxLength"]:
            errors.append(f"{path}: is longer than {schema['maxLength']} characters")
        pattern = schema.get("pattern")
        if pattern and re.fullmatch(pattern, value) is None:
            errors.append(f"{path}: does not match {pattern!r}")

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            errors.append(f"{path}: must be >= {schema['minimum']}")
        if "maximum" in schema and value > schema["maximum"]:
            errors.append(f"{path}: must be <= {schema['maximum']}")


def _check_forbidden_keys(value: Any, path: str, errors: list[str]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key.lower() in FORBIDDEN_KEYS:
                errors.append(f"{path}: executable key {key!r} is forbidden")
            _check_forbidden_keys(child, f"{path}.{key}", errors)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _check_forbidden_keys(child, f"{path}[{index}]", errors)


def validate_data(
    data: dict[str, Any], schema: dict[str, Any], *, partial: bool = False
) -> list[str]:
    errors: list[str] = []
    _check_forbidden_keys(data, "$", errors)
    _validate_node(data, schema, "$", errors, require_required=not partial)

    if not partial:
        duration = data.get("format", {}).get("duration_s", {})
        if all(key in duration for key in ("min", "target", "max")):
            if not duration["min"] <= duration["target"] <= duration["max"]:
                errors.append("$.format.duration_s: expected min <= target <= max")

        shot_duration = data.get("shots", {}).get("default_duration_s", {})
        if all(key in shot_duration for key in ("min", "max")):
            if shot_duration["min"] > shot_duration["max"]:
                errors.append("$.shots.default_duration_s: expected min <= max")

        kind = data.get("kind")
        inherits = data.get("inherits")
        if kind == "base" and inherits is not None:
            errors.append("$.inherits: a base profile must inherit null")
        if kind in {"primary", "custom"} and not isinstance(inherits, str):
            errors.append("$.inherits: primary and custom profiles must name a base")

        beats = data.get("story", {}).get("required_beats", [])
        for beat in beats:
            if isinstance(beat, dict) and beat.get("start_pct", 0) > beat.get("end_pct", 0):
                errors.append(f"$.story.required_beats.{beat.get('id', '?')}: start exceeds end")

    return sorted(set(errors))


def deep_merge(base: Any, overlay: Any) -> Any:
    if isinstance(base, dict) and isinstance(overlay, dict):
        merged = dict(base)
        for key, value in overlay.items():
            merged[key] = deep_merge(merged[key], value) if key in merged else value
        return merged
    return overlay


def command_validate(args: argparse.Namespace) -> int:
    schema = load_data(args.schema)
    profile = load_data(args.profile)
    errors = validate_data(profile, schema)
    result = {"valid": not errors, "profile": str(args.profile), "errors": errors}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


def command_resolve(args: argparse.Namespace) -> int:
    schema = load_data(args.schema)
    base = load_data(args.base)
    profile = load_data(args.profile)
    errors = [f"base: {item}" for item in validate_data(base, schema)]
    errors.extend(f"profile: {item}" for item in validate_data(profile, schema))

    resolved = deep_merge(base, profile)
    if args.override:
        override = load_data(args.override)
        errors.extend(
            f"override: {item}" for item in validate_data(override, schema, partial=True)
        )
        resolved = deep_merge(resolved, override)

    errors.extend(f"resolved: {item}" for item in validate_data(resolved, schema))
    errors = sorted(set(errors))
    if errors:
        print(json.dumps({"valid": False, "errors": errors}, ensure_ascii=False, indent=2))
        return 1

    dump_data(args.output, resolved)
    print(
        json.dumps(
            {
                "valid": True,
                "base": str(args.base),
                "profile": str(args.profile),
                "override": str(args.override) if args.override else None,
                "output": str(args.output),
                "resolved_id": resolved.get("id"),
                "resolved_version": resolved.get("version"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.set_defaults(func=None)
    subparsers = parser.add_subparsers(dest="command")

    validate_parser = subparsers.add_parser("validate", help="validate one complete profile")
    validate_parser.add_argument("profile", type=Path)
    validate_parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    validate_parser.set_defaults(func=command_validate)

    resolve_parser = subparsers.add_parser("resolve", help="merge base, profile, and override")
    resolve_parser.add_argument("--base", type=Path, required=True)
    resolve_parser.add_argument("--profile", type=Path, required=True)
    resolve_parser.add_argument("--override", type=Path)
    resolve_parser.add_argument("--output", type=Path, required=True)
    resolve_parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    resolve_parser.set_defaults(func=command_resolve)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.func is None:
        parser.print_help(sys.stderr)
        return 2
    try:
        return args.func(args)
    except ProfileError as exc:
        print(json.dumps({"valid": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
