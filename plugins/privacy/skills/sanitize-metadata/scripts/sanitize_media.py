#!/usr/bin/env python3
"""Value-blind local metadata audit and sanitization for private media."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


CATEGORY_ORDER = (
    "location",
    "identity",
    "timestamp",
    "device",
    "description",
    "identifier",
    "embedded_preview",
)

IGNORED_GROUPS = {"", "composite", "exiftool", "file", "system"}

LOCATION_FRAGMENTS = (
    "address",
    "city",
    "country",
    "gps",
    "geotag",
    "geolocation",
    "latitude",
    "longitude",
    "location",
    "postalcode",
    "province",
    "sublocation",
    "worldregion",
)
IDENTITY_FRAGMENTS = (
    "artist",
    "author",
    "byline",
    "company",
    "contact",
    "copyright",
    "credit",
    "creator",
    "email",
    "organization",
    "owner",
    "person",
    "publisher",
    "regionname",
    "rights",
    "writereditor",
)
TIMESTAMP_FRAGMENTS = (
    "contentcreatedate",
    "createdate",
    "creationdate",
    "datecreated",
    "datetimedigitized",
    "datetimeoriginal",
    "gpsdatestamp",
    "gpsdatetime",
    "gpstimestamp",
    "mediacreatedate",
    "mediamodifydate",
    "metadatadate",
    "modifydate",
    "timecreated",
    "trackcreatedate",
    "trackmodifydate",
)
DEVICE_TAGS = {
    "cameraidentifier",
    "cameramodelname",
    "cameraownername",
    "deviceid",
    "devicemake",
    "devicemodel",
    "firmware",
    "firmwareversion",
    "hostcomputer",
    "internalserialnumber",
    "lensid",
    "lensmake",
    "lensmodel",
    "lensserialnumber",
    "make",
    "model",
    "ownername",
    "serialnumber",
    "software",
}
DESCRIPTION_FRAGMENTS = (
    "caption",
    "category",
    "comment",
    "description",
    "headline",
    "history",
    "instructions",
    "keywords",
    "label",
    "objectname",
    "rating",
    "subject",
    "title",
    "usercomment",
)
IDENTIFIER_FRAGMENTS = (
    "assetid",
    "contentidentifier",
    "digest",
    "documentid",
    "instanceid",
    "mediaid",
    "originaldocumentid",
    "uniqueid",
    "umid",
    "uuid",
)
PREVIEW_FRAGMENTS = (
    "coverart",
    "embeddedimage",
    "jpegfromraw",
    "otherimage",
    "previewimage",
    "previewpng",
    "photoshopthumbnail",
    "thumbnail",
)
TECHNICAL_DESCRIPTION_PREFIXES = (
    "handlerdescription",
    "sampledescription",
)

IMAGE_EXTENSIONS = {
    ".avif",
    ".bmp",
    ".gif",
    ".heic",
    ".heif",
    ".jpeg",
    ".jpg",
    ".png",
    ".tif",
    ".tiff",
    ".webp",
}
IMAGE_CODERS = {
    ".avif": "avif",
    ".bmp": "bmp",
    ".gif": "gif",
    ".heic": "heic",
    ".heif": "heic",
    ".jpeg": "jpeg",
    ".jpg": "jpeg",
    ".png": "png",
    ".tif": "tiff",
    ".tiff": "tiff",
    ".webp": "webp",
}
VIDEO_INPUT_EXTENSIONS = {
    ".3gp",
    ".avi",
    ".flv",
    ".m2ts",
    ".m4v",
    ".mkv",
    ".mov",
    ".mp4",
    ".mpeg",
    ".mpg",
    ".mts",
    ".ts",
    ".webm",
}
VIDEO_EXTENSIONS = {".avi", ".m4v", ".mkv", ".mov", ".mp4", ".webm"}
DEEP_VIDEO_EXTENSIONS = {".m4v", ".mkv", ".mov", ".mp4"}
ENCODER_PRESETS = {
    "ultrafast",
    "superfast",
    "veryfast",
    "faster",
    "fast",
    "medium",
    "slow",
    "slower",
    "veryslow",
    "placebo",
}


class PrivacyError(RuntimeError):
    """A failure safe to summarize without raw diagnostics."""


class ResidualMetadataError(PrivacyError):
    def __init__(self, counts: dict[str, int]) -> None:
        super().__init__("sensitive metadata remains after sanitization")
        self.counts = counts


def normalize_tag(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower())


def is_zero_timestamp(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    normalized = re.sub(r"[\s:./+\-TZ]", "", value).strip("0")
    return normalized == ""


def classify_tag(group: str, tag: str, value: Any) -> str | None:
    group_norm = normalize_tag(group)
    tag_norm = normalize_tag(tag)
    if group_norm in IGNORED_GROUPS or not tag_norm:
        return None
    if any(fragment in tag_norm for fragment in PREVIEW_FRAGMENTS):
        return "embedded_preview"
    if "gps" in group_norm or any(fragment in tag_norm for fragment in LOCATION_FRAGMENTS):
        return "location"
    if any(fragment in tag_norm for fragment in IDENTITY_FRAGMENTS):
        return "identity"
    if any(fragment in tag_norm for fragment in TIMESTAMP_FRAGMENTS):
        if is_zero_timestamp(value):
            return None
        return "timestamp"
    if tag_norm in DEVICE_TAGS or tag_norm.endswith("serialnumber"):
        return "device"
    if any(tag_norm.startswith(prefix) for prefix in TECHNICAL_DESCRIPTION_PREFIXES):
        return None
    if any(fragment in tag_norm for fragment in DESCRIPTION_FRAGMENTS):
        return "description"
    if any(fragment in tag_norm for fragment in IDENTIFIER_FRAGMENTS):
        return "identifier"
    return None


def require_tool(name: str) -> str:
    path = shutil.which(name)
    if not path:
        raise PrivacyError(f"required local command is not installed: {name}")
    return path


def run_capture(command: list[str], purpose: str) -> str:
    try:
        result = subprocess.run(
            command,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            encoding="utf-8",
            errors="replace",
        )
    except OSError as exc:
        raise PrivacyError(f"{purpose} could not start") from exc
    if result.returncode != 0:
        raise PrivacyError(f"{purpose} failed; diagnostics were suppressed for privacy")
    return result.stdout


def run_silent(command: list[str], purpose: str) -> None:
    run_capture(command, purpose)


def resolve_input(raw_path: str) -> Path:
    if raw_path == "-" or "://" in raw_path:
        raise PrivacyError("input must be a local file")
    path = Path(raw_path).expanduser()
    try:
        resolved = path.resolve(strict=True)
    except OSError as exc:
        raise PrivacyError("input must be a local regular file") from exc
    if not resolved.is_file():
        raise PrivacyError("input must be a local regular file")
    return resolved


def resolve_output(raw_path: str, overwrite: bool) -> Path:
    if raw_path == "-" or "://" in raw_path:
        raise PrivacyError("output must be a local file")
    path = Path(raw_path).expanduser()
    parent = path.parent.resolve(strict=True)
    output = parent / path.name
    if output.is_symlink():
        raise PrivacyError("output must not be a symbolic link")
    if output.exists():
        if not output.is_file():
            raise PrivacyError("output must be a regular file")
        if not overwrite:
            raise PrivacyError("output exists; use --overwrite only with user authorization")
    if not output.suffix:
        raise PrivacyError("output must have a file extension")
    return output


def detect_media_type(path: Path) -> str:
    file_tool = require_tool("file")
    mime_type = run_capture(
        [file_tool, "--brief", "--mime-type", "--", str(path)],
        "media type detection",
    ).strip()
    if mime_type.startswith("image/"):
        if path.suffix.lower() not in IMAGE_EXTENSIONS:
            raise PrivacyError("unsupported raster image input extension")
        return "image"
    if mime_type.startswith("video/"):
        if path.suffix.lower() not in VIDEO_INPUT_EXTENSIONS:
            raise PrivacyError("unsupported video input extension")
        return "video"
    raise PrivacyError("input must be a supported image or video")


def audit_metadata(path: Path) -> dict[str, int]:
    exiftool = require_tool("exiftool")
    raw_json = run_capture(
        [
            exiftool,
            "-json",
            "-G1",
            "-s",
            "-a",
            "-charset",
            "filename=UTF8",
            "-api",
            "LargeFileSupport=1",
            str(path),
        ],
        "metadata audit",
    )
    try:
        payload = json.loads(raw_json)
    except json.JSONDecodeError as exc:
        raise PrivacyError("metadata audit returned an unreadable local result") from exc
    if not isinstance(payload, list) or not payload or not isinstance(payload[0], dict):
        raise PrivacyError("metadata audit returned an unexpected local result")

    counts = {category: 0 for category in CATEGORY_ORDER}
    for full_tag, value in payload[0].items():
        if full_tag == "SourceFile":
            continue
        group, separator, tag = full_tag.partition(":")
        if not separator:
            group, tag = "", full_tag
        category = classify_tag(group, tag, value)
        if category:
            counts[category] += 1
    return counts


def total_sensitive(counts: dict[str, int]) -> int:
    return sum(counts.values())


def strip_all_metadata(path: Path) -> None:
    exiftool = require_tool("exiftool")
    run_silent(
        [exiftool, "-overwrite_original", "-all=", str(path)],
        "metadata removal",
    )


def create_temp_output(output: Path) -> Path:
    descriptor, temp_name = tempfile.mkstemp(
        prefix=".privacy-sanitize-",
        suffix=output.suffix,
        dir=output.parent,
    )
    os.close(descriptor)
    temp_path = Path(temp_name)
    temp_path.unlink()
    return temp_path


def sanitize_image(
    input_path: Path,
    temp_path: Path,
    deep: bool,
    image_quality: int,
) -> None:
    suffix = temp_path.suffix.lower()
    if suffix not in IMAGE_EXTENSIONS:
        raise PrivacyError("unsupported image output extension")
    if not deep:
        if input_path.suffix.lower() != suffix:
            raise PrivacyError("standard image mode requires matching input and output extensions")
        shutil.copyfile(input_path, temp_path)
    else:
        magick = require_tool("magick")
        input_coder = IMAGE_CODERS.get(input_path.suffix.lower())
        if not input_coder:
            raise PrivacyError("unsupported deep image input extension")
        command = [
            magick,
            f"{input_coder}:{input_path}",
            "-auto-orient",
            "-strip",
        ]
        if suffix in {".jpeg", ".jpg", ".webp"}:
            command.extend(["-quality", str(image_quality)])
        command.append(str(temp_path))
        run_silent(command, "deep image sanitization")
    strip_all_metadata(temp_path)


def sanitize_video(
    input_path: Path,
    temp_path: Path,
    deep: bool,
    video_crf: int,
    video_preset: str,
    audio_bitrate: str,
) -> None:
    suffix = temp_path.suffix.lower()
    if suffix not in VIDEO_EXTENSIONS:
        raise PrivacyError("unsupported video output extension")
    if deep and suffix not in DEEP_VIDEO_EXTENSIONS:
        raise PrivacyError("deep video mode supports mp4, m4v, mov, or mkv output")

    ffmpeg = require_tool("ffmpeg")
    command = [
        ffmpeg,
        "-nostdin",
        "-hide_banner",
        "-loglevel",
        "error",
        "-n",
        "-protocol_whitelist",
        "file",
        "-i",
        str(input_path),
        "-map",
        "0:V:0",
        "-map",
        "0:a:0?",
        "-map_metadata",
        "-1",
        "-map_metadata:s",
        "-1",
        "-map_chapters",
        "-1",
        "-sn",
        "-dn",
    ]
    if deep:
        command.extend(
            [
                "-c:v",
                "libx264",
                "-crf",
                str(video_crf),
                "-preset",
                video_preset,
                "-pix_fmt",
                "yuv420p",
                "-c:a",
                "aac",
                "-b:a",
                audio_bitrate,
            ]
        )
    else:
        command.extend(["-c", "copy"])
    if suffix in {".m4v", ".mov", ".mp4"}:
        command.extend(["-movflags", "+faststart"])
    command.append(str(temp_path))
    run_silent(command, "video sanitization")
    strip_all_metadata(temp_path)


def print_counts(prefix: str, counts: dict[str, int]) -> None:
    for category in CATEGORY_ORDER:
        print(f"{prefix}{category}_fields={counts[category]}")


def sanitize(args: argparse.Namespace) -> int:
    input_path = resolve_input(args.input)
    output_path = resolve_output(args.output, args.overwrite)
    if input_path == output_path:
        raise PrivacyError("input and output must be different files")

    media_type = detect_media_type(input_path)
    before_counts = audit_metadata(input_path)
    temp_path = create_temp_output(output_path)
    try:
        if media_type == "image":
            sanitize_image(input_path, temp_path, args.deep, args.image_quality)
        else:
            sanitize_video(
                input_path,
                temp_path,
                args.deep,
                args.video_crf,
                args.video_preset,
                args.audio_bitrate,
            )
        after_counts = audit_metadata(temp_path)
        if total_sensitive(after_counts) != 0:
            raise ResidualMetadataError(after_counts)
        output_bytes = temp_path.stat().st_size
        os.replace(temp_path, output_path)
    finally:
        if temp_path.exists():
            temp_path.unlink()

    print("status=ok")
    print("action=sanitize")
    print(f"media_type={media_type}")
    print(f"level={'deep' if args.deep else 'standard'}")
    print(f"sensitive_field_count_before={total_sensitive(before_counts)}")
    print_counts("before_", before_counts)
    print("sensitive_field_count_after=0")
    print(f"output_bytes={output_bytes}")
    return 0


def audit(args: argparse.Namespace) -> int:
    input_path = resolve_input(args.input)
    media_type = detect_media_type(input_path)
    counts = audit_metadata(input_path)
    total = total_sensitive(counts)
    print("status=ok")
    print("action=audit")
    print(f"media_type={media_type}")
    print("audit_scope=common_embedded_privacy_fields")
    print(f"sensitive_metadata_present={'yes' if total else 'no'}")
    print(f"sensitive_field_count={total}")
    print_counts("", counts)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Audit or remove private image/video metadata without printing values."
    )
    subparsers = parser.add_subparsers(dest="action", required=True)

    audit_parser = subparsers.add_parser("audit", help="Report safe metadata category counts")
    audit_parser.add_argument("--input", required=True, help="Local image or video path")
    audit_parser.set_defaults(handler=audit)

    sanitize_parser = subparsers.add_parser(
        "sanitize", help="Write a separate metadata-sanitized output"
    )
    sanitize_parser.add_argument("--input", required=True, help="Local image or video path")
    sanitize_parser.add_argument("--output", required=True, help="Separate local output path")
    sanitize_parser.add_argument(
        "--deep",
        action="store_true",
        help="Decode/re-encode locally for stronger sanitization",
    )
    sanitize_parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace an existing output after successful verification",
    )
    sanitize_parser.add_argument(
        "--image-quality",
        type=int,
        default=95,
        help="JPEG/WebP quality in deep mode (default: 95)",
    )
    sanitize_parser.add_argument(
        "--video-crf",
        type=int,
        default=20,
        help="H.264 CRF in deep mode (default: 20)",
    )
    sanitize_parser.add_argument(
        "--video-preset",
        default="medium",
        choices=sorted(ENCODER_PRESETS),
        help="H.264 preset in deep mode (default: medium)",
    )
    sanitize_parser.add_argument(
        "--audio-bitrate",
        default="128k",
        help="AAC bitrate in deep mode (default: 128k)",
    )
    sanitize_parser.set_defaults(handler=sanitize)
    return parser


def validate_options(args: argparse.Namespace) -> None:
    if args.action != "sanitize":
        return
    if not 1 <= args.image_quality <= 100:
        raise PrivacyError("image quality must be an integer from 1 to 100")
    if not 0 <= args.video_crf <= 51:
        raise PrivacyError("video CRF must be an integer from 0 to 51")
    if not re.fullmatch(r"[1-9][0-9]*[kKmM]?", args.audio_bitrate):
        raise PrivacyError("invalid audio bitrate")


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        validate_options(args)
        return args.handler(args)
    except ResidualMetadataError as exc:
        print(f"error={exc}", file=sys.stderr)
        print(f"residual_sensitive_field_count={total_sensitive(exc.counts)}", file=sys.stderr)
        for category in CATEGORY_ORDER:
            print(
                f"residual_{category}_fields={exc.counts[category]}",
                file=sys.stderr,
            )
        return 2
    except PrivacyError as exc:
        message = str(exc) if str(exc) else "local metadata operation failed"
        print(f"error={message}", file=sys.stderr)
        return 1
    except OSError:
        print("error=local metadata operation failed", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
