# Deterministic tool contracts

All configuration files may use JSON-compatible YAML. Relative media paths resolve from the configuration file's directory.

## Caption overlays

```json
{
  "width": 1080,
  "height": 1920,
  "font_size": 56,
  "max_lines": 2,
  "top_safe_pct": 12,
  "bottom_safe_pct": 18,
  "cues": [
    {
      "id": "S01-line-1",
      "start": 0.7,
      "end": 4.2,
      "text": "Exact caption text",
      "highlight_terms": ["caption"],
      "position": "bottom"
    }
  ]
}
```

Run `render_caption_overlays.py`; add the resulting PNG paths and time ranges to the timeline overlays.
Safe-area values use percentages from 0 to 100; decimal fractions from 0 to 1 remain accepted for backward compatibility.

## Audio mix

```json
{
  "duration": 12.0,
  "sample_rate": 48000,
  "channel_layout": "stereo",
  "output": "../audio/mix/master.wav",
  "target_lufs": -14,
  "true_peak_db": -1.5,
  "tracks": [
    {"path": "../audio/dialogue/line-01.wav", "start": 0.5, "gain_db": 0},
    {"path": "../audio/music/bed.wav", "start": 0, "gain_db": -12}
  ]
}
```

Each track may add `trim_start` and `duration`. Run `mix_audio.py` before picture assembly.

## Picture timeline

```json
{
  "output": "../final/master-v001.mp4",
  "video": {"width": 1080, "height": 1920, "fps": 24, "fit": "crop", "preset": "medium", "crf": 18},
  "audio_master": "../audio/mix/master.wav",
  "clips": [
    {"path": "../clips/selected/S01.mp4", "trim_start": 0, "duration": 5},
    {"path": "../clips/selected/S02.mp4", "trim_start": 0, "duration": 5, "transition": {"type": "fadewhite", "duration": 0.08}}
  ],
  "overlays": [
    {"path": "../subtitles/overlays/001.png", "start": 0.7, "end": 4.2, "x": 0, "y": 0}
  ]
}
```

The transition belongs to the incoming clip. Supported transitions are cut, fade, fadeblack, fadewhite, directional wipes, and directional slides. The assembler uses finite overlay behavior and an explicit output duration.

The audio mixer, TTS adapter, and timeline assembler refuse to replace an existing output by default. Prefer a new versioned path. Use `--replace` only when intentionally updating a stable selected artifact after preserving its versioned source.

## QC

```bash
python3 scripts/qc_media.py \
  --input <project>/final/master.mp4 \
  --output-dir <project>/qc \
  --media-info-output <project>/final/media-info.json \
  --expected-width 1080 --expected-height 1920 \
  --expected-fps 24 --expected-duration 43.5 \
  --target-lufs -14 --true-peak-ceiling -1.0
```

The script completes technical checks and leaves visual review as `pending`. Inspect the contact sheet and update the QC report before declaring completion.

```bash
python3 scripts/record_visual_qc.py \
  --qc-dir <project>/qc --status pass \
  --check "Identity and wardrobe remain stable" \
  --check "Narrative order, transitions, and caption safe areas are correct"
```

Use `--hard-failure` or `--warning` to preserve visual findings in both JSON and Markdown reports.
