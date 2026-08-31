# Audio example gallery

These instructions apply to `examples/audio/`. They specialize the general `examples/AGENTS.md` rules for a flat audio-only collection and override its drama-specific `exp-NNN-*` directory, image, storyboard, poster, and video requirements. Continue to follow the parent rules for bilingual parity, relative links, privacy, append-only publication order, compact media, and final link verification.

## Purpose

Keep a curated, reproducible gallery of MiniMax H3 audio-only outputs. Each published case must let a reader identify the creative scenario, copy the exact prompt, inspect the meaningful generation parameters, and play or download the exact verified audio.

This folder is not a run archive. Do not add request payloads, workflow JSON, logs, ASR intermediates, QC WAV files, spectrograms, rejected takes, local paths, server details, timestamps, or account and creator metadata.

## Stable numbering and filenames

- Allocate the next unused three-digit index, starting at `001`.
- Never renumber, reorder, or reuse an existing published index.
- Store exactly one primary audio file per case at the collection root.
- Name it `<NNN>-<short-kebab-case-title>.flac`, for example `014-woman-calm-documentary.flac`.
- Keep the slug short, descriptive, lowercase, and stable. Do not encode model versions or parameter values in the filename.
- Append new cards after the last existing card in both README files.

## Required bilingual pair

Maintain `README.md` and `README_zh.md` together. They must contain the same cases in the same order with identical prompts, parameters, result facts, filenames, and links.

Translate reader-facing titles, descriptions, field labels, and link text naturally. Do not translate or rewrite the model prompt, filename, model identifier, node name, sampler, scheduler, seed, latent length, duration, sample rate, channel count, or format.

Keep the reciprocal language switch and same-language parent-gallery link at the top of each page.

## Card format

Use one outer HTML table per case so each entry renders as a card without custom CSS or JavaScript. Copy this structure and append it at the end:

```html
<table>
  <tr>
    <td>
      <h2>014 · 👩 Short descriptive title</h2>
      <p><strong>Parameters:</strong> Audio · Turbo · FL2VA INT8 ConvRot · 32×32 · length 124 · 6 steps · <code>MiniMaxH3TurboSampler</code> · <code>simple</code> · LoRA strength 1.0 · low VRAM off · denoise 1.0 · seed 2014</p>
      <p><strong>Result:</strong> 5.175 s · 32 kHz stereo · FLAC</p>
      <p><strong>Prompt</strong></p>
      <pre><code>Exact prompt payload, with dialogue tags HTML-escaped as &amp;lt;d&amp;gt;...&amp;lt;/d&amp;gt;.</code></pre>
      <audio controls preload="none" src="./014-woman-calm-documentary.flac"></audio>
      <p><a href="./014-woman-calm-documentary.flac">🔊 Play or download the FLAC</a></p>
    </td>
  </tr>
</table>
```

Every card must include:

1. Stable three-digit index, meaningful emoji, and concise title.
2. Exact mode and variant, model family, proxy size, latent length, sampling steps, sampler, scheduler, LoRA settings when applicable, denoise, and seed.
3. Measured output duration, sample rate, channel layout, and container/codec.
4. Exact prompt payload. Escape prompt dialogue tags as `&lt;d&gt;` and `&lt;/d&gt;` so they remain visible.
5. A non-autoplay `<audio controls preload="none">` player using the relative FLAC path.
6. A relative play/download link as the fallback for renderers that remove the HTML audio player.

If a case uses standard sampling, a different model, sampler, scheduler, step count, denoise, duration, channel layout, or format, state the exact actual value instead of copying Turbo defaults.

## Audio publication standard

- Preserve the exact selected generation output; do not normalize, denoise, resample, trim, or transcode it silently.
- Prefer the native lossless FLAC produced by `SaveAudio`.
- Before publication, confirm that the file decodes and record its measured duration, sample rate, and channel layout.
- For speech, compare an ASR transcript with the locked dialogue and listen for speaker, mood, and scenario fit.
- For non-speech cases, listen or inspect a spectrogram for requested event order and unwanted dialogue.
- Check integrated loudness, true peak, and clipped samples. Keep the raw example when it honestly represents the tested output, but document any material defect in the card rather than calling it mastered audio.
- Keep repository size practical. Ask before adding an unusually large or long file.

## Append checklist

1. Find the highest published index and allocate the next one.
2. Copy only the selected FLAC using the canonical filename.
3. Recover the exact submitted prompt and actual parameters from the retained workflow/history; do not reconstruct them from memory.
4. Append matching cards to `README.md` and `README_zh.md`.
5. Verify that every `<audio>` source and fallback link resolves with case-sensitive filenames.
6. Verify sequential IDs, English/Chinese parity, FLAC decoding, duration, sample rate, channel layout, and file size.
7. Check `git diff --check`, `git diff --stat`, and `git status --short` so no intermediates or unrelated files are included.
