#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
DISTILLER = SCRIPT_DIR.parent.parent / "minimax-h3-profile-distiller" / "scripts" / "analyze_video.py"


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg is required")
class MediaPipelineTests(unittest.TestCase):
    def run_checked(self, command: list[str]) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        self.assertEqual(0, result.returncode, result.stderr or result.stdout)
        return result

    def make_clip(self, path: Path, color: str, frequency: int) -> None:
        self.run_checked(
            [
                "ffmpeg",
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-f",
                "lavfi",
                "-i",
                f"color=c={color}:s=320x180:r=24:d=1",
                "-f",
                "lavfi",
                "-i",
                f"sine=frequency={frequency}:duration=1",
                "-shortest",
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-c:a",
                "aac",
                str(path),
            ]
        )

    def test_mix_assemble_qc_and_distill(self) -> None:
        with tempfile.TemporaryDirectory(prefix="minimax-h3-media-test-") as directory:
            root = Path(directory)
            clip_a, clip_b = root / "a.mp4", root / "b.mp4"
            self.make_clip(clip_a, "red", 440)
            self.make_clip(clip_b, "blue", 660)

            mix_config = root / "mix.json"
            mix_config.write_text(
                json.dumps(
                    {
                        "duration": 2,
                        "output": "mix.wav",
                        "tracks": [
                            {"path": str(clip_a), "start": 0, "gain_db": -6},
                            {"path": str(clip_b), "start": 1, "gain_db": -6},
                        ],
                    }
                ),
                encoding="utf-8",
            )
            self.run_checked([sys.executable, str(SCRIPT_DIR / "mix_audio.py"), "--config", str(mix_config)])
            duplicate_mix = subprocess.run(
                [sys.executable, str(SCRIPT_DIR / "mix_audio.py"), "--config", str(mix_config)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(0, duplicate_mix.returncode)
            self.assertIn("output already exists", duplicate_mix.stdout)

            timeline = root / "timeline.json"
            timeline.write_text(
                json.dumps(
                    {
                        "output": "master.mp4",
                        "video": {"width": 320, "height": 180, "fps": 24, "preset": "ultrafast", "crf": 28},
                        "audio_master": "mix.wav",
                        "clips": [
                            {"path": str(clip_a), "duration": 1},
                            {"path": str(clip_b), "duration": 1, "transition": {"type": "fade", "duration": 0.1}},
                        ],
                    }
                ),
                encoding="utf-8",
            )
            self.run_checked([sys.executable, str(SCRIPT_DIR / "assemble_timeline.py"), "--timeline", str(timeline)])
            master = root / "master.mp4"
            self.assertTrue(master.is_file())
            duplicate_master = subprocess.run(
                [sys.executable, str(SCRIPT_DIR / "assemble_timeline.py"), "--timeline", str(timeline)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(0, duplicate_master.returncode)
            self.assertIn("output already exists", duplicate_master.stdout)

            qc_dir = root / "qc"
            self.run_checked(
                [
                    sys.executable,
                    str(SCRIPT_DIR / "qc_media.py"),
                    "--input",
                    str(master),
                    "--output-dir",
                    str(qc_dir),
                    "--expected-width",
                    "320",
                    "--expected-height",
                    "180",
                    "--expected-fps",
                    "24",
                    "--expected-duration",
                    "1.9",
                    "--duration-tolerance",
                    "0.12",
                ]
            )
            report = json.loads((qc_dir / "qc-report.json").read_text(encoding="utf-8"))
            self.assertEqual("pass", report["technical_result"])
            self.assertEqual("pending", report["overall_result"])
            self.assertTrue((qc_dir / "final-contact-sheet.png").is_file())
            self.run_checked(
                [
                    sys.executable,
                    str(SCRIPT_DIR / "record_visual_qc.py"),
                    "--qc-dir",
                    str(qc_dir),
                    "--status",
                    "pass",
                    "--check",
                    "Synthetic red and blue shots appear in order.",
                ]
            )
            reviewed = json.loads((qc_dir / "qc-report.json").read_text(encoding="utf-8"))
            self.assertEqual("pass", reviewed["overall_result"])
            self.assertEqual("pass", reviewed["visual_review"]["status"])

            analysis_dir = root / "analysis"
            self.run_checked(
                [
                    sys.executable,
                    str(DISTILLER),
                    "--input",
                    str(master),
                    "--output-dir",
                    str(analysis_dir),
                    "--samples",
                    "4",
                ]
            )
            evidence = json.loads((analysis_dir / "evidence.json").read_text(encoding="utf-8"))
            self.assertEqual(1, len(evidence["sources"]))
            self.assertIsNotNone(evidence["sources"][0]["measured"]["loudness"])
            contact_sheet = Path(evidence["sources"][0]["artifacts"]["contact_sheet"])
            self.assertTrue(contact_sheet.is_file())
            contact_sheet.resolve().relative_to(analysis_dir.resolve())

            duplicate = subprocess.run(
                [
                    sys.executable,
                    str(DISTILLER),
                    "--input",
                    str(master),
                    "--output-dir",
                    str(analysis_dir),
                    "--samples",
                    "4",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(0, duplicate.returncode)
            self.assertIn("use a new versioned output directory", duplicate.stdout)

    @unittest.skipUnless(importlib.util.find_spec("PIL"), "Pillow is required")
    def test_caption_renderer(self) -> None:
        with tempfile.TemporaryDirectory(prefix="minimax-h3-caption-test-") as directory:
            root = Path(directory)
            config = root / "captions.json"
            config.write_text(
                json.dumps(
                    {
                        "width": 320,
                        "height": 568,
                        "font_size": 24,
                        "top_safe_pct": 12,
                        "bottom_safe_pct": 18,
                        "cues": [
                            {"id": "one", "start": 0, "end": 1, "text": "Respect every role.", "highlight_terms": ["Respect"]}
                        ],
                    }
                ),
                encoding="utf-8",
            )
            output = root / "overlays"
            self.run_checked(
                [
                    sys.executable,
                    str(SCRIPT_DIR / "render_caption_overlays.py"),
                    "--config",
                    str(config),
                    "--output-dir",
                    str(output),
                ]
            )
            self.assertTrue((output / "001-one.png").is_file())
            duplicate = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_DIR / "render_caption_overlays.py"),
                    "--config",
                    str(config),
                    "--output-dir",
                    str(output),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(0, duplicate.returncode)
            self.assertIn("use a new versioned directory", duplicate.stdout)


if __name__ == "__main__":
    unittest.main()
