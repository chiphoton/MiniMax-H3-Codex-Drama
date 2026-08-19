#!/usr/bin/env python3
"""Run a read-only MiniMax-H3 Drama environment preflight."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import platform
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
PLUGIN_ROOT = SCRIPT_DIR.parents[2]
COMFY_SKILL = PLUGIN_ROOT / "skills" / "minimax-h3-comfyui"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def run_text(command: list[str], timeout: float = 8.0) -> tuple[int | None, str]:
    try:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=timeout,
            check=False,
        )
        return result.returncode, result.stdout
    except (OSError, subprocess.TimeoutExpired) as exc:
        return None, str(exc)


def command_report(name: str, version_args: list[str]) -> dict[str, Any]:
    path = shutil.which(name)
    if not path:
        return {"status": "missing", "path": None, "version": None}
    code, output = run_text([path, *version_args])
    first_line = output.strip().splitlines()[0] if output.strip() else None
    return {
        "status": "available" if code == 0 else "error",
        "path": path,
        "version": first_line,
        "exit_code": code,
    }


def ffmpeg_report(path: str | None) -> dict[str, Any]:
    if not path:
        return {"status": "missing", "filters": {}, "encoders": {}}
    _, filter_text = run_text([path, "-hide_banner", "-filters"])
    _, encoder_text = run_text([path, "-hide_banner", "-encoders"])
    filters = {
        name: name in filter_text
        for name in ["blackdetect", "drawtext", "freezedetect", "loudnorm", "overlay", "subtitles", "xfade"]
    }
    encoders = {name: name in encoder_text for name in ["aac", "libx264"]}
    status = "available" if all(filters[name] for name in ["blackdetect", "loudnorm", "overlay", "xfade"]) and all(encoders.values()) else "limited"
    return {"status": status, "filters": filters, "encoders": encoders}


def python_modules_report() -> dict[str, Any]:
    modules = {
        "Pillow": importlib.util.find_spec("PIL") is not None,
        "PyYAML": importlib.util.find_spec("yaml") is not None,
    }
    return {
        "status": "available" if modules["Pillow"] else "limited",
        "modules": modules,
        "python": sys.version.splitlines()[0],
        "executable": sys.executable,
    }


def font_report() -> dict[str, Any]:
    system = platform.system().lower()
    candidates: list[Path]
    if system == "darwin":
        candidates = [Path("/System/Library/Fonts"), Path("/Library/Fonts"), Path.home() / "Library/Fonts"]
    elif system == "windows":
        windows_dir = Path(os.environ.get("WINDIR", "C:/Windows"))
        candidates = [windows_dir / "Fonts"]
    else:
        candidates = [Path("/usr/share/fonts"), Path("/usr/local/share/fonts"), Path.home() / ".fonts"]
    existing = [str(path) for path in candidates if path.is_dir()]
    return {"status": "available" if existing else "missing", "directories": existing}


def tts_report() -> dict[str, Any]:
    engines = {name: shutil.which(name) for name in ["say", "espeak-ng", "espeak"]}
    available = {name: path for name, path in engines.items() if path}
    return {
        "status": "available" if available else "optional-missing",
        "engines": available,
        "note": "System TTS is an optional fallback, not a quality guarantee.",
    }


def comfyui_report(url: str, timeout: float) -> dict[str, Any]:
    endpoint = url.rstrip("/") + "/system_stats"
    request = urllib.request.Request(endpoint, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return {
            "status": "reachable",
            "url": url,
            "endpoint": endpoint,
            "system": payload.get("system", {}),
            "devices": payload.get("devices", []),
        }
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError) as exc:
        return {"status": "unreachable", "url": url, "endpoint": endpoint, "error": str(exc)}


def workflow_report() -> dict[str, Any]:
    manifest = COMFY_SKILL / "assets" / "workflows" / "manifest.json"
    required = [
        "t2v.api.json",
        "i2v.api.json",
        "r2v.api.json",
        "t2v-turbo.api.json",
        "i2v-turbo.api.json",
        "r2v-turbo.api.json",
        "manifest.json",
    ]
    base = manifest.parent
    files = {name: (base / name).is_file() for name in required}
    return {
        "status": "available" if all(files.values()) else "missing",
        "directory": str(base),
        "files": files,
    }


def atomic_write(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--comfyui-url", default="http://localhost:8188")
    parser.add_argument("--timeout", type=float, default=3.0)
    parser.add_argument("--require-captions", action="store_true")
    args = parser.parse_args()

    ffmpeg = command_report("ffmpeg", ["-version"])
    ffprobe = command_report("ffprobe", ["-version"])
    ffmpeg_features = ffmpeg_report(ffmpeg.get("path"))
    python_capability = python_modules_report()
    caption_methods = {
        "ffmpeg_subtitles": bool(ffmpeg_features.get("filters", {}).get("subtitles")),
        "pillow_overlays": bool(python_capability.get("modules", {}).get("Pillow")),
    }
    caption_rendering = {
        "status": "available" if any(caption_methods.values()) else "missing",
        "required": args.require_captions,
        "methods": caption_methods,
    }
    report: dict[str, Any] = {
        "schema_version": "1.0",
        "checked_at": utc_now(),
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
        },
        "capabilities": {
            "gpt_image": {
                "status": "agent-check-required",
                "note": "The Codex agent must confirm the image generation skill and tool at runtime.",
            },
            "comfyui": comfyui_report(args.comfyui_url, args.timeout),
            "workflows": workflow_report(),
            "ffmpeg": ffmpeg,
            "ffmpeg_features": ffmpeg_features,
            "ffprobe": ffprobe,
            "python": python_capability,
            "fonts": font_report(),
            "tts": tts_report(),
            "caption_rendering": caption_rendering,
        },
    }

    critical = {
        "comfyui": report["capabilities"]["comfyui"]["status"] == "reachable",
        "workflows": report["capabilities"]["workflows"]["status"] == "available",
        "ffmpeg": ffmpeg["status"] == "available",
        "ffprobe": ffprobe["status"] == "available",
        "caption_rendering": not args.require_captions or caption_rendering["status"] == "available",
    }
    report["critical"] = critical
    report["ready_for_full_pipeline"] = all(critical.values())
    report["missing_or_limited"] = [name for name, ready in critical.items() if not ready]
    atomic_write(args.output, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ready_for_full_pipeline"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
