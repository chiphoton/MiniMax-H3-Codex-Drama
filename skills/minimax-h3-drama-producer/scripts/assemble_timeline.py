#!/usr/bin/env python3
"""Compile a declarative timeline into a finite H.264/AAC master with FFmpeg."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

import profile_tool


ALLOWED_TRANSITIONS = {
    "fade",
    "fadeblack",
    "fadewhite",
    "wipeleft",
    "wiperight",
    "wipeup",
    "wipedown",
    "slideleft",
    "slideright",
}


def number(value: float) -> str:
    return f"{value:.6f}".rstrip("0").rstrip(".") or "0"


def resolve_path(value: str, base: Path) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else (base / path).resolve()


def has_audio(ffprobe: str, path: Path) -> bool:
    result = subprocess.run(
        [
            ffprobe,
            "-v",
            "error",
            "-select_streams",
            "a:0",
            "-show_entries",
            "stream=index",
            "-of",
            "csv=p=0",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode == 0 and bool(result.stdout.strip())


def transition_spec(raw: Any) -> tuple[str, float]:
    if raw is None or raw == "cut":
        return "cut", 0.0
    if isinstance(raw, str):
        name, duration = raw, 0.2
    elif isinstance(raw, dict):
        name = str(raw.get("type", "cut"))
        duration = float(raw.get("duration", 0 if name == "cut" else 0.2))
    else:
        raise RuntimeError(f"invalid transition: {raw!r}")
    if name != "cut" and name not in ALLOWED_TRANSITIONS:
        raise RuntimeError(f"unsupported FFmpeg transition {name!r}")
    if duration < 0 or duration > 3:
        raise RuntimeError("transition duration must be between 0 and 3 seconds")
    return name, duration


def scale_filter(width: int, height: int, fit: str) -> str:
    if fit == "crop":
        return (
            f"scale={width}:{height}:force_original_aspect_ratio=increase:flags=lanczos,"
            f"crop={width}:{height}"
        )
    if fit == "stretch":
        return f"scale={width}:{height}:flags=lanczos"
    return (
        f"scale={width}:{height}:force_original_aspect_ratio=decrease:flags=lanczos,"
        f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color=black"
    )


def build_command(config: dict[str, Any], config_path: Path, ffmpeg: str, ffprobe: str, output: Path) -> tuple[list[str], float]:
    base = config_path.resolve().parent
    video = config.get("video", {})
    width = int(video.get("width", 1080))
    height = int(video.get("height", 1920))
    fps = float(video.get("fps", 24))
    fit = str(video.get("fit", "contain"))
    if width <= 0 or height <= 0 or fps <= 0 or fit not in {"contain", "crop", "stretch"}:
        raise RuntimeError("invalid video width, height, fps, or fit")

    clips = config.get("clips")
    if not isinstance(clips, list) or not clips:
        raise RuntimeError("timeline requires a non-empty clips array")

    command = [ffmpeg, "-y", "-hide_banner", "-loglevel", "warning"]
    clip_data: list[dict[str, Any]] = []
    for index, clip in enumerate(clips):
        if not isinstance(clip, dict) or "path" not in clip or "duration" not in clip:
            raise RuntimeError(f"clip {index} requires path and duration")
        path = resolve_path(str(clip["path"]), base)
        if not path.is_file():
            raise RuntimeError(f"clip does not exist: {path}")
        duration = float(clip["duration"])
        trim_start = float(clip.get("trim_start", 0))
        if duration <= 0 or trim_start < 0:
            raise RuntimeError(f"clip {index} has invalid duration or trim_start")
        clip_data.append(
            {
                "path": path,
                "duration": duration,
                "trim_start": trim_start,
                "transition": transition_spec(clip.get("transition")) if index > 0 else ("cut", 0.0),
                "has_audio": has_audio(ffprobe, path),
            }
        )
        command.extend(["-i", str(path)])

    master_audio_path: Path | None = None
    master_audio_index: int | None = None
    if config.get("audio_master"):
        master_audio_path = resolve_path(str(config["audio_master"]), base)
        if not master_audio_path.is_file():
            raise RuntimeError(f"audio master does not exist: {master_audio_path}")
        master_audio_index = len(clip_data)
        command.extend(["-i", str(master_audio_path)])

    overlays = config.get("overlays", [])
    if not isinstance(overlays, list):
        raise RuntimeError("overlays must be an array")
    overlay_indices: list[tuple[int, dict[str, Any], Path]] = []
    next_index = len(clip_data) + (1 if master_audio_path else 0)
    for overlay in overlays:
        if not isinstance(overlay, dict) or not all(key in overlay for key in ("path", "start", "end")):
            raise RuntimeError("each overlay requires path, start, and end")
        path = resolve_path(str(overlay["path"]), base)
        if not path.is_file():
            raise RuntimeError(f"overlay does not exist: {path}")
        start, end = float(overlay["start"]), float(overlay["end"])
        if start < 0 or end <= start:
            raise RuntimeError(f"invalid overlay time range for {path}")
        command.extend(["-loop", "1", "-framerate", number(fps), "-i", str(path)])
        overlay_indices.append((next_index, overlay, path))
        next_index += 1

    filters: list[str] = []
    scaled = scale_filter(width, height, fit)
    for index, clip in enumerate(clip_data):
        start = number(clip["trim_start"])
        duration = number(clip["duration"])
        filters.append(
            f"[{index}:v]trim=start={start}:duration={duration},setpts=PTS-STARTPTS,"
            f"fps={number(fps)},{scaled},setsar=1,settb=AVTB[v{index}]"
        )
        if master_audio_path is None:
            if clip["has_audio"]:
                filters.append(
                    f"[{index}:a]atrim=start={start}:duration={duration},asetpts=PTS-STARTPTS,"
                    "aresample=48000,aformat=channel_layouts=stereo"
                    f"[a{index}]"
                )
            else:
                filters.append(
                    f"anullsrc=r=48000:cl=stereo,atrim=duration={duration}[a{index}]"
                )

    transitions = [clip["transition"] for clip in clip_data[1:]]
    all_cuts = all(name == "cut" or duration == 0 for name, duration in transitions)
    total_duration = sum(clip["duration"] for clip in clip_data)

    if len(clip_data) == 1:
        filters.append("[v0]null[vbase]")
        if master_audio_path is None:
            filters.append("[a0]anull[abase]")
    elif all_cuts:
        filters.append("".join(f"[v{i}]" for i in range(len(clip_data))) + f"concat=n={len(clip_data)}:v=1:a=0[vbase]")
        if master_audio_path is None:
            filters.append("".join(f"[a{i}]" for i in range(len(clip_data))) + f"concat=n={len(clip_data)}:v=0:a=1[abase]")
    else:
        video_label = "v0"
        audio_label = "a0"
        running_duration = clip_data[0]["duration"]
        for index in range(1, len(clip_data)):
            name, duration = clip_data[index]["transition"]
            if name == "cut" or duration == 0:
                name, duration = "fade", min(0.001, clip_data[index]["duration"] / 2)
            if duration >= min(running_duration, clip_data[index]["duration"]):
                raise RuntimeError(f"transition before clip {index} is longer than an adjacent clip")
            offset = running_duration - duration
            output_label = "vbase" if index == len(clip_data) - 1 else f"vx{index}"
            filters.append(
                f"[{video_label}][v{index}]xfade=transition={name}:duration={number(duration)}:"
                f"offset={number(offset)}[{output_label}]"
            )
            video_label = output_label
            if master_audio_path is None:
                audio_output = "abase" if index == len(clip_data) - 1 else f"ax{index}"
                filters.append(
                    f"[{audio_label}][a{index}]acrossfade=d={number(duration)}:c1=tri:c2=tri[{audio_output}]"
                )
                audio_label = audio_output
            running_duration += clip_data[index]["duration"] - duration
        total_duration = running_duration

    current_video = "vbase"
    for overlay_number, (input_index, overlay, _) in enumerate(overlay_indices):
        output_label = "vout" if overlay_number == len(overlay_indices) - 1 else f"ov{overlay_number}"
        start, end = number(float(overlay["start"])), number(float(overlay["end"]))
        x, y = int(overlay.get("x", 0)), int(overlay.get("y", 0))
        filters.append(
            f"[{current_video}][{input_index}:v]overlay={x}:{y}:"
            f"enable='between(t,{start},{end})':shortest=1[{output_label}]"
        )
        current_video = output_label
    if not overlay_indices:
        filters.append("[vbase]null[vout]")

    if master_audio_path is not None and master_audio_index is not None:
        filters.append(
            f"[{master_audio_index}:a]atrim=duration={number(total_duration)},asetpts=PTS-STARTPTS,"
            f"aresample=48000,aformat=channel_layouts=stereo,apad,atrim=duration={number(total_duration)}[aout]"
        )
    else:
        filters.append(
            f"[abase]apad,atrim=duration={number(total_duration)}[aout]"
        )

    preset = str(video.get("preset", "medium"))
    crf = int(video.get("crf", 18))
    temporary = output.with_name(output.stem + ".tmp" + output.suffix)
    command.extend(
        [
            "-filter_complex",
            ";".join(filters),
            "-map",
            "[vout]",
            "-map",
            "[aout]",
            "-t",
            number(total_duration),
            "-c:v",
            "libx264",
            "-preset",
            preset,
            "-crf",
            str(crf),
            "-profile:v",
            "high",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            str(config.get("audio_bitrate", "192k")),
            "-ar",
            "48000",
            "-movflags",
            "+faststart",
            str(temporary),
        ]
    )
    return command, total_duration


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeline", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--replace", action="store_true", help="explicitly replace an existing output")
    parser.add_argument("--ffmpeg", default="ffmpeg")
    parser.add_argument("--ffprobe", default="ffprobe")
    args = parser.parse_args()

    temporary: Path | None = None
    try:
        config = profile_tool.load_data(args.timeline)
        base = args.timeline.resolve().parent
        output_value = args.output or Path(str(config.get("output", "../final/master.mp4")))
        output = output_value if output_value.is_absolute() else (base / output_value).resolve()
        if output.suffix.lower() != ".mp4":
            raise RuntimeError("the v1 timeline assembler outputs MP4")
        if output.exists() and not args.replace:
            raise RuntimeError(f"output already exists: {output}; use a versioned path or --replace")
        output.parent.mkdir(parents=True, exist_ok=True)
        ffmpeg = shutil.which(args.ffmpeg) or args.ffmpeg
        ffprobe = shutil.which(args.ffprobe) or args.ffprobe
        command, duration = build_command(config, args.timeline, ffmpeg, ffprobe, output)
        temporary = output.with_name(output.stem + ".tmp" + output.suffix)
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            if temporary.exists():
                temporary.unlink()
            raise RuntimeError(result.stderr.strip() or "ffmpeg timeline assembly failed")
        os.replace(temporary, output)
        print(
            json.dumps(
                {"ok": True, "output": str(output), "duration": duration, "clips": len(config["clips"])},
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    except (KeyError, OSError, RuntimeError, ValueError, profile_tool.ProfileError) as exc:
        if temporary is not None and temporary.exists():
            temporary.unlink()
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
