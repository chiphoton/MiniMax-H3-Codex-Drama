#!/usr/bin/env python3
"""Extract deterministic production evidence from local reference videos."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def run(command: list[str], timeout: float | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, capture_output=True, text=True, timeout=timeout, check=False)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rational(value: str | None) -> float | None:
    if not value or value == "0/0":
        return None
    if "/" in value:
        numerator, denominator = value.split("/", 1)
        return float(numerator) / float(denominator) if float(denominator) else None
    return float(value)


def parse_loudnorm(text: str) -> dict[str, float] | None:
    matches = re.findall(r"\{\s*\"input_i\".*?\}", text, flags=re.DOTALL)
    if not matches:
        return None
    try:
        raw = json.loads(matches[-1])
        numeric: dict[str, float] = {}
        for key, value in raw.items():
            try:
                numeric[key] = float(value)
            except (TypeError, ValueError):
                continue
        return numeric or None
    except (json.JSONDecodeError, TypeError, ValueError):
        return None


def average(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def rewrite_artifact_paths(source: dict[str, Any], staging: Path, target: Path) -> None:
    artifacts = source["artifacts"]
    if artifacts["contact_sheet"]:
        contact = Path(artifacts["contact_sheet"]).relative_to(staging)
        artifacts["contact_sheet"] = str(target / contact)
    artifacts["sample_frames"] = [
        str(target / Path(item).relative_to(staging)) for item in artifacts["sample_frames"]
    ]


def analyze_one(
    path: Path,
    source_id: str,
    output_dir: Path,
    ffmpeg: str,
    ffprobe: str,
    scene_threshold: float,
    sample_count: int,
) -> dict[str, Any]:
    probe = run(
        [
            ffprobe,
            "-v",
            "error",
            "-show_entries",
            "format=duration,size,bit_rate,format_name:stream=index,codec_name,codec_type,width,height,r_frame_rate,sample_rate,channels",
            "-of",
            "json",
            str(path),
        ]
    )
    if probe.returncode != 0:
        raise RuntimeError(f"ffprobe failed for {path}: {probe.stderr.strip()}")
    metadata = json.loads(probe.stdout)
    streams = metadata.get("streams", [])
    video = next((item for item in streams if item.get("codec_type") == "video"), None)
    audio = next((item for item in streams if item.get("codec_type") == "audio"), None)
    if not video:
        raise RuntimeError(f"no video stream in {path}")
    duration = float(metadata.get("format", {}).get("duration", 0))
    if duration <= 0:
        raise RuntimeError(f"invalid duration for {path}")

    scene = run(
        [
            ffmpeg,
            "-hide_banner",
            "-nostats",
            "-loglevel",
            "info",
            "-i",
            str(path),
            "-vf",
            f"select=gt(scene\\,{scene_threshold}),showinfo",
            "-an",
            "-f",
            "null",
            "-",
        ]
    )
    scene_times = sorted(
        {
            round(float(value), 3)
            for value in re.findall(r"pts_time:([0-9.]+)", scene.stderr + scene.stdout)
            if 0 < float(value) < duration
        }
    )
    boundaries = [0.0, *scene_times, duration]
    shot_lengths = [round(boundaries[index + 1] - boundaries[index], 3) for index in range(len(boundaries) - 1)]

    source_dir = output_dir / source_id
    frames_dir = source_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    sample_fps = sample_count / duration
    sample_pattern = frames_dir / "sample-%03d.png"
    samples = run(
        [
            ffmpeg,
            "-y",
            "-hide_banner",
            "-loglevel",
            "warning",
            "-i",
            str(path),
            "-vf",
            f"fps={sample_fps:.8f}",
            "-frames:v",
            str(sample_count),
            str(sample_pattern),
        ]
    )
    if samples.returncode != 0:
        raise RuntimeError(f"frame sampling failed for {path}: {samples.stderr.strip()}")

    width, height = int(video["width"]), int(video["height"])
    cell_width = 270
    cell_height = max(2, int(round(cell_width * height / width)))
    if cell_height % 2:
        cell_height += 1
    rows = int(math.ceil(sample_count / 4))
    contact_sheet = source_dir / "contact-sheet.png"
    contact = run(
        [
            ffmpeg,
            "-y",
            "-hide_banner",
            "-loglevel",
            "warning",
            "-i",
            str(path),
            "-vf",
            f"fps={sample_fps:.8f},scale={cell_width}:{cell_height}:flags=lanczos,tile=4x{rows}:padding=4:margin=4",
            "-frames:v",
            "1",
            "-update",
            "1",
            str(contact_sheet),
        ]
    )

    loudness = None
    if audio:
        loud = run(
            [
                ffmpeg,
                "-hide_banner",
                "-nostats",
                "-loglevel",
                "info",
                "-i",
                str(path),
                "-vn",
                "-af",
                "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json",
                "-f",
                "null",
                "-",
            ]
        )
        loudness = parse_loudnorm(loud.stderr + loud.stdout)

    signal = run(
        [
            ffmpeg,
            "-hide_banner",
            "-nostats",
            "-loglevel",
            "info",
            "-i",
            str(path),
            "-vf",
            "fps=1/5,signalstats,metadata=print",
            "-an",
            "-f",
            "null",
            "-",
        ]
    )
    signal_text = signal.stderr + signal.stdout
    yavg = [float(value) for value in re.findall(r"lavfi\.signalstats\.YAVG=([0-9.]+)", signal_text)]
    satavg = [float(value) for value in re.findall(r"lavfi\.signalstats\.SATAVG=([0-9.]+)", signal_text)]
    hueavg = [float(value) for value in re.findall(r"lavfi\.signalstats\.HUEAVG=([0-9.-]+)", signal_text)]

    return {
        "source_id": source_id,
        "path": str(path),
        "sha256": sha256_file(path),
        "size_bytes": path.stat().st_size,
        "measured": {
            "duration_s": duration,
            "width": width,
            "height": height,
            "aspect_ratio": round(width / height, 6),
            "fps": rational(video.get("r_frame_rate")),
            "video_codec": video.get("codec_name"),
            "audio_codec": audio.get("codec_name") if audio else None,
            "sample_rate": int(audio["sample_rate"]) if audio and audio.get("sample_rate") else None,
            "channels": audio.get("channels") if audio else None,
            "scene_threshold": scene_threshold,
            "scene_cut_times_s": scene_times,
            "estimated_shot_count": len(shot_lengths),
            "estimated_shot_lengths_s": shot_lengths,
            "estimated_average_shot_length_s": round(sum(shot_lengths) / len(shot_lengths), 3),
            "loudness": loudness,
            "sampled_signal": {
                "yavg": average(yavg),
                "satavg": average(satavg),
                "hueavg": average(hueavg),
                "samples": len(yavg),
            },
        },
        "artifacts": {
            "contact_sheet": str(contact_sheet) if contact.returncode == 0 and contact_sheet.is_file() else None,
            "sample_frames": [str(item) for item in sorted(frames_dir.glob("sample-*.png"))],
        },
        "observations": [],
        "notes": ["Scene cuts are threshold-based candidates and require visual review."],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, action="append", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--scene-threshold", type=float, default=0.30)
    parser.add_argument("--samples", type=int, default=12)
    parser.add_argument("--ffmpeg", default="ffmpeg")
    parser.add_argument("--ffprobe", default="ffprobe")
    args = parser.parse_args()

    staging_dir: Path | None = None
    try:
        if not 0 < args.scene_threshold < 1:
            raise RuntimeError("scene threshold must be between 0 and 1")
        if not 4 <= args.samples <= 24:
            raise RuntimeError("samples must be between 4 and 24")
        ffmpeg = shutil.which(args.ffmpeg) or args.ffmpeg
        ffprobe = shutil.which(args.ffprobe) or args.ffprobe
        output_dir = args.output_dir.expanduser().resolve()
        if output_dir.exists():
            raise RuntimeError(
                f"analysis already exists at {output_dir}; use a new versioned output directory"
            )
        output_dir.parent.mkdir(parents=True, exist_ok=True)
        staging_dir = output_dir.parent / f".{output_dir.name}.analyzing-{os.getpid()}"
        if staging_dir.exists():
            raise RuntimeError(f"staging directory already exists: {staging_dir}")
        staging_dir.mkdir()
        sources = []
        for index, input_value in enumerate(args.input, start=1):
            path = input_value.expanduser().resolve()
            if not path.is_file():
                raise RuntimeError(f"input does not exist: {path}")
            sources.append(
                analyze_one(
                    path,
                    f"video-{index:02d}",
                    staging_dir,
                    ffmpeg,
                    ffprobe,
                    args.scene_threshold,
                    args.samples,
                )
            )
        for source in sources:
            rewrite_artifact_paths(source, staging_dir, output_dir)

        evidence: dict[str, Any] = {
            "schema_version": "1.0",
            "created_at": utc_now(),
            "method": {
                "scene_detection": "FFmpeg scene score threshold",
                "sampling": f"{args.samples} evenly spaced frames per source",
                "audio": "FFmpeg EBU R128 loudnorm measurement when audio exists",
                "color": "sampled FFmpeg signalstats averages",
            },
            "sources": sources,
            "inferred_rules": [],
            "variants": [],
            "excluded_source_specific_content": [],
        }
        evidence_path = staging_dir / "evidence.json"
        temporary = evidence_path.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        os.replace(temporary, evidence_path)
        if output_dir.exists():
            raise RuntimeError(
                f"{output_dir} appeared during analysis; use a new versioned output directory"
            )
        os.replace(staging_dir, output_dir)
        staging_dir = None
        final_evidence = output_dir / "evidence.json"
        print(
            json.dumps(
                {
                    "ok": True,
                    "evidence": str(final_evidence),
                    "sources": len(sources),
                    "contact_sheets": [item["artifacts"]["contact_sheet"] for item in sources],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
        if staging_dir is not None and staging_dir.exists():
            shutil.rmtree(staging_dir)
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
