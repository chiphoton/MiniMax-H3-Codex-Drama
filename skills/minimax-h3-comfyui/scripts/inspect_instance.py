#!/usr/bin/env python3
"""Probe a configured ComfyUI instance and resolve compatible MiniMax H3 models."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from prepare_workflow import ConfigError, load_config, normalize_address


PINNED = {
    "fl2va": "minimax_h3_fl2va_pruned_int8_convrot.safetensors",
    "ref2va": "minimax_h3_ref2va_pruned_int8_convrot.safetensors",
    "text_encoder": "qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors",
    "video_vae": "minimax_h3_video_vae_fp16.safetensors",
    "audio_vae": "minimax_h3_audio_vae_fp32.safetensors",
    "turbo_lora": "minimax_h3_turbo_v4_step600_ema.safetensors",
}

MODEL_NODE = {
    "fl2va": ("UNETLoader", "unet_name"),
    "ref2va": ("UNETLoader", "unet_name"),
    "text_encoder": ("CLIPLoader", "clip_name"),
    "video_vae": ("VAELoader", "vae_name"),
    "audio_vae": ("VAELoader", "vae_name"),
    "turbo_lora": ("MiniMaxH3TurboLoRA", "lora_name"),
}

TURBO_NODES = ("MiniMaxH3TurboLoRA", "MiniMaxH3TurboSampler")


def get_json(address: str, route: str) -> dict[str, Any]:
    request = urllib.request.Request(f"{address}{route}", headers={"Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=4) as response:
        value = json.load(response)
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object from {route}")
    return value


def choices(object_info: dict[str, Any], node: str, field: str) -> list[str]:
    value = object_info[node]["input"]["required"][field][0]
    return [str(item) for item in value] if isinstance(value, list) else []


def compatible(kind: str, name: str) -> bool:
    folded = name.lower()
    terms = {
        "fl2va": ("minimax_h3", "fl2va"),
        "ref2va": ("minimax_h3", "ref2va"),
        "text_encoder": ("minimax_h3", "qwen3vl"),
        "video_vae": ("minimax_h3", "video", "vae"),
        "audio_vae": ("minimax_h3", "audio", "vae"),
        "turbo_lora": ("minimax", "h3", "turbo"),
    }[kind]
    return all(term in folded for term in terms)


def select(kind: str, available: list[str], preferred: str | None) -> dict[str, Any]:
    if preferred:
        if preferred in available:
            return {"selected": preferred, "reason": "configured", "candidates": [preferred]}
        return {
            "error": f"Configured {kind} model is not installed: {preferred}",
            "candidates": [name for name in available if compatible(kind, name)],
        }
    if PINNED[kind] in available:
        return {"selected": PINNED[kind], "reason": "pinned-default", "candidates": [PINNED[kind]]}
    candidates = [name for name in available if compatible(kind, name)]
    if len(candidates) == 1:
        return {"selected": candidates[0], "reason": "single-compatible", "candidates": candidates}
    if not candidates:
        return {"error": f"No compatible {kind} model is installed", "candidates": []}
    return {
        "error": f"More than one compatible {kind} model is installed; user choice required",
        "candidates": candidates,
    }


def required_models(mode: str, turbo: bool) -> list[str]:
    result = ["ref2va" if mode == "r2v" else "fl2va", "text_encoder", "video_vae", "audio_vae"]
    if turbo:
        result.append("turbo_lora")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", required=True, choices=("t2v", "i2v", "r2v"))
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--turbo", action=argparse.BooleanOptionalAction, default=None)
    args = parser.parse_args()
    try:
        config, config_files = load_config(args.project_root.resolve())
        turbo = args.turbo if args.turbo is not None else config["runtime"]["turbo"]
        address = normalize_address(config["connection"]["address"])
        stats = get_json(address, "/system_stats")
        nodes = ["UNETLoader", "CLIPLoader", "VAELoader"]
        if turbo:
            nodes.extend(TURBO_NODES)
        object_info: dict[str, Any] = {}
        missing_nodes: list[str] = []
        for node in nodes:
            try:
                payload = get_json(address, f"/object_info/{node}")
            except urllib.error.HTTPError as exc:
                if exc.code != 404:
                    raise
                missing_nodes.append(node)
                continue
            if node not in payload:
                missing_nodes.append(node)
                continue
            object_info.update(payload)
        if missing_nodes:
            print(json.dumps({
                "reachable": True,
                "address": address,
                "turbo": turbo,
                "config_files": config_files,
                "system": stats.get("system", {}),
                "missing_nodes": missing_nodes,
                "error": "Required ComfyUI node(s) are not installed",
            }, indent=2))
            return 4
        resolved: dict[str, Any] = {}
        for kind in required_models(args.mode, turbo):
            node, field = MODEL_NODE[kind]
            resolved[kind] = select(kind, choices(object_info, node, field), config["models"].get(kind))
        result = {
            "reachable": True,
            "address": address,
            "turbo": turbo,
            "config_files": config_files,
            "system": stats.get("system", {}),
            "models": resolved,
        }
        print(json.dumps(result, indent=2))
        return 4 if any("error" in value for value in resolved.values()) else 0
    except (ConfigError, KeyError, OSError, ValueError, urllib.error.URLError) as exc:
        print(json.dumps({"reachable": False, "error": str(exc)}, indent=2))
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
