#!/usr/bin/env python3

from __future__ import annotations

import argparse
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import init_project
import project_state


class InitProjectTests(unittest.TestCase):
    def args(self, workspace: Path, project: str = "demo-video") -> argparse.Namespace:
        return argparse.Namespace(
            workspace=workspace,
            outputs_dir=Path("outputs"),
            project=project,
            title="Demo Video",
            profile="tiktok-short-drama",
            mode="guided",
            language="en",
        )

    def test_unicode_slugs_do_not_collapse_to_one_value(self) -> None:
        self.assertNotEqual(init_project.slugify("短剧甲"), init_project.slugify("短剧乙"))
        self.assertNotEqual(init_project.slugify("AI短剧甲"), init_project.slugify("AI短剧乙"))

    def test_create_and_resume_project(self) -> None:
        with tempfile.TemporaryDirectory(prefix="minimax-h3-project-test-") as directory:
            workspace = Path(directory)
            args = self.args(workspace)
            project_dir, state, resumed = init_project.create_project(args)
            self.assertFalse(resumed)
            self.assertTrue((project_dir / "project.yaml").is_file())
            self.assertTrue((project_dir / "profile" / "resolved-profile.yaml").is_file())
            self.assertTrue((project_dir / "clips" / "raw").is_dir())
            init_project.atomic_write(project_dir / "project.yaml", state)

            second_dir, second_state, second_resumed = init_project.create_project(args)
            self.assertTrue(second_resumed)
            self.assertEqual(project_dir, second_dir)
            self.assertEqual(state["project"]["slug"], second_state["project"]["slug"])

            state_path = project_dir / "project.yaml"
            update_args = argparse.Namespace(
                project=state_path,
                stage="planning",
                status="in_progress",
                note="test update",
            )
            self.assertEqual(0, project_state.command_set_stage(update_args))
            updated = init_project.load_state(state_path)
            self.assertEqual("in_progress", updated["stages"]["planning"]["status"])

    def test_existing_unknown_directory_is_not_adopted(self) -> None:
        with tempfile.TemporaryDirectory(prefix="minimax-h3-project-test-") as directory:
            workspace = Path(directory)
            (workspace / "outputs" / "demo-video").mkdir(parents=True)
            with self.assertRaises(init_project.ProjectError):
                init_project.create_project(self.args(workspace))

    def test_failed_initialization_removes_staging_directory(self) -> None:
        with tempfile.TemporaryDirectory(prefix="minimax-h3-project-test-") as directory:
            workspace = Path(directory)
            args = self.args(workspace)
            with mock.patch.object(
                init_project, "copy_profile_bundle", side_effect=OSError("copy failed")
            ):
                with self.assertRaises(OSError):
                    init_project.create_project(args)
            outputs = workspace / "outputs"
            self.assertTrue(outputs.is_dir())
            self.assertEqual([], list(outputs.iterdir()))


if __name__ == "__main__":
    unittest.main()
