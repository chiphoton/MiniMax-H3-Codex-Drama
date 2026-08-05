#!/usr/bin/env python3
"""Record a completed human-or-agent visual review in existing QC reports."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import qc_media


def unique(existing: list[str], additions: list[str]) -> list[str]:
    return list(dict.fromkeys([*existing, *additions]))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--qc-dir", type=Path, required=True)
    parser.add_argument("--status", choices=["pass", "fail"], required=True)
    parser.add_argument("--check", action="append", required=True)
    parser.add_argument("--note", action="append", default=[])
    parser.add_argument("--hard-failure", action="append", default=[])
    parser.add_argument("--warning", action="append", default=[])
    parser.add_argument("--reviewer", default="Codex visual inspection")
    args = parser.parse_args()

    try:
        qc_dir = args.qc_dir.expanduser().resolve()
        report_json = qc_dir / "qc-report.json"
        report_md = qc_dir / "qc-report.md"
        if not report_json.is_file():
            raise RuntimeError(f"QC report does not exist: {report_json}")
        report: dict[str, Any] = json.loads(report_json.read_text(encoding="utf-8"))
        if not isinstance(report, dict) or "technical_result" not in report:
            raise RuntimeError("QC report is malformed")
        contact_value = report.get("artifacts", {}).get("contact_sheet")
        if not contact_value or not Path(contact_value).is_file():
            raise RuntimeError("the visual review requires an existing contact sheet")

        report["visual_review"] = {
            "status": args.status,
            "reviewed_at": qc_media.utc_now(),
            "reviewer": args.reviewer,
            "checks": args.check,
            "notes": args.note,
        }
        report["hard_failures"] = unique(report.get("hard_failures", []), args.hard_failure)
        report["warnings"] = unique(report.get("warnings", []), args.warning)
        report["overall_result"] = (
            "fail"
            if report["technical_result"] == "fail"
            or args.status == "fail"
            or report["hard_failures"]
            else "pass"
        )

        qc_media.atomic_write(
            report_json, json.dumps(report, ensure_ascii=False, indent=2) + "\n"
        )
        qc_media.atomic_write(report_md, qc_media.markdown_report(report))
        print(
            json.dumps(
                {
                    "ok": report["overall_result"] == "pass",
                    "overall_result": report["overall_result"],
                    "technical_result": report["technical_result"],
                    "visual_result": args.status,
                    "report_json": str(report_json),
                    "report_md": str(report_md),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0 if report["overall_result"] == "pass" else 1
    except (OSError, RuntimeError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
