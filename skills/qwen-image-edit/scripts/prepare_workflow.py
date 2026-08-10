#!/usr/bin/env python3
"""Prepare the pinned Qwen Image Edit UI and API workflows deterministically."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any


SKILL_DIR = Path(__file__).resolve().parent.parent
WORKFLOW_DIR = SKILL_DIR / "assets" / "workflows"
MANIFEST_PATH = WORKFLOW_DIR / "manifest.json"
USER_CONFIG = Path.home() / ".config" / "minimax-h3-comfyui" / "comfy-config.json"
PROJECT_CONFIG = Path(".config") / "comfy-config.json"


class WorkflowError(ValueError):
    pass


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise WorkflowError(f"Missing file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise WorkflowError(f"Invalid JSON in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise WorkflowError(f"Expected a JSON object in {path}")
    return value


def merge_nonempty(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(base)
    for key, value in overlay.items():
        if isinstance(value, dict):
            result[key] = merge_nonempty(result.get(key, {}), value)
        elif value is not None and value != "":
            result[key] = value
    return result


def load_config(project_root: Path, defaults: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    config: dict[str, Any] = {
        "connection": {"address": "localhost:8188"},
        "runtime": {
            "return": True,
            "preview": True,
            "load_workflow": False,
            "wait_timeout_minutes": 60,
        },
        "models": {
            "qwen_checkpoint": defaults["checkpoint"],
            "qwen_lora": defaults["lora"],
        },
        "generation": {},
    }
    loaded: list[str] = []
    for path in (USER_CONFIG, project_root / PROJECT_CONFIG):
        if path.is_file():
            incoming = read_json(path)
            config = merge_nonempty(config, incoming)
            loaded.append(str(path))
    validate_runtime(config["runtime"])
    return config, loaded


def validate_runtime(runtime: dict[str, Any]) -> None:
    for name in ("return", "preview", "load_workflow"):
        if not isinstance(runtime.get(name), bool):
            raise WorkflowError(f"runtime.{name} must be true or false")
    timeout = runtime.get("wait_timeout_minutes")
    if not isinstance(timeout, (int, float)) or isinstance(timeout, bool) or not 0 < timeout <= 60:
        raise WorkflowError("runtime.wait_timeout_minutes must be greater than 0 and at most 60")


def effective_runtime(runtime: dict[str, Any]) -> dict[str, Any]:
    result = dict(runtime)
    if not result["load_workflow"]:
        result["preview"] = False
    return result


def find_ui_node(workflow: dict[str, Any], node_id: int, expected_type: str) -> dict[str, Any]:
    for node in workflow.get("nodes", []):
        if node.get("id") == node_id:
            if node.get("type") != expected_type:
                raise WorkflowError(
                    f"UI node {node_id} changed type: expected {expected_type}, got {node.get('type')}"
                )
            return node
    raise WorkflowError(f"Missing UI node {node_id} ({expected_type})")


def remove_second_ui_image(workflow: dict[str, Any], node_id: int, link_id: int) -> None:
    workflow["nodes"] = [node for node in workflow["nodes"] if node.get("id") != node_id]
    workflow["links"] = [link for link in workflow["links"] if link[0] != link_id]
    prompt_node = find_ui_node(
        workflow, 1, "TextEncodeQwenImageEditPlusAdvance_lrzjason"
    )
    for input_spec in prompt_node.get("inputs", []):
        if input_spec.get("name") == "vl_resize_image2":
            input_spec.pop("link", None)


def patch_ui(
    workflow: dict[str, Any],
    manifest: dict[str, Any],
    images: list[str],
    prompt: str,
    checkpoint: str,
    lora: str,
    seed: int | None,
) -> dict[str, Any]:
    ids = manifest["ui_nodes"]
    prompt_node = find_ui_node(
        workflow, ids["prompt"], "TextEncodeQwenImageEditPlusAdvance_lrzjason"
    )
    image_1 = find_ui_node(workflow, ids["image_1"], "LoadImage")
    checkpoint_node = find_ui_node(workflow, ids["checkpoint"], "CheckpointLoaderSimple")
    lora_node = find_ui_node(workflow, ids["lora"], "LoraLoaderModelOnly")
    sampler_node = find_ui_node(workflow, ids["sampler"], "KSampler")

    prompt_node["widgets_values"][0] = prompt
    image_1["widgets_values"][0] = images[0]
    checkpoint_node["widgets_values"][0] = checkpoint
    lora_node["widgets_values"][0] = lora
    if seed is not None:
        sampler_node["widgets_values"][0] = seed
        sampler_node["widgets_values"][1] = "fixed"

    if len(images) == 2:
        image_2 = find_ui_node(workflow, ids["image_2"], "LoadImage")
        image_2["widgets_values"][0] = images[1]
        image_2["mode"] = 0
    else:
        remove_second_ui_image(workflow, ids["image_2"], 4)
    return workflow


def patch_api(
    workflow: dict[str, Any],
    manifest: dict[str, Any],
    images: list[str],
    prompt: str,
    checkpoint: str,
    lora: str,
    seed: int | None,
) -> dict[str, Any]:
    ids = manifest["api_nodes"]
    workflow[ids["prompt"]]["inputs"]["prompt"] = prompt
    workflow[ids["image_1"]]["inputs"]["image"] = images[0]
    workflow[ids["checkpoint"]]["inputs"]["ckpt_name"] = checkpoint
    workflow[ids["lora"]]["inputs"]["lora_name"] = lora
    if seed is not None:
        workflow[ids["sampler"]]["inputs"]["seed"] = seed

    if len(images) == 2:
        workflow[ids["image_2"]]["inputs"]["image"] = images[1]
    else:
        workflow.pop(ids["image_2"], None)
        workflow[ids["prompt"]]["inputs"].pop("vl_resize_image2", None)
    return workflow


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--image", action="append", required=True, help="Uploaded ComfyUI filename; repeat once for a second image")
    prompt_group = parser.add_mutually_exclusive_group(required=True)
    prompt_group.add_argument("--prompt")
    prompt_group.add_argument("--prompt-file", type=Path)
    parser.add_argument("--checkpoint")
    parser.add_argument("--lora")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--output-api", type=Path)
    parser.add_argument("--output-ui", type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        if not 1 <= len(args.image) <= 2:
            raise WorkflowError("Supply exactly one or two --image values")
        if args.seed is not None and args.seed < 0:
            raise WorkflowError("seed must be non-negative")
        if args.output_api is None and args.output_ui is None:
            raise WorkflowError("Supply --output-api, --output-ui, or both")

        manifest = read_json(MANIFEST_PATH)
        config, config_files = load_config(args.project_root.resolve(), manifest["defaults"])
        prompt = args.prompt
        if args.prompt_file:
            prompt = args.prompt_file.read_text(encoding="utf-8")
        if not prompt or not prompt.strip():
            raise WorkflowError("prompt must not be empty")

        checkpoint = args.checkpoint or config["models"].get("qwen_checkpoint")
        lora = args.lora or config["models"].get("qwen_lora")
        seed = args.seed if args.seed is not None else config["generation"].get("seed")
        if not isinstance(checkpoint, str) or not checkpoint:
            raise WorkflowError("A Qwen checkpoint filename is required")
        if not isinstance(lora, str) or not lora:
            raise WorkflowError("A Qwen LoRA filename is required")
        if seed is not None and (not isinstance(seed, int) or isinstance(seed, bool) or seed < 0):
            raise WorkflowError("generation.seed must be a non-negative integer or null")

        if args.output_api:
            api = read_json(WORKFLOW_DIR / manifest["template"]["api"])
            write_json(
                args.output_api,
                patch_api(api, manifest, args.image, prompt, checkpoint, lora, seed),
            )
        if args.output_ui:
            ui = read_json(WORKFLOW_DIR / manifest["template"]["ui"])
            write_json(
                args.output_ui,
                patch_ui(ui, manifest, args.image, prompt, checkpoint, lora, seed),
            )

        print(
            json.dumps(
                {
                    "images": args.image,
                    "checkpoint": checkpoint,
                    "lora": lora,
                    "seed": seed,
                    "runtime": effective_runtime(config["runtime"]),
                    "config_files": config_files,
                    "output_api": str(args.output_api) if args.output_api else None,
                    "output_ui": str(args.output_ui) if args.output_ui else None,
                },
                indent=2,
            )
        )
        return 0
    except (OSError, WorkflowError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
