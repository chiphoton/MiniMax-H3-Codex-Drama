#!/usr/bin/env python3
"""Render deterministic transparent caption overlays from JSON-compatible YAML."""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import shutil
import sys
from pathlib import Path
from typing import Any

import profile_tool


def parse_color(value: str) -> tuple[int, int, int, int]:
    from PIL import ImageColor

    return ImageColor.getcolor(value, "RGBA")


def percentage_fraction(value: Any, name: str) -> float:
    number = float(value)
    if number > 1:
        number /= 100
    if not 0 <= number <= 1:
        raise RuntimeError(f"{name} must be a fraction from 0 to 1 or a percentage from 0 to 100")
    return number


def font_candidates() -> list[Path]:
    system = platform.system().lower()
    if system == "darwin":
        return [
            Path("/System/Library/Fonts/PingFang.ttc"),
            Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf"),
            Path("/System/Library/Fonts/Helvetica.ttc"),
        ]
    if system == "windows":
        root = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
        return [root / "msyh.ttc", root / "arial.ttf", root / "segoeui.ttf"]
    return [
        Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"),
    ]


def load_font(config: dict[str, Any]):
    from PIL import ImageFont

    size = int(config.get("font_size", 56))
    requested = config.get("font")
    candidates = [Path(requested).expanduser()] if requested else []
    candidates.extend(font_candidates())
    for candidate in candidates:
        if candidate.is_file():
            try:
                return ImageFont.truetype(str(candidate), size=size), str(candidate)
            except OSError:
                continue
    raise RuntimeError("no usable TrueType/OpenType font was found")


def highlight_mask(text: str, terms: list[str]) -> list[bool]:
    mask = [False] * len(text)
    for term in terms:
        if not term:
            continue
        for match in re.finditer(re.escape(term), text, flags=re.IGNORECASE):
            for index in range(match.start(), match.end()):
                mask[index] = True
    return mask


def char_width(draw, char: str, font) -> float:
    return float(draw.textlength(char, font=font))


def wrap_text(draw, text: str, font, max_width: int) -> list[list[tuple[str, int]]]:
    lines: list[list[tuple[str, int]]] = []
    current: list[tuple[str, int]] = []
    width = 0.0
    for index, char in enumerate(text):
        if char == "\n":
            lines.append(current)
            current = []
            width = 0.0
            continue
        advance = char_width(draw, char, font)
        if current and width + advance > max_width:
            while current and current[-1][0].isspace():
                current.pop()
            lines.append(current)
            current = []
            width = 0.0
            if char.isspace():
                continue
        current.append((char, index))
        width += advance
    if current or not lines:
        lines.append(current)
    return lines


def render_cue(
    cue: dict[str, Any],
    config: dict[str, Any],
    output: Path,
    font,
) -> None:
    from PIL import Image, ImageDraw

    width = int(config["width"])
    height = int(config["height"])
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    text = str(cue["text"])
    mask = highlight_mask(text, [str(item) for item in cue.get("highlight_terms", [])])
    max_width = int(width * float(config.get("max_width_pct", 0.86)))
    lines = wrap_text(draw, text, font, max_width)
    max_lines = int(config.get("max_lines", 2))
    if len(lines) > max_lines:
        raise RuntimeError(f"cue {cue.get('id')} wraps to {len(lines)} lines; maximum is {max_lines}")

    stroke_width = int(config.get("stroke_width", 4))
    line_spacing = int(config.get("line_spacing", 12))
    padding_x = int(config.get("padding_x", 24))
    padding_y = int(config.get("padding_y", 16))
    ascent, descent = font.getmetrics()
    line_height = ascent + descent
    line_widths = [sum(char_width(draw, char, font) for char, _ in line) for line in lines]
    text_width = max(line_widths) if line_widths else 0
    text_height = len(lines) * line_height + max(0, len(lines) - 1) * line_spacing
    box_width = int(text_width + 2 * padding_x)
    box_height = int(text_height + 2 * padding_y)
    x0 = int((width - box_width) / 2)

    position = cue.get("position", config.get("position", "bottom"))
    if position == "top":
        y0 = int(height * percentage_fraction(config.get("top_safe_pct", 10), "top_safe_pct"))
    elif position == "center":
        y0 = int((height - box_height) / 2)
    else:
        bottom_safe = percentage_fraction(config.get("bottom_safe_pct", 16), "bottom_safe_pct")
        y0 = int(height * (1 - bottom_safe) - box_height)
    y0 = max(0, min(height - box_height, y0))

    background = parse_color(config.get("background_color", "#000000B8"))
    radius = int(config.get("background_radius", 18))
    draw.rounded_rectangle((x0, y0, x0 + box_width, y0 + box_height), radius=radius, fill=background)

    normal_color = parse_color(config.get("text_color", "#FFFFFFFF"))
    highlight_color = parse_color(config.get("highlight_color", "#FFD400FF"))
    stroke_color = parse_color(config.get("stroke_color", "#000000FF"))

    y = y0 + padding_y
    for line, measured_width in zip(lines, line_widths):
        x = (width - measured_width) / 2
        for char, original_index in line:
            color = highlight_color if mask[original_index] else normal_color
            draw.text(
                (x, y),
                char,
                font=font,
                fill=color,
                stroke_width=stroke_width,
                stroke_fill=stroke_color,
            )
            x += char_width(draw, char, font)
        y += line_height + line_spacing

    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    staging: Path | None = None
    try:
        config = profile_tool.load_data(args.config)
        cues = config.get("cues")
        if not isinstance(cues, list) or not cues:
            raise RuntimeError("caption config requires a non-empty cues array")
        if int(config.get("width", 0)) <= 0 or int(config.get("height", 0)) <= 0:
            raise RuntimeError("caption config requires positive width and height")
        font, font_path = load_font(config)
        output_dir = args.output_dir.expanduser().resolve()
        if output_dir.exists():
            raise RuntimeError(
                f"caption output already exists: {output_dir}; use a new versioned directory"
            )
        output_dir.parent.mkdir(parents=True, exist_ok=True)
        staging = output_dir.parent / f".{output_dir.name}.rendering-{os.getpid()}"
        if staging.exists():
            raise RuntimeError(f"caption staging directory already exists: {staging}")
        staging.mkdir()
        manifest: dict[str, Any] = {
            "schema_version": "1.0",
            "width": int(config["width"]),
            "height": int(config["height"]),
            "font": font_path,
            "overlays": [],
        }
        for index, cue in enumerate(cues):
            if not isinstance(cue, dict) or not all(key in cue for key in ("start", "end", "text")):
                raise RuntimeError(f"caption cue {index} requires start, end, and text")
            start = float(cue["start"])
            end = float(cue["end"])
            if start < 0 or end <= start:
                raise RuntimeError(f"caption cue {index} has an invalid time range")
            cue_id = str(cue.get("id", f"cue-{index + 1:03d}"))
            safe_id = re.sub(r"[^a-zA-Z0-9._-]+", "-", cue_id).strip("-") or f"cue-{index + 1:03d}"
            filename = f"{index + 1:03d}-{safe_id}.png"
            render_cue(cue, config, staging / filename, font)
            manifest["overlays"].append(
                {"id": cue_id, "path": str(output_dir / filename), "start": start, "end": end, "x": 0, "y": 0}
            )

        manifest_path = staging / "overlay-manifest.json"
        temporary = manifest_path.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        os.replace(temporary, manifest_path)
        if output_dir.exists():
            raise RuntimeError(f"caption output appeared during rendering: {output_dir}")
        os.replace(staging, output_dir)
        staging = None
        print(json.dumps({"ok": True, "manifest": str(output_dir / 'overlay-manifest.json'), "count": len(cues)}, ensure_ascii=False, indent=2))
        return 0
    except (profile_tool.ProfileError, RuntimeError, OSError, ValueError, ImportError) as exc:
        if staging is not None and staging.exists():
            shutil.rmtree(staging)
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
