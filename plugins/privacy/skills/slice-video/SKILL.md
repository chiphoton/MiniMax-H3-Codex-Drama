---
name: slice-video
description: Split a private local video into time-based files with FFmpeg while keeping its visual and audio content inaccessible to the agent and off network or cloud services. Use for content-blind local video slicing, including 10- or 15-second chunks; do not use for scene-aware, dialogue-aware, or visually selected cuts.
---

# Slice Private Video

Treat every input and output as private media. The user authorizes local mechanical processing only; that authorization does not permit content inspection.

## Privacy Boundary

- Use only local shell execution with `ffmpeg`, `ffprobe`, and the bundled helpers. Never send the input, outputs, extracted data, or media-bearing logs to a website, API, MCP server, connector, remote host, or cloud model.
- Do not open, render, preview, play, listen to, sample, screenshot, thumbnail, extract frames from, transcribe, OCR, caption, classify, summarize, or otherwise perceive the media. Do not use image, audio, browser, computer-use, or media-preview tools on it.
- It is permitted for local `ffmpeg`/`ffprobe` processes to read or decode the file as required for technical probing and slicing. Never emit decoded media, binary data, subtitles, packets, frame dumps, thumbnails, waveforms, or audio samples to stdout/stderr or an agent-visible result.
- Agent-visible inspection is limited to technical, non-content fields: file size, duration, dimensions, frame-rate rationals, codec names, bit rates, stream types/counts, requested segment length, segment count, and exit status. Never dump tags, chapters, attachments, subtitle text, or unrestricted metadata.
- Accept only local filesystem paths. Reject URLs, network protocols, stdin media, and stdout media. Keep all segments local.
- Time-based cuts are allowed. Scene-, face-, action-, silence-, speech-, beat-, or dialogue-based cuts require content analysis and are forbidden under this skill.

If a requested step would cross this boundary, stop and explain that the private-video skill can only make content-blind time cuts. Do not silently fall back to a content-reading tool.

## Safe Technical Probe

Use [scripts/probe_video.sh](scripts/probe_video.sh) when duration, FPS, dimensions, codecs, or stream types are useful:

```bash
bash scripts/probe_video.sh --input "/local/path/private.mp4"
```

The helper selects only named technical fields. Do not replace it with unrestricted `ffprobe -show_format`, `-show_streams`, `-show_frames`, or `-show_packets` output. Duration and average frame-rate are enough to estimate `ceil(duration / segment_seconds)` chunks without inspecting content.

The helpers suppress FFmpeg/FFprobe diagnostics and return generic failures because malformed private media can place sensitive strings in an error. Do not expose or upload raw diagnostics to troubleshoot a private file.

## Slice Workflow

1. Use the segment duration requested by the user, such as 10 or 15 seconds. Do not infer cut points from content.
2. Choose the mechanical mode:

   - `precise`: locally re-encodes the primary video and first audio stream to H.264/AAC, forces keyframes at the requested interval, and produces frame-aligned chunks. Use when approximately equal fixed-length pieces are the priority. Boundaries are limited by frame timing and the final segment may be shorter.
   - `copy`: preserves encoded streams without generation loss and is much faster, but cuts at existing keyframes, so segment lengths can differ from the requested interval. Use when the user prioritizes stream copy, speed, or no re-encoding, and state this boundary caveat.

3. Prefer [scripts/slice_video.sh](scripts/slice_video.sh). For frame-aligned 10-second MP4 pieces:

   ```bash
   bash scripts/slice_video.sh \
     --input "/local/path/private.mp4" \
     --output-dir "/local/path/private-parts" \
     --segment-seconds 10 \
     --prefix part \
     --mode precise
   ```

   For keyframe-aligned stream copy, use `--mode copy`; choose an extension compatible with the source codecs, such as `--extension mkv` when appropriate. The helper refuses an output prefix that already has matching files, preventing stale private segments and accidental replacement.
4. The helpers map the primary non-attached video plus first audio stream, omit subtitles/data/attachments, and strip metadata and chapters. If the user requires other streams or a different codec/container, formulate a direct local `ffmpeg` command with explicit mappings while preserving every privacy invariant above.
5. Verify only mechanical outcomes: process success, technical duration/FPS, requested interval, output count, and optionally each segment's duration through the safe probe. Never inspect a segment's visual or audio content.

Tell the user whether the result used `precise` or `copy` mode and where the local segments were written. Do not claim scene quality, continuity, or perceptual correctness.
