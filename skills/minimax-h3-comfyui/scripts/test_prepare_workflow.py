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
        "turbo": None,
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
        "turbo_lora": None,
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
    def test_pinned_assets_match_manifest_hashes(self) -> None:
        manifest = prepare.read_json(prepare.MANIFEST_PATH)
        self.assertEqual(manifest["default_variant"], "turbo")
        for source in ("source", "turbo_source"):
            for filename, expected in manifest[source]["files"].items():
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
                workflow, metadata = prepare.build_workflow(args)
            self.assertEqual(workflow["104"]["inputs"]["prompt"], "A controlled test")
            self.assertEqual(workflow["104"]["inputs"]["width"], 1280)
            self.assertEqual(workflow["104"]["inputs"]["height"], 736)
            self.assertEqual(workflow["104"]["inputs"]["length"], 243)
            self.assertEqual(workflow["15"]["inputs"]["noise_seed"], 42)
            self.assertEqual(workflow["6"]["inputs"]["unet_name"], "installed-fl2va.safetensors")
            self.assertEqual(workflow["9"]["inputs"]["steps"], 6)
            self.assertEqual(workflow["17"]["class_type"], "MiniMaxH3TurboSampler")
            self.assertEqual(metadata["variant"], "turbo")

    def test_turbo_is_default_for_every_mode(self) -> None:
        cases = {
            "t2v": ("9", "17", "16", "134", "6"),
            "i2v": ("9", "17", "16", "134", "6"),
            "r2v": ("124", "123", "126", "141", "127"),
        }
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with mock.patch.object(prepare, "USER_CONFIG", root / "missing.json"):
                for mode, (scheduler, sampler, guider, lora, loader) in cases.items():
                    with self.subTest(mode=mode):
                        workflow, metadata = prepare.build_workflow(
                            arguments(root, root / f"{mode}.json", mode=mode)
                        )
                        self.assertTrue(metadata["turbo"])
                        self.assertEqual(metadata["variant"], "turbo")
                        self.assertEqual(workflow[sampler]["class_type"], "MiniMaxH3TurboSampler")
                        self.assertEqual(workflow[scheduler]["inputs"]["steps"], 6)
                        self.assertEqual(workflow[scheduler]["inputs"]["model"], [lora, 0])
                        self.assertEqual(workflow[guider]["inputs"]["model"], [lora, 0])
                        self.assertEqual(workflow[lora]["class_type"], "MiniMaxH3TurboLoRA")
                        self.assertEqual(workflow[lora]["inputs"]["model"], [loader, 0])
                        self.assertEqual(workflow[lora]["inputs"]["strength"], 1.0)
                        self.assertFalse(workflow[lora]["inputs"]["low_vram"])

    def test_no_turbo_selects_original_workflow(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            args = arguments(root, root / "out.json", turbo=False)
            with mock.patch.object(prepare, "USER_CONFIG", root / "missing.json"):
                workflow, metadata = prepare.build_workflow(args)
            self.assertFalse(metadata["turbo"])
            self.assertEqual(metadata["variant"], "standard")
            self.assertEqual(workflow["17"]["class_type"], "KSamplerSelect")
            self.assertEqual(workflow["9"]["inputs"]["steps"], 20)
            self.assertNotIn("134", workflow)

    def test_explicit_turbo_flag_overrides_project_config(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            project = root / ".config" / "comfy-config.json"
            project.parent.mkdir()
            project.write_text(json.dumps({"runtime": {"turbo": False}}))
            with mock.patch.object(prepare, "USER_CONFIG", root / "missing.json"):
                _, configured = prepare.build_workflow(arguments(root, root / "off.json"))
                _, explicit = prepare.build_workflow(
                    arguments(root, root / "on.json", turbo=True)
                )
            self.assertEqual(configured["variant"], "standard")
            self.assertEqual(explicit["variant"], "turbo")

    def test_turbo_lora_can_be_overridden(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            args = arguments(root, root / "out.json", turbo_lora="chosen-turbo.safetensors")
            with mock.patch.object(prepare, "USER_CONFIG", root / "missing.json"):
                workflow, _ = prepare.build_workflow(args)
            self.assertEqual(workflow["134"]["inputs"]["lora_name"], "chosen-turbo.safetensors")

    def test_turbo_steps_must_stay_in_recommended_range(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with mock.patch.object(prepare, "USER_CONFIG", root / "missing.json"):
                for steps in (3, 9):
                    with self.subTest(steps=steps):
                        with self.assertRaisesRegex(prepare.ConfigError, "between 4 and 8"):
                            prepare.build_workflow(arguments(root, root / "out.json", steps=steps))

                for steps in (4, 8):
                    with self.subTest(steps=steps):
                        workflow, _ = prepare.build_workflow(
                            arguments(root, root / "out.json", steps=steps)
                        )
                        self.assertEqual(workflow["9"]["inputs"]["steps"], steps)

    def test_turbo_rejects_standard_sampler_override(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with mock.patch.object(prepare, "USER_CONFIG", root / "missing.json"):
                with self.assertRaisesRegex(prepare.ConfigError, "Turbo uses"):
                    prepare.build_workflow(
                        arguments(root, root / "out.json", sampler="res_multistep")
                    )

                with self.assertRaisesRegex(prepare.ConfigError, "simple"):
                    prepare.build_workflow(
                        arguments(root, root / "out.json", scheduler="beta")
                    )

    def test_turbo_ui_assets_contain_matching_nodes_and_defaults(self) -> None:
        manifest = prepare.read_json(prepare.MANIFEST_PATH)
        for mode_name, mode in manifest["modes"].items():
            workflow = prepare.read_json(prepare.WORKFLOW_DIR / mode["variants"]["turbo"]["ui"])
            graph = workflow.get("definitions", {}).get("subgraphs", [workflow])[0]
            nodes = graph["nodes"]
            types = [node["type"] for node in nodes]
            scheduler = next(node for node in nodes if node["type"] == "BasicScheduler")
            with self.subTest(mode=mode_name):
                self.assertIn("MiniMaxH3TurboLoRA", types)
                self.assertIn("MiniMaxH3TurboSampler", types)
                self.assertNotIn("KSamplerSelect", types)
                self.assertEqual(scheduler["widgets_values"][:2], ["simple", 6])
                node_ids = {node["id"] for node in nodes}
                link_ids = [
                    link["id"] if isinstance(link, dict) else link[0]
                    for link in graph["links"]
                ]
                self.assertEqual(len(link_ids), len(set(link_ids)))
                for link in graph["links"]:
                    origin = link["origin_id"] if isinstance(link, dict) else link[1]
                    target = link["target_id"] if isinstance(link, dict) else link[3]
                    self.assertTrue(origin in node_ids or origin < 0)
                    self.assertTrue(target in node_ids or target < 0)

    def test_every_api_variant_has_closed_node_links(self) -> None:
        manifest = prepare.read_json(prepare.MANIFEST_PATH)
        for mode_name, mode in manifest["modes"].items():
            for variant_name, variant in mode["variants"].items():
                workflow = prepare.read_json(prepare.WORKFLOW_DIR / variant["api"])
                with self.subTest(mode=mode_name, variant=variant_name):
                    for node in workflow.values():
                        for value in node["inputs"].values():
                            if (
                                isinstance(value, list)
                                and len(value) == 2
                                and isinstance(value[0], str)
                                and isinstance(value[1], int)
                            ):
                                self.assertIn(value[0], workflow)

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
