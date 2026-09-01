---
name: sanitize-metadata
description: Audit and remove embedded metadata, EXIF, GPS, author/device identifiers, timestamps, descriptions, and hidden previews from private local images or videos without exposing metadata values or media content to the agent or cloud services. Use for content-blind local metadata sanitization; do not use for visible watermarks, faces, text, speech, or other privacy information embedded in the pixels or audio.
---

# Sanitize Private Media Metadata

Treat the media and every metadata value as private. The user authorizes local mechanical inspection and rewriting only; that authorization does not permit the agent to see the media or raw metadata.

## Privacy Boundary

- Ask for a local filename or absolute path. Never ask the user to drag and drop or attach private media to the Codex chat box.
- Use only local shell execution and [scripts/sanitize_media.py](scripts/sanitize_media.py), which invokes local ExifTool, FFmpeg, ImageMagick, and `file` as needed. Never send the file, metadata, logs, or derivatives to a website, API, MCP server, connector, remote host, or cloud model.
- Do not preview, render, play, listen to, extract frames from, thumbnail, transcribe, OCR, caption, classify, summarize, or otherwise perceive the media.
- Never print raw EXIF/XMP/IPTC/QuickTime metadata, GPS coordinates, names, device identifiers, timestamps, comments, thumbnails, or diagnostic output. The helper captures those values inside a local process and returns only category counts and pass/fail status.
- Accept local regular files only. Reject URLs, network protocols, stdin media, and stdout media. Never sanitize in place; write to a separate local output path.
- Do not compute or disclose media hashes or fingerprints unless the user explicitly requests them.

If a requested step crosses this boundary, stop. Do not fall back to a content-reading or cloud tool.

## Audit

Run a value-blind audit before removal when the user asks what kinds of private metadata are present:

```bash
python3 scripts/sanitize_media.py audit \
  --input "/local/path/private.jpg"
```

The safe report contains only the media family, whether common sensitive metadata is present, and counts for location, identity, timestamp, device, description, identifier, and embedded-preview categories. Do not replace this with raw `exiftool`, `ffprobe -show_format`, or `ffprobe -show_streams` output.

## Sanitize

Use a distinct output path. Standard mode removes recognized metadata without re-encoding media payloads where possible:

```bash
python3 scripts/sanitize_media.py sanitize \
  --input "/local/path/private.jpg" \
  --output "/local/path/private-sanitized.jpg"
```

For stronger sanitization, add `--deep`:

```bash
python3 scripts/sanitize_media.py sanitize \
  --input "/local/path/private.mov" \
  --output "/local/path/private-sanitized.mp4" \
  --deep
```

- Standard image mode copies the encoded image and uses ExifTool to remove all writable embedded metadata. It is generation-loss-free, but deleting EXIF Orientation and color profiles can change display orientation or color rendering.
- Deep image mode uses local ImageMagick to bake orientation into pixels, decode/re-encode, strip profiles and metadata, then applies ExifTool again. JPEG/WebP output defaults to quality 95 and is lossy.
- Standard video mode remuxes the primary video and first audio stream with stream copy, drops subtitles/data/attachments and chapters, strips container/stream metadata, then applies ExifTool. Codec-level side data may remain.
- Deep video mode re-encodes the primary video and first audio stream to H.264/AAC before the final ExifTool pass. This is more thorough but lossy and can change HDR, color, audio, and stream characteristics.

Use `--overwrite` only when the user explicitly authorizes replacing an existing output. The helper writes atomically and keeps an existing output unchanged if processing or verification fails.

## Verification and Limits

The helper audits the private categories before and after sanitization and refuses to publish the output if common sensitive fields remain. Report only the safe summary and the chosen `standard` or `deep` level. Do not claim forensic certainty.

This skill removes embedded metadata; it does not remove visible faces, text, license plates, burned-in timestamps, watermarks, spoken names, background details, steganography, filenames, filesystem timestamps outside the generated file, backups, or previously uploaded copies. Those require a different workflow and may require content access that this skill forbids.
