# Privacy Media

`privacy` provides content-blind, local-only video processing skills:

- `privacy:compress-video` converts or compresses a private video with FFmpeg.
- `privacy:slice-video` splits a private video into fixed-time segments and can read only narrow technical properties such as duration and FPS.

## Important Privacy Reminder

> [!IMPORTANT]
> Do **not** drag and drop privacy-sensitive media files into the Codex chat box. Attaching a media file can upload its contents to a cloud server. Keep the media on local disk and refer to it by its local filename or, preferably, its absolute local path. This lets the skill pass that path to local FFmpeg/FFprobe commands without attaching or uploading the media itself.

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

Referencing a path shares the path text with Codex, but not the media bytes. Avoid filenames containing sensitive descriptive information when even the path itself is confidential.

## Privacy Contract

These skills require agents to:

- run only local `ffmpeg`, `ffprobe`, or bundled shell helpers;
- reject URLs, network media, stdin media, and stdout media;
- never preview, render, play, listen to, extract frames from, transcribe, OCR, classify, summarize, or otherwise perceive the media;
- never use browser, connector, MCP, API, or cloud services with the media;
- expose only selected non-content technical data such as duration, FPS, dimensions, codecs, bit rates, file size, segment count, and exit status;
- suppress raw FFmpeg/FFprobe diagnostics because malformed media can place private strings in error messages; and
- keep all derivatives on the local filesystem.

The bundled defaults map the primary video and first audio stream, omit subtitles, attachments, and data streams, and strip metadata and chapters from generated files. State any stream-preservation requirements explicitly.

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

## Requirements

- Local `ffmpeg`
- Local `ffprobe`
- Bash

No network service or account is required.
