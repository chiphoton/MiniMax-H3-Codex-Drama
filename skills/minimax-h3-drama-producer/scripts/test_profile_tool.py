#!/usr/bin/env python3

from __future__ import annotations

import copy
import unittest

import profile_tool


class ProfileToolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = profile_tool.load_data(profile_tool.DEFAULT_SCHEMA)
        cls.profile_root = profile_tool.SCRIPT_DIR.parent / "references" / "profiles"

    def test_builtin_profiles_are_valid(self) -> None:
        for profile_id in ("base-video", "tiktok-short-drama", "commercial-ad"):
            with self.subTest(profile=profile_id):
                data = profile_tool.load_data(self.profile_root / profile_id / "profile.yaml")
                self.assertEqual([], profile_tool.validate_data(data, self.schema))

    def test_unknown_and_executable_keys_are_rejected(self) -> None:
        data = profile_tool.load_data(self.profile_root / "base-video" / "profile.yaml")
        data["script"] = "echo unsafe"
        errors = profile_tool.validate_data(data, self.schema)
        self.assertTrue(any("executable key" in item for item in errors))
        self.assertTrue(any("unknown key" in item for item in errors))

    def test_lists_replace_and_mappings_merge(self) -> None:
        base = {"a": {"x": 1, "items": [1, 2]}, "b": 2}
        overlay = {"a": {"items": [3], "y": 4}}
        self.assertEqual(
            {"a": {"x": 1, "items": [3], "y": 4}, "b": 2},
            profile_tool.deep_merge(base, overlay),
        )

    def test_invalid_duration_order_is_rejected(self) -> None:
        data = copy.deepcopy(
            profile_tool.load_data(self.profile_root / "base-video" / "profile.yaml")
        )
        data["format"]["duration_s"] = {"min": 30, "target": 10, "max": 20}
        errors = profile_tool.validate_data(data, self.schema)
        self.assertTrue(any("min <= target <= max" in item for item in errors))


if __name__ == "__main__":
    unittest.main()
