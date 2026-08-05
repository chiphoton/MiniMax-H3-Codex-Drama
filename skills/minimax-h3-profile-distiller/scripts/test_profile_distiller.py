#!/usr/bin/env python3

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent


class ProfileDistillerTests(unittest.TestCase):
    def run_checked(self, command: list[str]) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        self.assertEqual(0, result.returncode, result.stderr or result.stdout)
        return result

    def test_scaffold_and_project_install(self) -> None:
        with tempfile.TemporaryDirectory(prefix="minimax-h3-profile-test-") as directory:
            root = Path(directory)
            evidence = root / "evidence.json"
            evidence.write_text(
                json.dumps(
                    {
                        "schema_version": "1.0",
                        "sources": [],
                        "inferred_rules": [],
                        "variants": [],
                        "excluded_source_specific_content": [],
                    }
                ),
                encoding="utf-8",
            )
            output = root / "profiles"
            self.run_checked(
                [
                    sys.executable,
                    str(SCRIPT_DIR / "scaffold_profile.py"),
                    "--slug",
                    "sample-profile",
                    "--display-name",
                    "Sample Profile",
                    "--summary",
                    "A test production profile.",
                    "--evidence",
                    str(evidence),
                    "--output-dir",
                    str(output),
                ]
            )
            bundle = output / "sample-profile"
            self.assertTrue((bundle / "profile.yaml").is_file())
            unexpected = bundle / "run.py"
            unexpected.write_text("raise SystemExit\n", encoding="utf-8")
            workspace = root / "workspace"
            unsafe = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_DIR / "install_profile.py"),
                    str(bundle),
                    "--scope",
                    "project",
                    "--workspace",
                    str(workspace),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(0, unsafe.returncode)
            self.assertIn("unexpected entries", unsafe.stdout)
            unexpected.unlink()
            self.run_checked(
                [
                    sys.executable,
                    str(SCRIPT_DIR / "install_profile.py"),
                    str(bundle),
                    "--scope",
                    "project",
                    "--workspace",
                    str(workspace),
                ]
            )
            installed = workspace / ".minimax-h3-drama" / "profiles" / "sample-profile"
            self.assertTrue((installed / "profile.yaml").is_file())

            duplicate = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_DIR / "install_profile.py"),
                    str(bundle),
                    "--scope",
                    "project",
                    "--workspace",
                    str(workspace),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(0, duplicate.returncode)
            self.assertIn("already installed", duplicate.stdout)


if __name__ == "__main__":
    unittest.main()
