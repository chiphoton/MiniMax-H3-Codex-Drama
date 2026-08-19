#!/usr/bin/env python3
"""Patch pinned MiniMax H3 API workflows through declared semantic fields only."""

from __future__ import annotations

import argparse
import copy
import json
import math
import sys
from pathlib import Path
from typing import Any


SKILL_DIR = Path(__file__).resolve().parent.parent
WORKFLOW_DIR = SKILL_DIR / "assets" / "workflows"
MANIFEST_PATH = WORKFLOW_DIR / "manifest.json"
USER_CONFIG = Path.home() / ".config" / "minimax-h3-comfyui" / "comfy-config.json"
PROJECT_CONFIG = Path(".config") / "comfy-config.json"

CONFIG_KEYS = {
    "connection": {"address"},
    "runtime": {"return", "preview", "load_workflow", "turbo", "wait_timeout_minutes"},
    "models": {
        "fl2va",
        "ref2va",
        "text_encoder",
        "video_vae",
        "audio_vae",
        "turbo_lora",
        "qwen_checkpoint",
        "qwen_lora",
    },
    "generation": {
        "width",
        "height",
        "duration_seconds",
        "seed",
        "filename_prefix",
        "sampler",
        "scheduler",
        "steps",
        "denoise",
        "ref_image_size",
    },
}


class ConfigError(ValueError):
    pass


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ConfigError(f"Invalid JSON in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ConfigError(f"Expected a JSON object in {path}")
    return value


def validate_config(config: dict[str, Any], path: Path) -> None:
    unknown_sections = set(config) - set(CONFIG_KEYS)
    if unknown_sections:
        raise ConfigError(f"Unknown section(s) in {path}: {', '.join(sorted(unknown_sections))}")
    for section, value in config.items():
        if not isinstance(value, dict):
            raise ConfigError(f"Expected {section} to be an object in {path}")
        unknown = set(value) - CONFIG_KEYS[section]
        if unknown:
            raise ConfigError(
                f"Unknown {section} field(s) in {path}: {', '.join(sorted(unknown))}"
            )


def merge_nonempty(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(base)
    for key, value in overlay.items():
        if isinstance(value, dict):
            result[key] = merge_nonempty(result.get(key, {}), value)
        elif value is not None and value != "":
            result[key] = value
    return result


def load_config(project_root: Path) -> tuple[dict[str, Any], list[str]]:
    config: dict[str, Any] = {
        "connection": {"address": "localhost:8188"},
        "runtime": {
            "return": True,
            "preview": True,
            "load_workflow": False,
            "turbo": True,
            "wait_timeout_minutes": 60,
        },
        "models": {},
        "generation": {},
    }
    loaded: list[str] = []
    for path in (USER_CONFIG, project_root / PROJECT_CONFIG):
        if path.is_file():
            incoming = read_json(path)
            validate_config(incoming, path)
            config = merge_nonempty(config, incoming)
            loaded.append(str(path))
    validate_values(config)
    return config, loaded


def validate_values(config: dict[str, Any]) -> None:
    runtime = config["runtime"]
    for name in ("return", "preview", "load_workflow", "turbo"):
        if not isinstance(runtime[name], bool):
            raise ConfigError(f"runtime.{name} must be true or false")
    timeout = runtime["wait_timeout_minutes"]
    if not isinstance(timeout, (int, float)) or isinstance(timeout, bool) or not 0 < timeout <= 60:
        raise ConfigError("runtime.wait_timeout_minutes must be greater than 0 and at most 60")

    generation = config["generation"]
    for name in ("width", "height"):
        value = generation.get(name)
        if value is not None and (not isinstance(value, int) or isinstance(value, bool) or value < 32 or value % 32):
            raise ConfigError(f"generation.{name} must be an integer multiple of 32")
    for name in ("seed", "steps"):
        value = generation.get(name)
        if value is not None and (not isinstance(value, int) or isinstance(value, bool) or value < (0 if name == "seed" else 1)):
            raise ConfigError(f"generation.{name} must be a valid non-negative integer")
    duration = generation.get("duration_seconds")
    if duration is not None and (
        not isinstance(duration, (int, float))
        or isinstance(duration, bool)
        or not 0 < duration <= 15
    ):
        raise ConfigError("generation.duration_seconds must be greater than 0 and at most 15")
    denoise = generation.get("denoise")
    if denoise is not None and (
        not isinstance(denoise, (int, float))
        or isinstance(denoise, bool)
        or not 0 <= denoise <= 1
    ):
        raise ConfigError("generation.denoise must be between 0 and 1")
    if generation.get("ref_image_size") not in (None, "", "match", "max"):
        raise ConfigError("generation.ref_image_size must be 'match' or 'max'")


def normalize_address(address: str) -> str:
    value = address.strip().rstrip("/")
    if not value:
        value = "localhost:8188"
    if "://" not in value:
        value = f"http://{value}"
    return value


def effective_runtime(runtime: dict[str, Any]) -> dict[str, Any]:
    result = dict(runtime)
    if not result["load_workflow"]:
        result["preview"] = False
    return result


def duration_to_length(seconds: float) -> int:
    rounded = math.floor(seconds * 24 + 0.5)
    base = max(5, rounded)
    return base + (5 - (base % 17)) % 17


def set_input(workflow: dict[str, Any], location: list[str], value: Any) -> None:
    node_id, input_name = location
    workflow[node_id]["inputs"][input_name] = value


def remove_r2v_template_media(workflow: dict[str, Any]) -> None:
    inputs = workflow["136"]["inputs"]
    for key in list(inputs):
        if key.startswith(("ref_images.", "ref_videos.", "ref_video_audios.", "ref_audios.")):
            del inputs[key]
    for node_id in ("137", "139"):
        workflow.pop(node_id, None)


def add_r2v_media(
    workflow: dict[str, Any],
    images: list[str],
    videos: list[str],
    audios: list[str],
) -> None:
    if not (images or videos or audios):
        return
    if len(images) > 9 or len(videos) > 3 or len(audios) > 3:
        raise ConfigError("R2V accepts at most 9 images, 3 videos, and 3 standalone audio files")
    remove_r2v_template_media(workflow)
    target = workflow["136"]["inputs"]
    next_node = 200
    for index, filename in enumerate(images):
        node_id = str(next_node)
        next_node += 1
        workflow[node_id] = {"class_type": "LoadImage", "inputs": {"image": filename}}
        target[f"ref_images.ref_image_{index}"] = [node_id, 0]
    for index, filename in enumerate(videos):
        load_id = str(next_node)
        parts_id = str(next_node + 1)
        next_node += 2
        workflow[load_id] = {"class_type": "LoadVideo", "inputs": {"file": filename}}
        workflow[parts_id] = {
            "class_type": "GetVideoComponents",
            "inputs": {"video": [load_id, 0]},
        }
        target[f"ref_videos.ref_video_{index}"] = [parts_id, 0]
        target[f"ref_video_audios.ref_video_audio_{index}"] = [parts_id, 1]
    for index, filename in enumerate(audios):
        node_id = str(next_node)
        next_node += 1
        workflow[node_id] = {"class_type": "LoadAudio", "inputs": {"audio": filename}}
        target[f"ref_audios.ref_audio_{index}"] = [node_id, 0]


def apply_media(workflow: dict[str, Any], args: argparse.Namespace) -> None:
    if args.mode == "t2v" and (args.first_frame or args.last_frame):
        raise ConfigError("T2V does not accept first or last frames; select i2v")
    if args.mode == "i2v":
        if args.reference_image or args.reference_video or args.reference_audio:
            raise ConfigError("I2V accepts --first-frame and optional --last-frame only")
        if args.first_frame:
            workflow["114"] = {
                "class_type": "LoadImage",
                "inputs": {"image": args.first_frame},
            }
            workflow["104"]["inputs"]["first_frame"] = ["114", 0]
        if args.last_frame:
            workflow["116"] = {
                "class_type": "LoadImage",
                "inputs": {"image": args.last_frame},
            }
            workflow["104"]["inputs"]["last_frame"] = ["116", 0]
    elif args.mode == "r2v":
        if args.first_frame or args.last_frame:
            raise ConfigError("R2V uses --reference-image, --reference-video, or --reference-audio")
        add_r2v_media(
            workflow,
            args.reference_image,
            args.reference_video,
            args.reference_audio,
        )


def build_workflow(args: argparse.Namespace) -> tuple[dict[str, Any], dict[str, Any]]:
    manifest = read_json(MANIFEST_PATH)
    mode = manifest["modes"][args.mode]
    config, config_files = load_config(args.project_root.resolve())
    explicit_turbo = getattr(args, "turbo", None)
    turbo = explicit_turbo if explicit_turbo is not None else config["runtime"]["turbo"]
    variant_name = "turbo" if turbo else "standard"
    variant = mode["variants"][variant_name]
    workflow = read_json(WORKFLOW_DIR / variant["api"])
    generation = config["generation"]

    prompt = args.prompt
    if args.prompt_file:
        prompt = args.prompt_file.read_text(encoding="utf-8")
    if prompt is not None:
        set_input(workflow, mode["prompt"], prompt)

    width = args.width if args.width is not None else generation.get("width")
    height = args.height if args.height is not None else generation.get("height")
    if (width is None) != (height is None):
        raise ConfigError("width and height must be supplied together")
    if width is not None:
        for name, value in (("width", width), ("height", height)):
            if value < 32 or value % 32:
                raise ConfigError(f"{name} must be a multiple of 32")
        node_id, width_name, height_name = mode["size"]
        workflow[node_id]["inputs"][width_name] = width
        workflow[node_id]["inputs"][height_name] = height

    duration = args.duration if args.duration is not None else generation.get("duration_seconds")
    if duration is not None:
        if not 0 < duration <= 15:
            raise ConfigError("duration must be greater than 0 and at most 15 seconds")
        set_input(workflow, mode["length"], duration_to_length(duration))

    seed = args.seed if args.seed is not None else generation.get("seed")
    if seed is not None:
        if seed < 0:
            raise ConfigError("seed must be non-negative")
        set_input(workflow, mode["seed"], seed)

    filename_prefix = args.filename_prefix or generation.get("filename_prefix")
    if filename_prefix:
        set_input(workflow, mode["output"], filename_prefix)

    models = dict(config["models"])
    model_fields = {**mode["models"], **variant.get("models", {})}
    for model_name, location in model_fields.items():
        explicit = getattr(args, model_name, None)
        selected = explicit or models.get(model_name)
        if selected:
            set_input(workflow, location, selected)

    if turbo:
        sampler = args.sampler if args.sampler is not None else generation.get("sampler")
        if sampler not in (None, ""):
            raise ConfigError("Turbo uses MiniMaxH3TurboSampler; set turbo=false to override sampler")
        scheduler = args.scheduler if args.scheduler is not None else generation.get("scheduler")
        if scheduler not in (None, "", "simple"):
            raise ConfigError("Turbo requires the 'simple' scheduler")
        steps = args.steps if args.steps is not None else generation.get("steps")
        minimum, maximum = manifest["turbo_source"]["recommended_steps"]
        if steps is not None and not minimum <= steps <= maximum:
            raise ConfigError(f"Turbo steps must be between {minimum} and {maximum}")

    sampling = variant["sampling"]
    for setting in ("sampler", "scheduler", "steps", "denoise", "ref_image_size"):
        if setting not in sampling:
            continue
        explicit = getattr(args, setting, None)
        selected = explicit if explicit is not None else generation.get(setting)
        if selected not in (None, ""):
            set_input(workflow, sampling[setting], selected)

    apply_media(workflow, args)
    metadata = {
        "mode": args.mode,
        "variant": variant_name,
        "turbo": turbo,
        "workflow": str(WORKFLOW_DIR / variant["api"]),
        "ui_workflow": str(WORKFLOW_DIR / variant["ui"]),
        "config_files": config_files,
        "address": normalize_address(config["connection"]["address"]),
        "runtime": effective_runtime({**config["runtime"], "turbo": turbo}),
    }
    return workflow, metadata


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--mode", required=True, choices=("t2v", "i2v", "r2v"))
    prompt_group = result.add_mutually_exclusive_group()
    prompt_group.add_argument("--prompt")
    prompt_group.add_argument("--prompt-file", type=Path)
    result.add_argument("--project-root", type=Path, default=Path.cwd())
    result.add_argument("--output", type=Path, required=True)
    result.add_argument("--turbo", action=argparse.BooleanOptionalAction, default=None)
    result.add_argument("--width", type=int)
    result.add_argument("--height", type=int)
    result.add_argument("--duration", type=float)
    result.add_argument("--seed", type=int)
    result.add_argument("--filename-prefix")
    result.add_argument("--fl2va")
    result.add_argument("--ref2va")
    result.add_argument("--text-encoder", dest="text_encoder")
    result.add_argument("--video-vae", dest="video_vae")
    result.add_argument("--audio-vae", dest="audio_vae")
    result.add_argument("--turbo-lora", dest="turbo_lora")
    result.add_argument("--sampler")
    result.add_argument("--scheduler")
    result.add_argument("--steps", type=int)
    result.add_argument("--denoise", type=float)
    result.add_argument("--ref-image-size", dest="ref_image_size", choices=("match", "max"))
    result.add_argument("--first-frame")
    result.add_argument("--last-frame")
    result.add_argument("--reference-image", action="append", default=[])
    result.add_argument("--reference-video", action="append", default=[])
    result.add_argument("--reference-audio", action="append", default=[])
    return result


def main() -> int:
    args = parser().parse_args()
    try:
        workflow, metadata = build_workflow(args)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(workflow, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(json.dumps(metadata, indent=2))
        return 0
    except (ConfigError, KeyError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
