#!/usr/bin/env python3
"""Use an already-installed system TTS engine and normalize its output to WAV."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path


def choose_engine(requested: str) -> tuple[str, str]:
    candidates = [requested] if requested != "auto" else ["say", "espeak-ng", "espeak"]
    for name in candidates:
        path = shutil.which(name)
        if path:
            return name, path
    raise RuntimeError("no supported system TTS engine is installed")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--text")
    source.add_argument("--text-file", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--replace", action="store_true", help="explicitly replace an existing output")
    parser.add_argument("--engine", choices=["auto", "say", "espeak-ng", "espeak"], default="auto")
    parser.add_argument("--voice")
    parser.add_argument("--rate", type=int)
    parser.add_argument("--sample-rate", type=int, default=48000)
    parser.add_argument("--target-lufs", type=float, default=-18)
    parser.add_argument("--true-peak-db", type=float, default=-2)
    parser.add_argument("--ffmpeg", default="ffmpeg")
    args = parser.parse_args()

    temporary_output: Path | None = None
    try:
        text = args.text if args.text is not None else args.text_file.read_text(encoding="utf-8")
        if not text.strip():
            raise RuntimeError("TTS text is empty")
        engine_name, engine_path = choose_engine(args.engine)
        ffmpeg = shutil.which(args.ffmpeg) or args.ffmpeg
        output = args.output.expanduser().resolve()
        if output.suffix.lower() != ".wav":
            raise RuntimeError("the system TTS adapter outputs WAV files")
        if output.exists() and not args.replace:
            raise RuntimeError(f"output already exists: {output}; use a versioned path or --replace")
        output.parent.mkdir(parents=True, exist_ok=True)
        temporary_output = output.with_name(output.stem + ".tmp" + output.suffix)

        with tempfile.TemporaryDirectory(prefix="minimax-h3-drama-tts-") as directory:
            raw = Path(directory) / ("speech.aiff" if engine_name == "say" else "speech.wav")
            if engine_name == "say":
                command = [engine_path, "-o", str(raw)]
                if args.voice:
                    command.extend(["-v", args.voice])
                if args.rate:
                    command.extend(["-r", str(args.rate)])
                command.append(text)
            else:
                command = [engine_path, "-w", str(raw)]
                if args.voice:
                    command.extend(["-v", args.voice])
                if args.rate:
                    command.extend(["-s", str(args.rate)])
                command.append(text)
            generated = subprocess.run(command, capture_output=True, text=True, check=False)
            if generated.returncode != 0 or not raw.is_file():
                raise RuntimeError(generated.stderr.strip() or f"{engine_name} did not create audio")

            converted = subprocess.run(
                [
                    ffmpeg,
                    "-y",
                    "-hide_banner",
                    "-loglevel",
                    "warning",
                    "-i",
                    str(raw),
                    "-af",
                    f"loudnorm=I={args.target_lufs}:TP={args.true_peak_db}:LRA=11",
                    "-ar",
                    str(args.sample_rate),
                    "-ac",
                    "1",
                    "-c:a",
                    "pcm_s24le",
                    str(temporary_output),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            if converted.returncode != 0 or not temporary_output.is_file():
                raise RuntimeError(converted.stderr.strip() or "FFmpeg TTS conversion failed")
        os.replace(temporary_output, output)
        print(
            json.dumps(
                {
                    "ok": True,
                    "engine": engine_name,
                    "output": str(output),
                    "voice": args.voice,
                    "rate": args.rate,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    except (OSError, RuntimeError) as exc:
        if temporary_output is not None and temporary_output.exists():
            temporary_output.unlink()
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
