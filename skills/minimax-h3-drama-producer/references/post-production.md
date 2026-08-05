# Post-production

## Timeline contract

Store the selected edit in `edit/timeline.yaml`. Use JSON-compatible YAML unless a full YAML parser is already available. Keep paths relative to the project whenever possible.

Read [tool-contracts.md](tool-contracts.md) for the exact caption, audio, timeline, and QC configuration shapes.

The timeline contains:

- output width, height, frame rate, fit strategy, codec preset, quality, and duration;
- ordered clips with source path, trim start, duration, and incoming transition;
- optional full-frame PNG overlays with start and end times;
- an optional mastered audio file;
- final output path.

Use `scripts/assemble_timeline.py` for hard cuts and supported FFmpeg crossfades. The script locks output duration explicitly and uses finite overlay behavior; never allow looped image inputs to extend a render indefinitely.

## Voice and captions

Treat both features as `auto`, `on`, or `off`. User instructions outrank profile defaults.

Voice source priority:

1. supplied dialogue or voice reference;
2. configured high-quality local TTS;
3. disclosed system TTS fallback;
4. no generated voice when voice is optional.

Keep exact dialogue in a structured cue file. Preserve editable `.srt` or `.ass` whenever captions are enabled. Prefer FFmpeg `subtitles` only when libass and the requested font are available. Otherwise use `scripts/render_caption_overlays.py` to create transparent full-frame PNG overlays and include them in the timeline.

## Sound

Prefer user-cleared audio, useful H3 native audio, locally synthesized effects, and configured licensed libraries in that order. Record provenance. Do not download music silently.

Use `scripts/mix_audio.py` for deterministic placement, gain, mixing, and final loudness normalization. Preserve dialogue intelligibility, intentional silence, and transition sound bridges. A social master should normally target the active profile's integrated loudness and true-peak limit rather than maximize level.

## Export

Always render a versioned master before updating `final/master.mp4`. Use H.264 High Profile plus AAC for broad social delivery unless the user or profile requires another mezzanine or codec. Add `faststart` for MP4.

Generate profile-requested derivatives from the validated master rather than rebuilding the creative timeline separately. This keeps preview, cover, alternate ratio, and clean-master outputs traceable to one edit.
