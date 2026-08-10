#!/usr/bin/env python3

from __future__ import annotations

import copy
import unittest

import prepare_workflow as prepare


class PrepareWorkflowTests(unittest.TestCase):
    def test_prompt_is_copied_exactly_to_api_and_ui_workflows(self) -> None:
        prompt = "  保持人物不变。\nRemove the blue object; don't ‘fix’ grammar.\n[style=yes] stays literal.  "
        manifest = prepare.read_json(prepare.MANIFEST_PATH)
        defaults = manifest["defaults"]
        api = prepare.read_json(prepare.WORKFLOW_DIR / manifest["template"]["api"])
        ui = prepare.read_json(prepare.WORKFLOW_DIR / manifest["template"]["ui"])

        prepared_api = prepare.patch_api(
            copy.deepcopy(api),
            manifest,
            ["uploaded.png"],
            prompt,
            defaults["checkpoint"],
            defaults["lora"],
            None,
        )
        prepared_ui = prepare.patch_ui(
            copy.deepcopy(ui),
            manifest,
            ["uploaded.png"],
            prompt,
            defaults["checkpoint"],
            defaults["lora"],
            None,
        )

        self.assertEqual(prepared_api[manifest["api_nodes"]["prompt"]]["inputs"]["prompt"], prompt)
        ui_prompt = prepare.find_ui_node(
            prepared_ui,
            manifest["ui_nodes"]["prompt"],
            "TextEncodeQwenImageEditPlusAdvance_lrzjason",
        )
        self.assertEqual(ui_prompt["widgets_values"][0], prompt)


if __name__ == "__main__":
    unittest.main()
