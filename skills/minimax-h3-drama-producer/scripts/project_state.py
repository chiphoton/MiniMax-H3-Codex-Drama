#!/usr/bin/env python3
"""Inspect and safely update a MiniMax-H3 Drama project state ledger."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import init_project


VALID_STATUSES = {"pending", "in_progress", "blocked", "failed", "completed"}
VALID_JOB_STATUSES = {"prepared", "queued", "running", "completed", "failed"}


def state_path(value: Path) -> Path:
    path = value.expanduser().resolve()
    return path / "project.yaml" if path.is_dir() else path


def load(value: Path) -> tuple[Path, dict[str, Any]]:
    path = state_path(value)
    return path, init_project.load_state(path)


def save(path: Path, state: dict[str, Any], event: str, detail: dict[str, Any]) -> None:
    now = init_project.utc_now()
    state["project"]["updated_at"] = now
    state.setdefault("history", []).append({"at": now, "event": event, "detail": detail})
    init_project.atomic_write(path, state)


def command_status(args: argparse.Namespace) -> int:
    path, state = load(args.project)
    print(
        json.dumps(
            {
                "state": str(path),
                "project": state["project"],
                "profile": state.get("profile", {}),
                "stages": state.get("stages", {}),
                "inputs": len(state.get("inputs", [])),
                "shots": len(state.get("shots", [])),
                "jobs": len(state.get("jobs", [])),
                "artifacts": len(state.get("artifacts", [])),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def command_set_stage(args: argparse.Namespace) -> int:
    path, state = load(args.project)
    if args.status not in VALID_STATUSES:
        raise RuntimeError(f"invalid stage status {args.status!r}")
    if args.stage not in state.get("stages", {}):
        raise RuntimeError(f"unknown stage {args.stage!r}")
    now = init_project.utc_now()
    state["stages"][args.stage] = {"status": args.status, "updated_at": now, "note": args.note}
    state["project"]["status"] = (
        "blocked"
        if any(item.get("status") == "blocked" for item in state["stages"].values())
        else "active"
    )
    save(path, state, "stage-updated", {"stage": args.stage, "status": args.status, "note": args.note})
    print(json.dumps({"ok": True, "stage": args.stage, "status": args.status}, indent=2))
    return 0


def command_record_job(args: argparse.Namespace) -> int:
    path, state = load(args.project)
    if args.status not in VALID_JOB_STATUSES:
        raise RuntimeError(f"invalid job status {args.status!r}")
    jobs = state.setdefault("jobs", [])
    existing = next((item for item in jobs if item.get("prompt_id") == args.prompt_id), None)
    payload = {
        "shot": args.shot,
        "prompt_id": args.prompt_id,
        "route": args.route,
        "workflow": args.workflow,
        "status": args.status,
        "output": args.output,
        "error": args.error,
        "updated_at": init_project.utc_now(),
    }
    if existing:
        if existing.get("shot") != args.shot:
            raise RuntimeError("the prompt ID is already assigned to another shot")
        existing.update(payload)
    else:
        jobs.append(payload)
    save(path, state, "job-recorded", {"shot": args.shot, "prompt_id": args.prompt_id, "status": args.status})
    print(json.dumps({"ok": True, **payload}, ensure_ascii=False, indent=2))
    return 0


def command_record_artifact(args: argparse.Namespace) -> int:
    path, state = load(args.project)
    artifacts = state.setdefault("artifacts", [])
    if any(item.get("id") == args.artifact_id for item in artifacts):
        raise RuntimeError(f"artifact ID {args.artifact_id!r} already exists; use a new versioned ID")
    payload = {
        "id": args.artifact_id,
        "role": args.role,
        "path": args.path,
        "version": args.version,
        "sources": args.source,
        "created_at": init_project.utc_now(),
    }
    artifacts.append(payload)
    save(path, state, "artifact-recorded", {"id": args.artifact_id, "role": args.role})
    print(json.dumps({"ok": True, "artifact": payload}, ensure_ascii=False, indent=2))
    return 0


def command_select_take(args: argparse.Namespace) -> int:
    path, state = load(args.project)
    shots = state.setdefault("shots", [])
    shot = next((item for item in shots if item.get("id") == args.shot), None)
    if shot is None:
        shot = {"id": args.shot, "takes": [], "selected_take": None}
        shots.append(shot)
    take = {
        "path": args.take_path,
        "prompt_id": args.prompt_id,
        "score": args.score,
        "selected_at": init_project.utc_now(),
    }
    if not any(
        item.get("path") == args.take_path and item.get("prompt_id") == args.prompt_id
        for item in shot.setdefault("takes", [])
    ):
        shot["takes"].append(take)
    shot["selected_take"] = take
    save(path, state, "take-selected", {"shot": args.shot, "path": args.take_path, "prompt_id": args.prompt_id})
    print(json.dumps({"ok": True, "shot": args.shot, "selected_take": take}, ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command")

    status_parser = subparsers.add_parser("status")
    status_parser.add_argument("project", type=Path)
    status_parser.set_defaults(func=command_status)

    stage_parser = subparsers.add_parser("set-stage")
    stage_parser.add_argument("project", type=Path)
    stage_parser.add_argument("stage")
    stage_parser.add_argument("status", choices=sorted(VALID_STATUSES))
    stage_parser.add_argument("--note")
    stage_parser.set_defaults(func=command_set_stage)

    job_parser = subparsers.add_parser("record-job")
    job_parser.add_argument("project", type=Path)
    job_parser.add_argument("--shot", required=True)
    job_parser.add_argument("--prompt-id", required=True)
    job_parser.add_argument("--route", required=True)
    job_parser.add_argument("--workflow")
    job_parser.add_argument("--status", choices=sorted(VALID_JOB_STATUSES), required=True)
    job_parser.add_argument("--output")
    job_parser.add_argument("--error")
    job_parser.set_defaults(func=command_record_job)

    artifact_parser = subparsers.add_parser("record-artifact")
    artifact_parser.add_argument("project", type=Path)
    artifact_parser.add_argument("--artifact-id", required=True)
    artifact_parser.add_argument("--role", required=True)
    artifact_parser.add_argument("--path", required=True)
    artifact_parser.add_argument("--version", default="1")
    artifact_parser.add_argument("--source", action="append", default=[])
    artifact_parser.set_defaults(func=command_record_artifact)

    take_parser = subparsers.add_parser("select-take")
    take_parser.add_argument("project", type=Path)
    take_parser.add_argument("--shot", required=True)
    take_parser.add_argument("--take-path", required=True)
    take_parser.add_argument("--prompt-id")
    take_parser.add_argument("--score", type=float)
    take_parser.set_defaults(func=command_select_take)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help()
        return 2
    try:
        return args.func(args)
    except (OSError, RuntimeError, init_project.ProjectError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
