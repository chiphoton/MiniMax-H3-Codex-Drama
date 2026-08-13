# Featured example gallery

These instructions apply to `examples/` and every example directory beneath it.

## Purpose

`examples/` is a curated, lightweight showcase of dramas made with this project. It is not an archive of complete production runs. Commit only the selected visual sources of truth and the compressed final video needed to explain a featured example.

Keep two levels of documentation in sync:

- `examples/README.md` and `examples/README_zh.md` are the English and Simplified Chinese gallery entry points.
- `examples/<exp-X>/README.md` and `examples/<exp-X>/README_zh.md` are the English and Simplified Chinese transcript-like production stories for one example.

The English and Chinese pages are a required pair. Add or update them together, keep their facts and media selections equivalent, and put a reciprocal language switch at the top of every page:

```html
<!-- README.md -->
<p align="center">
  <a href="README_zh.md">🌐 简体中文</a>
</p>

<!-- README_zh.md -->
<p align="center">
  <a href="README.md">🌐 English</a>
</p>
```

The relative switch above works at both hierarchy levels because each language pair lives in the same directory. Translate reader-facing titles, briefs, captions, stage summaries, link labels, and alt text; do not translate filenames, paths, technical identifiers, or factual values.

Do not publish production dates or timestamps, author names, creator identities, account names, local source paths, workstation details, or authorship metadata. These details do not help readers understand an example and may leak private information.

Use stable directory names such as `exp-001-short-title`, `exp-002-short-title`, and so on. Do not renumber an example after its link has been published.

## Canonical reference implementation

Treat the first published example as the visual and structural reference for all later examples:

- Gallery card: `examples/README.md` and `examples/README_zh.md`
- Detail page: `examples/exp-001-jiangnan-ancient-drama/README.md` and `README_zh.md`

Reuse their page hierarchy, HTML-table treatment, spacing, image placement, emoji vocabulary, action-link placement, and English/Chinese parity. Replace the story-specific content and media; do not redesign the page for each new example. Small improvements to the shared pattern are allowed only when they are applied consistently to the gallery and every affected example in both languages.

## Required directory shape

Use this as the default shape, omitting only assets that genuinely do not help tell the example:

```text
examples/
├── README.md
├── README_zh.md
├── AGENTS.md
└── exp-001-short-title/
    ├── README.md
    ├── README_zh.md
    ├── poster.webp
    ├── final.mp4
    ├── entity/
    │   └── entity-sheet-01.webp
    ├── scene/
    │   └── scene-01.webp
    └── storyboard/
        └── storyboard-01.webp
```

Every example directory must contain the `entity/`, `scene/`, and `storyboard/` subdirectories. Keep the poster, compressed final video, and detail README at the example root. Each asset subdirectory may contain a few numbered, selected showcase images; if a stage has no published asset, keep its directory with a `.gitkeep` file and explain the omission in the detail README. Do not copy the original output tree, workflow JSON, prompts ledger, logs, rejected takes, raw keyframes, unselected clips, or other intermediate files into `examples/`.

## Gallery README

After their language switches, `examples/README.md` and `examples/README_zh.md` must begin with a short explanation that these are selected outputs and that media is compressed for repository viewing. Then present the examples in a consistent card-like grid or list.

Match the root README's emoji-rich presentation. Use relevant emoji in the page title, major section headings, gallery metadata, and action links so the gallery feels like part of the same project. Suitable recurring labels include `🎬 Example Gallery`, `🎭 Drama`, `📝 Brief`, `🖼️ Poster`, `▶️ Watch`, and `✨ View production story`; translate the words in `README_zh.md` while keeping the visual vocabulary consistent.

Every example entry must include:

1. Drama title.
2. A one- or two-sentence brief.
3. One representative image for each of four ordered categories: poster, entity sheet, scene, and storyboard. If a category has multiple published images, choose only one for the gallery card.
4. Meaningful translated labels and alt text for all four images.
5. A clearly labeled final-video preview or link.
6. A link to the same-language detail page; clicking any of the four images should also open it. English gallery entries link to `./<exp-X>/README.md`, and Chinese gallery entries link to `./<exp-X>/README_zh.md`.

Use relative repository links. Keep cards visually consistent and make the entire gallery readable on GitHub without external scripts, CSS, or hosted assets. Use one full-width outer HTML table per example, matching the first gallery entry. Each card contains, in order: an emoji-led title, the brief, a centered translated category legend, a centered inline flow of four selected images linked to the same-language detail page, then a centered line with the video action and production-story action. Give every preview a numeric `width="250"` rather than a percentage width. Inline images can wrap naturally as the GitHub content area narrows, avoiding the horizontal scrollbar produced by a nested four-column table. Preserve the poster/entity/scene/storyboard source order so the legend stays meaningful after wrapping. If embedded local video is unreliable in the target renderer, the four selected images are the preview and the prominent watch link opens the MP4.

Follow this card skeleton in both languages:

```html
<table>
  <tr>
    <td>
      <h2>🎭 Example title</h2>
      <p>One- or two-sentence brief.</p>
      <p align="center"><strong>🖼️ Poster · 🎭 Entity sheet · 🏙️ Scene · 🧩 Storyboard</strong></p>
      <p align="center">
        <a href="./exp-NNN-short-title/README.md"><img src="./exp-NNN-short-title/poster.webp" alt="Descriptive poster text" title="Poster" width="250"></a>
        <a href="./exp-NNN-short-title/README.md"><img src="./exp-NNN-short-title/entity/entity-sheet-01.webp" alt="Descriptive entity sheet text" title="Entity sheet" width="250"></a>
        <a href="./exp-NNN-short-title/README.md"><img src="./exp-NNN-short-title/scene/scene-01.webp" alt="Descriptive scene text" title="Scene" width="250"></a>
        <a href="./exp-NNN-short-title/README.md"><img src="./exp-NNN-short-title/storyboard/storyboard-01.webp" alt="Descriptive storyboard text" title="Storyboard" width="250"></a>
      </p>
      <p align="center">
        <a href="./exp-NNN-short-title/final.mp4">▶️ Watch the compressed final video</a> ·
        <a href="./exp-NNN-short-title/README.md">✨ View the production story</a>
      </p>
    </td>
  </tr>
</table>
```

For the Chinese card, translate visible copy and alt text, and change both detail links to `README_zh.md`. Keep asset paths unchanged.

Keep entries in publication order and append every new example after the existing cards. Do not insert a new example at the top or reorder published entries unless a maintainer explicitly requests editorial ordering. When adding, renaming, or removing an example, update the gallery in the same change and verify every image, detail-page, and video link.

## Per-example README

Write both `examples/<exp-X>/README.md` and `examples/<exp-X>/README_zh.md` as compact chatbot-style conversations. They should show what the user asked for and how the production progressed, rather than reading like generic case studies.

Use this page order without rearranging it:

1. Centered navigation: same-language gallery link first, reciprocal language switch second.
2. Centered emoji-led title and one-line brief.
3. Full-width poster linked to `final.mp4`, followed by a centered watch action.
4. Compact Markdown facts table: duration, aspect ratio/resolution, frame rate, production profile, mode, and language/dialogue treatment. Do not include production dates or authorship information.
5. `## 💬 Production conversation` and the six messages below.
6. `## 📦 Selected output` with links to every published showcase asset.

Use these exact navigation targets:

```html
<!-- English detail page -->
<p align="center">
  <a href="../README.md">🎬 Example Gallery</a> ·
  <a href="README_zh.md">🌐 简体中文</a>
</p>

<!-- Chinese detail page -->
<p align="center">
  <a href="../README_zh.md">🎬 示例画廊</a> ·
  <a href="README.md">🌐 English</a>
</p>
```

Then show these messages in this exact order:

1. **👤 User · Normalized prompt**
2. **🧠 Agent · Drama plan**
3. **🎭 Agent · Entity sheet generation**
4. **🏙️ Agent · Scene generation**
5. **🧩 Agent · Storyboard generation**
6. **🎞️ Agent · Video output**

Use the same two-column HTML table for every message. The speaker cell is `width="88"`, centered, and top-aligned; it contains the stage emoji, a line break, and `User`/`Agent` or `用户`/`Agent`. The content cell is top-aligned and begins with a bold stage title. Use short paragraphs and an ordered or unordered list only when it improves scanning. Do not add custom CSS or JavaScript.

```html
<table>
  <tr>
    <td width="88" align="center" valign="top"><strong>🧠<br>Agent</strong></td>
    <td valign="top">
      <strong>Drama plan</strong>
      <p>Concise, observable decisions and actions.</p>
    </td>
  </tr>
</table>
```

Place selected media immediately after the message that produced or locked it. Show two entity sheets side by side in a 50/50 HTML table. Show a scene or storyboard as one centered, full-width image. Put a short italic emoji-led caption directly below each image. Do not place the same large image again in the output summary.

Use emoji throughout both language versions in the same spirit as the root README: add them to the page title, major headings, facts row, chatbot stage labels, media captions, output summary, back link, language switch, and final-video action. Keep each emoji semantically meaningful and keep equivalent sections visually consistent between English and Chinese. Prefer one leading emoji per heading or label; do not decorate every sentence, repeat long emoji strings, or replace accessible text with emoji alone.

For each agent stage:

- State the stage goal and the important production decisions in a few sentences or bullets.
- Show only the selected compressed artifact(s) that best explain the result.
- Add a short caption identifying what the artifact demonstrates, such as character continuity, location lock, shot progression, or final assembly.
- Say when a stage has no published asset instead of inventing or backfilling one.
- Keep artifact names and terminology consistent with the project (`entity sheet`, `scene`, `storyboard`, and `final video`).
- Be precise about provenance without revealing identity: if an entity sheet or other artifact was supplied and reused unchanged, say so instead of implying that the agent generated it.

The normalized prompt should preserve the user's creative intent, explicit constraints, requested format, and important references while removing conversational noise. Redact personal data, credentials, private paths, and licensed or confidential source details. Do not present hidden chain-of-thought, system/developer prompts, private tool traces, raw logs, or exhaustive internal reasoning. Describe observable actions, decisions, and outputs instead.

End with a compact output summary linking the final video and any selected showcase assets already displayed on the page. Avoid duplicating large media embeds.

The English and Chinese detail pages must have the same sections, stage order, facts, media, and link destinations. Translation should read naturally rather than mirror English word order, but it must not add or omit factual claims.

## Media selection and compression

Repository size is a first-class constraint.

- Publish only representative entity sheets in `entity/`, scene images in `scene/`, storyboard images in `storyboard/`, plus the poster and final video at the example root.
- Prefer WebP for showcase images; use JPEG only when it is materially smaller at comparable visual quality. Avoid PNG unless transparency or lossless detail is essential.
- Resize images to the largest dimensions actually useful in a README. As a default, use a long edge around 1600 px and aim for no more than 1 MB per image.
- Encode final video as broadly playable H.264/AAC MP4 with `yuv420p` pixel format and fast-start metadata. Preserve the intended aspect ratio and keep the smallest bitrate that still represents the work honestly.
- Aim for a final video under 20 MB. If that would make the example visibly misleading, document the tradeoff and ask before committing a much larger file.
- Remove unnecessary metadata and confirm that audio, captions, orientation, and duration survived compression.
- Never overwrite or modify the source production artifacts while preparing showcase media; create compressed copies in the example directory.

Do not add animated GIF previews by default; they are usually much larger and lower quality than the compressed MP4. Do not rely on external CDNs, expiring URLs, or local absolute paths.

## Adding or updating an example

1. Inspect the source production and choose the smallest set of artifacts that tells the story.
2. Allocate the next unused stable `exp-NNN-short-title` directory.
3. Create compressed copies of the selected media and inspect the compressed results.
4. Write both per-example README language versions using the six-message sequence above, including reciprocal language switches.
5. Append or update the corresponding four-preview responsive gallery card in both `examples/README.md` and `examples/README_zh.md`, including reciprocal language switches.
6. Open all four README files in a GitHub-compatible renderer when possible. At minimum, verify language switches, same-language navigation, relative paths, content parity, case-sensitive filenames, image dimensions, video playback, file sizes, and mobile-readable layout.
7. Check `git diff --stat` and `git status --short` so no raw production artifacts or unrelated files are accidentally included.

When updating an existing example, preserve its directory name and public links. Keep historical claims accurate; do not silently replace the featured video with a materially different cut without updating the brief, stage notes, facts, poster, and gallery entry.

## Writing and quality bar

- Write concise, specific English in `README.md` and natural Simplified Chinese in `README_zh.md`.
- Keep both README levels visually consistent with the root README's emoji-rich style and with each other.
- Describe what is visible and produced; do not make unsupported quality or performance claims.
- Give every image useful alt text and every video a descriptive link label.
- Avoid autoplay, huge inline images, decorative badges, and repeated marketing copy.
- Keep titles, filenames, captions, and links deterministic so later agents can append examples without redesigning earlier entries.
- Do not commit an example until its English and Chinese detail pages and gallery entries are all complete.

If a requested layout cannot be expressed reliably in GitHub-flavored Markdown/allowed HTML, pause and discuss the presentation tradeoff before introducing generated site code or external hosting.
