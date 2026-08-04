#!/usr/bin/env python3

from __future__ import annotations

import unittest

import inspect_instance as inspect


class ModelSelectionTests(unittest.TestCase):
    def test_configured_model_must_be_installed(self) -> None:
        result = inspect.select(
            "fl2va",
            ["minimax_h3_fl2va_int8_convrot.safetensors"],
            "missing.safetensors",
        )
        self.assertIn("error", result)
        self.assertNotIn("selected", result)

    def test_pinned_default_wins_when_installed(self) -> None:
        pinned = inspect.PINNED["text_encoder"]
        result = inspect.select("text_encoder", [pinned, "qwen3vl_minimax_h3_other.safetensors"], None)
        self.assertEqual(result["selected"], pinned)
        self.assertEqual(result["reason"], "pinned-default")

    def test_exactly_one_compatible_model_is_selected(self) -> None:
        model = "minimax_h3_ref2va_int8_convrot.safetensors"
        result = inspect.select("ref2va", ["unrelated.safetensors", model], None)
        self.assertEqual(result["selected"], model)
        self.assertEqual(result["reason"], "single-compatible")

    def test_ambiguous_models_require_user_choice(self) -> None:
        result = inspect.select(
            "fl2va",
            [
                "minimax_h3_fl2va_int8_convrot.safetensors",
                "minimax_h3_fl2va_fp8.safetensors",
            ],
            None,
        )
        self.assertIn("error", result)
        self.assertNotIn("selected", result)
        self.assertEqual(len(result["candidates"]), 2)


if __name__ == "__main__":
    unittest.main()
