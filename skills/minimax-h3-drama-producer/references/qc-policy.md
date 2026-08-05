# QC policy

## Hard gates

Do not mark delivery complete when any applicable hard gate remains:

- the master does not exist, cannot be probed, or fails a complete decode;
- a required shot, subject, product, message beat, or CTA is missing;
- width, height, aspect ratio, frame rate, duration, codec, or stream layout violates the resolved profile;
- identity, product geometry, environment, wardrobe, key prop, screen direction, or continuity has a conspicuous incorrect change;
- a caption is unreadable, mistimed, or outside the declared safe area;
- audio clips, exceeds the true-peak ceiling, loses required dialogue, or has an invalid stream;
- an unintended black or frozen interval exceeds the profile threshold.

Repair deterministic edit defects first. Retry a generative shot only when the defect originates in that shot and the take budget permits it.

## Soft warnings

Allow delivery with an explicit warning for non-blocking defects such as brief hand deformation, minor background drift, small reflection mismatch, or a less-natural secondary motion. Never relabel a hard gate as a warning to finish sooner.

## Required checks

Run `scripts/qc_media.py` to produce:

- FFprobe stream and format metadata;
- a full decode result;
- expected dimension, frame-rate, duration, and audio checks;
- black-frame and freeze candidates;
- integrated loudness, loudness range, and true peak when audio exists;
- a whole-film contact sheet;
- machine-readable and Markdown reports.

Then inspect the contact sheet and any shot-level sheets. Review narrative order, entity fidelity, composition, transitions, caption safe areas, and end-state continuity. Record this visual review in the report; a pending visual review is not a complete QC pass.

Record the result with `scripts/record_visual_qc.py`, providing one `--check` for each class actually inspected. Use `--hard-failure` for a visual hard gate and `--warning` for an allowed soft defect. The helper updates both report formats and computes the overall result from technical and visual outcomes.

## Default numeric policy

Use the active profile values. In the absence of a stricter value:

- duration tolerance: 0.10 seconds;
- frame-rate tolerance: 0.01 fps;
- true peak ceiling: -1.0 dBTP;
- social integrated loudness target: -14 LUFS with ±1 LU tolerance;
- unintended black interval: 0.25 seconds;
- unintended freeze interval: 1.0 second, excluding a declared ending hold.

Store objective measurements separately from interpretation. Include the exact tool command or version in logs when a failure is difficult to reproduce.
