#!/usr/bin/env python3
"""Run deterministic technical QC and create a whole-film contact sheet."""

from __future__ import annotations

import argparse
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


def rational(value: str | None) -> float | None:
    if not value or value == "0/0":
        return None
    if "/" in value:
        numerator, denominator = value.split("/", 1)
        if float(denominator) == 0:
            return None
        return float(numerator) / float(denominator)
    return float(value)


def parse_loudnorm(output: str) -> dict[str, float] | None:
    blocks = re.findall(r"\{\s*\"input_i\".*?\}", output, flags=re.DOTALL)
    if not blocks:
        return None
    try:
        raw = json.loads(blocks[-1])
        numeric: dict[str, float] = {}
        for key, value in raw.items():
            try:
                numeric[key] = float(value)
            except (TypeError, ValueError):
                continue
        return numeric or None
    except (json.JSONDecodeError, TypeError, ValueError):
        return None


def parse_black(output: str) -> list[dict[str, float]]:
    pattern = re.compile(
        r"black_start:(?P<start>-?[0-9.]+)\s+black_end:(?P<end>-?[0-9.]+)\s+black_duration:(?P<duration>[0-9.]+)"
    )
    return [{key: float(value) for key, value in match.groupdict().items()} for match in pattern.finditer(output)]


def parse_freezes(output: str, total_duration: float) -> list[dict[str, float | None]]:
    starts = [float(value) for value in re.findall(r"freeze_start:\s*(-?[0-9.]+)", output)]
    ends = [float(value) for value in re.findall(r"freeze_end:\s*(-?[0-9.]+)", output)]
    durations = [float(value) for value in re.findall(r"freeze_duration:\s*([0-9.]+)", output)]
    results: list[dict[str, float | None]] = []
    for index, start in enumerate(starts):
        end = ends[index] if index < len(ends) else total_duration
        duration = durations[index] if index < len(durations) else max(0.0, end - start)
        results.append({"start": start, "end": end, "duration": duration})
    return results


def atomic_write(path: Path, text: str) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    os.replace(temporary, path)


def markdown_report(report: dict[str, Any]) -> str:
    media = report.get("media", {})
    audio = report.get("audio", {})
    lines = [
        "# Final media QC",
        "",
        f"- Checked: {report['checked_at']}",
        f"- File: `{report['input']}`",
        f"- Overall result: **{report.get('overall_result', 'pending')}**",
        f"- Technical result: **{report['technical_result']}**",
        f"- Visual review: **{report['visual_review']['status']}**",
        "",
        "## Media",
        "",
        f"- Duration: {media.get('duration_s', 'unknown')} s",
        f"- Video: {media.get('width', 'unknown')}×{media.get('height', 'unknown')} at {media.get('fps', 'unknown')} fps, {media.get('video_codec', 'unknown')}",
        f"- Audio: {media.get('audio_codec', 'none')}, {media.get('sample_rate', 'n/a')} Hz, {media.get('channels', 'n/a')} channel(s)",
    ]
    if audio.get("measurements"):
        measurements = audio["measurements"]
        lines.extend(
            [
                f"- Integrated loudness: {measurements.get('input_i')} LUFS",
                f"- True peak: {measurements.get('input_tp')} dBTP",
                f"- Loudness range: {measurements.get('input_lra')} LU",
            ]
        )
    lines.extend(["", "## Hard failures", ""])
    failures = report.get("hard_failures", [])
    lines.extend([f"- {item}" for item in failures] or ["- None."])
    lines.extend(["", "## Review candidates", ""])
    warnings = report.get("warnings", [])
    lines.extend([f"- {item}" for item in warnings] or ["- None."])
    lines.extend(
        [
            "",
            "## Visual review",
            "",
        ]
    )
    review = report.get("visual_review", {})
    checks = review.get("checks", [])
    notes = review.get("notes", [])
    if review.get("status") == "pending":
        lines.append(
            "Inspect `final-contact-sheet.png` plus shot-level sheets for identity or product fidelity, environment and prop continuity, screen direction, narrative order, transitions, and caption safe areas. Record the review before marking the project complete."
        )
    else:
        lines.extend(
            [
                f"- Status: **{review.get('status', 'unknown')}**",
                f"- Reviewed: {review.get('reviewed_at', 'unknown')}",
                f"- Reviewer: {review.get('reviewer', 'unknown')}",
                *[f"- Check: {item}" for item in checks],
                *[f"- Note: {item}" for item in notes],
            ]
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--media-info-output", type=Path)
    parser.add_argument("--expected-width", type=int)
    parser.add_argument("--expected-height", type=int)
    parser.add_argument("--expected-fps", type=float)
    parser.add_argument("--expected-duration", type=float)
    parser.add_argument("--duration-tolerance", type=float, default=0.1)
    parser.add_argument("--fps-tolerance", type=float, default=0.01)
    parser.add_argument("--target-lufs", type=float)
    parser.add_argument("--loudness-tolerance", type=float, default=1.0)
    parser.add_argument("--true-peak-ceiling", type=float, default=-1.0)
    parser.add_argument("--black-duration", type=float, default=0.25)
    parser.add_argument("--freeze-duration", type=float, default=1.0)
    parser.add_argument("--require-audio", action="store_true")
    parser.add_argument("--ffmpeg", default="ffmpeg")
    parser.add_argument("--ffprobe", default="ffprobe")
    args = parser.parse_args()

    input_path = args.input.expanduser().resolve()
    output_dir = args.output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    ffmpeg = shutil.which(args.ffmpeg) or args.ffmpeg
    ffprobe = shutil.which(args.ffprobe) or args.ffprobe
    hard_failures: list[str] = []
    warnings: list[str] = []

    if not input_path.is_file():
        print(json.dumps({"ok": False, "error": f"input does not exist: {input_path}"}, indent=2))
        return 1

    probe = run(
        [
            ffprobe,
            "-v",
            "error",
            "-show_entries",
            "format=duration,size,bit_rate:stream=index,codec_name,codec_type,width,height,r_frame_rate,sample_rate,channels",
            "-of",
            "json",
            str(input_path),
        ]
    )
    try:
        probe_data = json.loads(probe.stdout) if probe.returncode == 0 else {}
    except json.JSONDecodeError:
        probe_data = {}
    if probe.returncode != 0 or not probe_data.get("streams"):
        hard_failures.append("FFprobe could not read valid streams.")

    streams = probe_data.get("streams", [])
    video_stream = next((item for item in streams if item.get("codec_type") == "video"), {})
    audio_stream = next((item for item in streams if item.get("codec_type") == "audio"), {})
    try:
        duration = float(probe_data.get("format", {}).get("duration", 0))
    except (TypeError, ValueError):
        duration = 0
    fps = rational(video_stream.get("r_frame_rate"))
    width, height = video_stream.get("width"), video_stream.get("height")

    if not video_stream:
        hard_failures.append("No video stream exists.")
    if args.require_audio and not audio_stream:
        hard_failures.append("The profile requires audio but no audio stream exists.")
    elif not audio_stream:
        warnings.append("No audio stream exists; confirm that silence is intentional.")
    if args.expected_width is not None and width != args.expected_width:
        hard_failures.append(f"Width is {width}, expected {args.expected_width}.")
    if args.expected_height is not None and height != args.expected_height:
        hard_failures.append(f"Height is {height}, expected {args.expected_height}.")
    if args.expected_fps is not None and (fps is None or abs(fps - args.expected_fps) > args.fps_tolerance):
        hard_failures.append(f"Frame rate is {fps}, expected {args.expected_fps} ± {args.fps_tolerance}.")
    if args.expected_duration is not None and abs(duration - args.expected_duration) > args.duration_tolerance:
        hard_failures.append(f"Duration is {duration:.3f}s, expected {args.expected_duration:.3f}s ± {args.duration_tolerance:.3f}s.")

    decode = run([ffmpeg, "-hide_banner", "-nostats", "-v", "error", "-i", str(input_path), "-f", "null", "-"])
    if decode.returncode != 0:
        hard_failures.append("A complete decode failed: " + (decode.stderr.strip() or "unknown FFmpeg error"))

    black = run(
        [
            ffmpeg,
            "-hide_banner",
            "-nostats",
            "-v",
            "info",
            "-i",
            str(input_path),
            "-vf",
            f"blackdetect=d={args.black_duration}:pix_th=0.05",
            "-an",
            "-f",
            "null",
            "-",
        ]
    )
    black_intervals = parse_black(black.stderr + black.stdout)
    if black_intervals:
        warnings.append(f"Detected {len(black_intervals)} black interval candidate(s); verify intent.")

    freeze = run(
        [
            ffmpeg,
            "-hide_banner",
            "-nostats",
            "-v",
            "info",
            "-i",
            str(input_path),
            "-vf",
            f"freezedetect=n=-60dB:d={args.freeze_duration}",
            "-an",
            "-f",
            "null",
            "-",
        ]
    )
    freeze_intervals = parse_freezes(freeze.stderr + freeze.stdout, duration)
    if freeze_intervals:
        warnings.append(f"Detected {len(freeze_intervals)} freeze candidate(s); verify holds and ending pads.")

    loudness: dict[str, float] | None = None
    if audio_stream:
        loud = run(
            [
                ffmpeg,
                "-hide_banner",
                "-nostats",
                "-v",
                "info",
                "-i",
                str(input_path),
                "-vn",
                "-af",
                "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json",
                "-f",
                "null",
                "-",
            ]
        )
        loudness = parse_loudnorm(loud.stderr + loud.stdout)
        if loudness is None:
            warnings.append("Audio loudness measurement was unavailable.")
        else:
            if loudness.get("input_tp", -99) > args.true_peak_ceiling:
                hard_failures.append(
                    f"True peak is {loudness['input_tp']:.2f} dBTP, above {args.true_peak_ceiling:.2f} dBTP."
                )
            if args.target_lufs is not None and abs(loudness.get("input_i", -99) - args.target_lufs) > args.loudness_tolerance:
                hard_failures.append(
                    f"Integrated loudness is {loudness.get('input_i')} LUFS, outside {args.target_lufs} ± {args.loudness_tolerance} LU."
                )

    contact_sheet = output_dir / "final-contact-sheet.png"
    contact_result = None
    if duration > 0 and width and height:
        sample_fps = 12 / duration
        cell_width = 270
        cell_height = max(2, int(round(cell_width * float(height) / float(width))))
        if cell_height % 2:
            cell_height += 1
        contact_result = run(
            [
                ffmpeg,
                "-y",
                "-hide_banner",
                "-loglevel",
                "warning",
                "-i",
                str(input_path),
                "-vf",
                f"fps={sample_fps:.8f},scale={cell_width}:{cell_height}:flags=lanczos,tile=4x3:padding=4:margin=4",
                "-frames:v",
                "1",
                "-update",
                "1",
                str(contact_sheet),
            ]
        )
        if contact_result.returncode != 0 or not contact_sheet.is_file():
            warnings.append("The whole-film contact sheet could not be generated.")

    media = {
        "duration_s": duration,
        "width": width,
        "height": height,
        "fps": fps,
        "video_codec": video_stream.get("codec_name"),
        "audio_codec": audio_stream.get("codec_name") if audio_stream else None,
        "sample_rate": int(audio_stream["sample_rate"]) if audio_stream.get("sample_rate") else None,
        "channels": audio_stream.get("channels"),
        "size_bytes": int(probe_data.get("format", {}).get("size", 0) or 0),
        "bit_rate": int(probe_data.get("format", {}).get("bit_rate", 0) or 0),
    }
    report: dict[str, Any] = {
        "schema_version": "1.0",
        "checked_at": utc_now(),
        "input": str(input_path),
        "technical_result": "pass" if not hard_failures else "fail",
        "overall_result": "pending" if not hard_failures else "fail",
        "visual_review": {"status": "pending", "checks": [], "notes": []},
        "media": media,
        "audio": {"measurements": loudness},
        "black_intervals": black_intervals,
        "freeze_intervals": freeze_intervals,
        "hard_failures": hard_failures,
        "warnings": warnings,
        "artifacts": {
            "contact_sheet": str(contact_sheet) if contact_sheet.is_file() else None,
            "media_info": str(args.media_info_output.resolve()) if args.media_info_output else None,
        },
        "tooling": {
            "ffmpeg": ffmpeg,
            "ffprobe": ffprobe,
            "decode_exit_code": decode.returncode,
        },
    }

    report_json = output_dir / "qc-report.json"
    report_md = output_dir / "qc-report.md"
    atomic_write(report_json, json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    atomic_write(report_md, markdown_report(report))
    if args.media_info_output:
        args.media_info_output.parent.mkdir(parents=True, exist_ok=True)
        atomic_write(args.media_info_output, json.dumps(probe_data, ensure_ascii=False, indent=2) + "\n")

    print(
        json.dumps(
            {
                "ok": not hard_failures,
                "technical_result": report["technical_result"],
                "visual_review": "pending",
                "report_json": str(report_json),
                "report_md": str(report_md),
                "contact_sheet": str(contact_sheet) if contact_sheet.is_file() else None,
                "hard_failures": len(hard_failures),
                "warnings": len(warnings),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if not hard_failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
