#!/usr/bin/env python3
"""Mix positioned audio tracks and normalize the result with FFmpeg."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

import profile_tool


def resolve_path(value: str, base: Path) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else (base / path).resolve()


def ffmpeg_escape_number(value: float) -> str:
    return f"{value:.6f}".rstrip("0").rstrip(".") or "0"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--replace", action="store_true", help="explicitly replace an existing output")
    parser.add_argument("--ffmpeg", default="ffmpeg")
    args = parser.parse_args()

    temporary: Path | None = None
    try:
        config = profile_tool.load_data(args.config)
        tracks = config.get("tracks")
        if not isinstance(tracks, list) or not tracks:
            raise RuntimeError("audio config requires a non-empty tracks array")
        duration = float(config["duration"])
        if duration <= 0:
            raise RuntimeError("duration must be positive")
        sample_rate = int(config.get("sample_rate", 48000))
        layout = str(config.get("channel_layout", "stereo"))
        if layout not in {"mono", "stereo"}:
            raise RuntimeError("channel_layout must be mono or stereo")
        base = args.config.resolve().parent
        output_value = args.output or Path(str(config.get("output", "master-audio.wav")))
        output = output_value if output_value.is_absolute() else (base / output_value).resolve()
        if output.exists() and not args.replace:
            raise RuntimeError(f"output already exists: {output}; use a versioned path or --replace")
        output.parent.mkdir(parents=True, exist_ok=True)
        ffmpeg = shutil.which(args.ffmpeg) or args.ffmpeg

        command = [ffmpeg, "-y", "-hide_banner", "-loglevel", "warning"]
        input_paths: list[Path] = []
        for index, track in enumerate(tracks):
            if not isinstance(track, dict) or "path" not in track:
                raise RuntimeError(f"track {index} requires path")
            path = resolve_path(str(track["path"]), base)
            if not path.is_file():
                raise RuntimeError(f"audio track does not exist: {path}")
            input_paths.append(path)
            command.extend(["-i", str(path)])

        filters: list[str] = []
        labels: list[str] = []
        for index, track in enumerate(tracks):
            start = float(track.get("start", 0))
            trim_start = float(track.get("trim_start", 0))
            track_duration = track.get("duration")
            gain_db = float(track.get("gain_db", 0))
            if start < 0 or trim_start < 0:
                raise RuntimeError(f"track {index} has a negative start or trim_start")
            trim = f"atrim=start={ffmpeg_escape_number(trim_start)}"
            if track_duration is not None:
                if float(track_duration) <= 0:
                    raise RuntimeError(f"track {index} duration must be positive")
                trim += f":duration={ffmpeg_escape_number(float(track_duration))}"
            delay_ms = int(round(start * 1000))
            delay = str(delay_ms) if layout == "mono" else f"{delay_ms}|{delay_ms}"
            label = f"t{index}"
            filters.append(
                f"[{index}:a]{trim},asetpts=PTS-STARTPTS,aresample={sample_rate},"
                f"aformat=channel_layouts={layout},volume={ffmpeg_escape_number(gain_db)}dB,"
                f"adelay={delay}[{label}]"
            )
            labels.append(f"[{label}]")

        target_lufs = float(config.get("target_lufs", -14))
        true_peak = float(config.get("true_peak_db", -1.5))
        lra = float(config.get("lra", 11))
        filters.append(
            "".join(labels)
            + f"amix=inputs={len(labels)}:duration=longest:normalize=0,"
            + f"atrim=duration={ffmpeg_escape_number(duration)},"
            + f"loudnorm=I={ffmpeg_escape_number(target_lufs)}:"
            + f"TP={ffmpeg_escape_number(true_peak)}:LRA={ffmpeg_escape_number(lra)}[mix]"
        )

        temporary = output.with_name(output.stem + ".tmp" + output.suffix)
        command.extend(["-filter_complex", ";".join(filters), "-map", "[mix]"])
        if output.suffix.lower() == ".wav":
            command.extend(["-c:a", "pcm_s24le"])
        else:
            command.extend(["-c:a", "aac", "-b:a", str(config.get("aac_bitrate", "192k"))])
        command.extend(["-ar", str(sample_rate), "-t", ffmpeg_escape_number(duration), str(temporary)])
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            if temporary.exists():
                temporary.unlink()
            raise RuntimeError(result.stderr.strip() or "ffmpeg audio mix failed")
        os.replace(temporary, output)
        print(
            json.dumps(
                {
                    "ok": True,
                    "output": str(output),
                    "duration": duration,
                    "tracks": len(tracks),
                    "target_lufs": target_lufs,
                    "true_peak_db": true_peak,
                },
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
