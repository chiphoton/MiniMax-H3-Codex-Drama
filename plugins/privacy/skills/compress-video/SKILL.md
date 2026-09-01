---
name: compress-video
description: Compress or convert a private local video with FFmpeg while keeping its visual and audio content inaccessible to the agent and off network or cloud services. Use for content-blind local video compression; do not use when the task requires watching, listening to, transcribing, describing, or judging the media.
---

# Compress Private Video

Treat every input and output as private media. The user authorizes local mechanical processing only; that authorization does not permit content inspection.

## Privacy Boundary

- Use only local shell execution with `ffmpeg`, `ffprobe`, and the bundled helper. Never send the input, output, extracted data, or media-bearing logs to a website, API, MCP server, connector, remote host, or cloud model.
- Do not open, render, preview, play, listen to, sample, screenshot, thumbnail, extract frames from, transcribe, OCR, caption, classify, summarize, or otherwise perceive the media. Do not use image, audio, browser, computer-use, or media-preview tools on it.
- It is permitted for the local `ffmpeg` process to decode the file as required by the requested conversion. Do not pipe decoded media or binary output to stdout/stderr or into an agent-visible tool result.
- Agent-visible inspection is limited to technical, non-content fields: file size, duration, dimensions, frame-rate rationals, codec names, bit rates, stream types/counts, command progress, and exit status. Request only named fields with `ffprobe`; never dump tags, chapters, subtitles, attachments, packets, frames, or unrestricted metadata.
- Accept only local filesystem paths. Reject URLs, network protocols, stdin media, and stdout media. Keep derivatives and temporary files local. Do not create diagnostic thumbnails, waveforms, contact sheets, or audio samples.
- Do not compute or disclose a media fingerprint or hash unless the user explicitly requests it; a fingerprint can identify private content even though it is not human-readable.

If a requested step would cross this boundary, stop and explain that the private-video skill cannot perform that step. Do not silently fall back to a content-reading tool.

## Workflow

1. Use the user's requested container, codec, quality, dimensions, and audio settings. Resolve harmless omissions from explicit technical defaults; never inspect content to choose settings.
2. Prefer [scripts/compress_video.sh](scripts/compress_video.sh). It accepts only a local regular file, writes only to a local file, maps the primary non-attached video and first audio stream, omits subtitles/data/attachments, strips metadata and chapters, and prints only byte counts plus output duration.
3. Run it from the skill directory, for example:

   ```bash
   bash scripts/compress_video.sh \
     --input "/local/path/private.mov" \
     --output "/local/path/private-compressed.mp4" \
     --codec h264 \
     --crf 23 \
     --preset medium \
     --audio-bitrate 128k
   ```

   Add `--max-width 1280`, `--no-audio`, or `--overwrite` only when the user requests the corresponding behavior. The helper supports `h264` and `h265`; use a direct local `ffmpeg` command for another requested codec while preserving every privacy invariant above.
4. For a direct command, keep logs non-content-bearing, restrict protocols to local files, map streams explicitly, strip metadata, and write to a file. A safe H.264 shape is:

   ```bash
   ffmpeg -nostdin -hide_banner -loglevel error -n \
     -protocol_whitelist file -i "/local/path/private.mov" \
     -map 0:V:0 -map "0:a:0?" -map_metadata -1 -map_chapters -1 -sn -dn \
     -c:v libx264 -crf 23 -preset medium -pix_fmt yuv420p \
     -c:a aac -b:a 128k -movflags +faststart \
     "/local/path/private-compressed.mp4" 2>/dev/null
   ```

   Suppress FFmpeg diagnostics rather than returning them to the agent; a malformed private file can place sensitive strings in an error. Use only the exit code and a generic failure message.

5. Verify only mechanical outcomes: command success, output existence, byte size, and narrowly selected technical fields. Do not assess visual or audio quality. If human quality judgment is needed, ask the user to inspect the local result themselves.

The helper refuses to overwrite by default and must never overwrite the input. It intentionally removes embedded metadata and unselected streams from the derivative; tell the user when that affects a preservation requirement.
