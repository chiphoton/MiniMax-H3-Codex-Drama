#!/usr/bin/env python3

from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import prepare_workflow as prepare


def arguments(root: Path, output: Path, mode: str = "t2v", **changes: object) -> argparse.Namespace:
    values = {
        "mode": mode,
        "prompt": None,
        "prompt_file": None,
        "project_root": root,
        "output": output,
        "width": None,
        "height": None,
        "duration": None,
        "seed": None,
        "filename_prefix": None,
        "fl2va": None,
        "ref2va": None,
        "text_encoder": None,
        "video_vae": None,
        "audio_vae": None,
        "sampler": None,
        "scheduler": None,
        "steps": None,
        "denoise": None,
        "ref_image_size": None,
        "first_frame": None,
        "last_frame": None,
        "reference_image": [],
        "reference_video": [],
        "reference_audio": [],
    }
    values.update(changes)
    return argparse.Namespace(**values)


class PrepareWorkflowTests(unittest.TestCase):
    def test_pinned_ui_assets_match_manifest_hashes(self) -> None:
        manifest = prepare.read_json(prepare.MANIFEST_PATH)
        for filename, expected in manifest["source"]["files"].items():
            actual = hashlib.sha256((prepare.WORKFLOW_DIR / filename).read_bytes()).hexdigest()
            self.assertEqual(actual, expected, filename)

    def test_duration_snaps_to_h3_grid(self) -> None:
        self.assertEqual(prepare.duration_to_length(5), 124)
        self.assertEqual(prepare.duration_to_length(10), 243)
        self.assertEqual(prepare.duration_to_length(15), 362)

    def test_preview_is_effective_only_when_workflow_loading_is_enabled(self) -> None:
        defaults = {"preview": True, "load_workflow": False}
        visible = {"preview": True, "load_workflow": True}
        hidden = {"preview": False, "load_workflow": True}

        self.assertFalse(prepare.effective_runtime(defaults)["preview"])
        self.assertTrue(prepare.effective_runtime(visible)["preview"])
        self.assertFalse(prepare.effective_runtime(hidden)["preview"])

    def test_project_config_overrides_user_config_and_empty_preserves(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            user = root / "user.json"
            project = root / ".config" / "comfy-config.json"
            project.parent.mkdir()
            user.write_text(json.dumps({"models": {"fl2va": "user.safetensors"}}))
            project.write_text(json.dumps({"models": {"fl2va": "project.safetensors", "video_vae": ""}}))
            with mock.patch.object(prepare, "USER_CONFIG", user):
                config, loaded = prepare.load_config(root)
            self.assertEqual(config["models"]["fl2va"], "project.safetensors")
            self.assertNotIn("video_vae", config["models"])
            self.assertEqual(loaded, [str(user), str(project)])

    def test_known_fields_are_patched(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            args = arguments(
                root,
                root / "out.json",
                prompt="A controlled test",
                width=1280,
                height=736,
                duration=10,
                seed=42,
                fl2va="installed-fl2va.safetensors",
            )
            with mock.patch.object(prepare, "USER_CONFIG", root / "missing.json"):
                workflow, _ = prepare.build_workflow(args)
            self.assertEqual(workflow["104"]["inputs"]["prompt"], "A controlled test")
            self.assertEqual(workflow["104"]["inputs"]["width"], 1280)
            self.assertEqual(workflow["104"]["inputs"]["height"], 736)
            self.assertEqual(workflow["104"]["inputs"]["length"], 243)
            self.assertEqual(workflow["15"]["inputs"]["noise_seed"], 42)
            self.assertEqual(workflow["6"]["inputs"]["unet_name"], "installed-fl2va.safetensors")
            self.assertEqual(workflow["9"]["inputs"]["steps"], 20)

    def test_r2v_media_replaces_template_references(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            args = arguments(
                root,
                root / "out.json",
                mode="r2v",
                reference_image=["one.png"],
                reference_video=["motion.mp4"],
                reference_audio=["voice.wav"],
            )
            with mock.patch.object(prepare, "USER_CONFIG", root / "missing.json"):
                workflow, _ = prepare.build_workflow(args)
            inputs = workflow["136"]["inputs"]
            self.assertNotIn("137", workflow)
            self.assertNotIn("139", workflow)
            self.assertEqual(inputs["ref_images.ref_image_0"], ["200", 0])
            self.assertEqual(inputs["ref_videos.ref_video_0"], ["202", 0])
            self.assertEqual(inputs["ref_video_audios.ref_video_audio_0"], ["202", 1])
            self.assertEqual(inputs["ref_audios.ref_audio_0"], ["203", 0])

    def test_unknown_config_field_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            project = root / ".config" / "comfy-config.json"
            project.parent.mkdir()
            project.write_text(json.dumps({"runtime": {"surprise": True}}))
            with mock.patch.object(prepare, "USER_CONFIG", root / "missing.json"):
                with self.assertRaises(prepare.ConfigError):
                    prepare.load_config(root)


if __name__ == "__main__":
    unittest.main()
