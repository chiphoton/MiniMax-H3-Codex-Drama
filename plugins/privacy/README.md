# Privacy Media

`privacy` provides content-blind, local-only image and video processing skills:

- `privacy:compress-video` converts or compresses a private video with FFmpeg.
- `privacy:slice-video` splits a private video into fixed-time segments and can read only narrow technical properties such as duration and FPS.
- `privacy:sanitize-metadata` audits and removes EXIF, GPS, author/device identifiers, timestamps, descriptions, hidden previews, and other embedded metadata without showing values to the agent.

## Important Privacy Reminder

> [!IMPORTANT]
> Do **not** drag and drop privacy-sensitive media files into the Codex chat box. Attaching a media file can upload its contents to a cloud server. Keep the media on local disk and refer to it by its local filename or, preferably, its absolute local path. This lets the skill pass that path to local processing commands without attaching or uploading the media itself.

For example, write a prompt like:

```text
Use privacy:compress-video to compress the private local video at
"/Users/me/Videos/private.mov" to "/Users/me/Videos/private-compressed.mp4"
with H.264 CRF 23. Do not inspect its content.
```

For slicing:

```text
Use privacy:slice-video to split the private local video at
"/Users/me/Videos/private.mp4" into 10-second files under
"/Users/me/Videos/private-parts". Do not inspect its content.
```

For metadata sanitization:

```text
Use privacy:sanitize-metadata to remove embedded private metadata from the
local image at "/Users/me/Pictures/private.jpg" and write the result to
"/Users/me/Pictures/private-sanitized.jpg". Do not reveal metadata values.
```

Referencing a path shares the path text with Codex, but not the media bytes. Avoid filenames containing sensitive descriptive information when even the path itself is confidential.

## Privacy Contract

These skills require agents to:

- run only local `ffmpeg`, `ffprobe`, ExifTool, ImageMagick, `file`, or bundled helpers;
- reject URLs, network media, stdin media, and stdout media;
- never preview, render, play, listen to, extract frames from, transcribe, OCR, classify, summarize, or otherwise perceive the media;
- never use browser, connector, MCP, API, or cloud services with the media;
- expose only selected non-content technical data such as duration, FPS, dimensions, codecs, bit rates, file size, segment count, and exit status;
- suppress raw tool diagnostics because malformed media can place private strings in error messages; and
- keep all derivatives on the local filesystem.

The bundled video defaults map the primary video and first audio stream, omit subtitles, attachments, and data streams, and strip metadata and chapters from generated files. State any stream-preservation requirements explicitly.

## Compression

The compression helper supports H.264 and H.265, CRF and preset controls, optional downscaling, optional audio removal, and guarded overwriting:

```bash
bash skills/compress-video/scripts/compress_video.sh \
  --input "/absolute/path/private.mov" \
  --output "/absolute/path/private-compressed.mp4" \
  --codec h264 \
  --crf 23 \
  --preset medium \
  --audio-bitrate 128k
```

It refuses to overwrite an existing output unless `--overwrite` is explicitly supplied and never permits the input and output to be the same file.

## Slicing

Safely inspect only permitted technical fields:

```bash
bash skills/slice-video/scripts/probe_video.sh \
  --input "/absolute/path/private.mp4"
```

Split into frame-aligned 10-second pieces using local re-encoding:

```bash
bash skills/slice-video/scripts/slice_video.sh \
  --input "/absolute/path/private.mp4" \
  --output-dir "/absolute/path/private-parts" \
  --segment-seconds 10 \
  --prefix part \
  --mode precise
```

Use `--mode copy` for faster, generation-loss-free stream copying. Copy-mode boundaries follow existing keyframes, so segment lengths may differ from the requested interval. The final segment in either mode may be shorter.

## Metadata Sanitization

Audit only privacy-category counts; raw values never leave the local helper process:

```bash
python3 skills/sanitize-metadata/scripts/sanitize_media.py audit \
  --input "/absolute/path/private.jpg"
```

Write a separate sanitized output without re-encoding where possible:

```bash
python3 skills/sanitize-metadata/scripts/sanitize_media.py sanitize \
  --input "/absolute/path/private.jpg" \
  --output "/absolute/path/private-sanitized.jpg"
```

Add `--deep` to decode/re-encode locally for stronger removal. Deep image mode uses ImageMagick and can be lossy; deep video mode produces H.264/AAC and can change HDR, color, audio, and stream characteristics. The helper verifies the output before publishing it and refuses to sanitize in place.

Metadata sanitization does not remove privacy information visible in pixels or audible in sound, including faces, text, license plates, watermarks, speech, or background details. It also does not detect steganography or erase previously uploaded copies.

## Requirements

- Local `ffmpeg`
- Local `ffprobe`
- Local ExifTool
- Local ImageMagick for `--deep` image sanitization
- Local `file`
- Bash
- Python 3

No network service or account is required.
