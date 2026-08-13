<p align="center">
  <a href="../README.md">🎬 Example Gallery</a> ·
  <a href="README_zh.md">🌐 简体中文</a>
</p>

<h1 align="center">🏙️ Modern City Drama</h1>

<p align="center"><strong>A silent workplace exchange staged around a high-rise office presentation.</strong></p>

<p align="center">
  <a href="final.mp4"><img src="poster.webp" alt="Black title card for Modern City Drama with the Chinese title in white" width="100%"></a><br>
  <a href="final.mp4"><strong>▶️ Watch the compressed final video</strong></a>
</p>

| ⏱️ Duration | 📐 Format | 🎬 Mode | 🎚️ Profile | 🗣️ Language |
|---|---|---|---|---|
| 7.5 seconds | 16:9 · 1920×1080 · 24 fps | Guided | `commercial-ad` with project overrides | Chinese title and projected repository text · no dialogue, captions, or audio |

## 💬 Production conversation

<table>
  <tr>
    <td width="88" align="center" valign="top"><strong>👤<br>User</strong></td>
    <td valign="top">
      <strong>Normalized prompt</strong>
      <p>Create an approximately six-second, 16:9 cinematic workplace miniature using the two supplied character sheets as the only identity and wardrobe references. Keep both characters in one prosperous high-rise office with a large projection screen and no computer monitors. First show the secretary facing camera, presenting and pointing to the specified GitHub repository while her seated boss faces the screen; then cut to a frontal reverse angle where he applauds and gives a thumbs-up. Use exactly two continuous first/last-frame shot groups, place the exact Chinese title “现代都市剧” only in a standalone opening, and include no dialogue, voice-over, or captions.</p>
    </td>
  </tr>
</table>

<table>
  <tr>
    <td width="88" align="center" valign="top"><strong>🧠<br>Agent</strong></td>
    <td valign="top">
      <strong>Drama plan</strong>
      <p>Shape the film as three concise beats:</p>
      <ol>
        <li><strong>Title intro:</strong> isolate the exact Chinese title from all character footage.</li>
        <li><strong>Projection report:</strong> keep the secretary frontal, the boss side- or back-facing, and the repository readable during a held pointing gesture.</li>
        <li><strong>Approval reverse:</strong> center the boss as he completes the ordered action of applause followed by one thumbs-up.</li>
      </ol>
      <p>Keep a blue-and-gold office palette, preserve one spatial relationship across the hard cut, and avoid spoken mouth movement or unsupported product claims.</p>
    </td>
  </tr>
</table>

<table>
  <tr>
    <td width="88" align="center" valign="top"><strong>🎭<br>Agent</strong></td>
    <td valign="top">
      <strong>Entity sheet generation</strong>
      <p>The two supplied entity sheets were already the canonical identity and wardrobe sources, so they were reused unchanged rather than regenerated. Vera Lin was locked to long wavy dark-brown hair, a navy blazer, light top, gray pleated skirt, black tights, and black heels. Adrian Cho was locked to short black hair, a white shirt, black trousers, and black shoes.</p>
    </td>
  </tr>
</table>

<table>
  <tr>
    <td width="50%" align="center"><img src="entity/vera-lin-entity-sheet.webp" alt="Entity sheet for Vera Lin showing full-body rotations and facial close-ups in her office wardrobe" width="100%"><br><em>👩‍💼 Canonical female identity, hair, and presentation wardrobe</em></td>
    <td width="50%" align="center"><img src="entity/adrian-cho-entity-sheet.webp" alt="Entity sheet for Adrian Cho showing full-body rotations and facial close-ups in a white shirt and black trousers" width="100%"><br><em>👔 Canonical male identity, hair, and office wardrobe</em></td>
  </tr>
</table>

<table>
  <tr>
    <td width="88" align="center" valign="top"><strong>🏙️<br>Agent</strong></td>
    <td valign="top">
      <strong>Scene generation</strong>
      <p>Build one projection area inside a premium high-rise office: floor-to-ceiling windows, a dense glass-tower skyline, warm walnut panels, a large wall-mounted screen, a ceiling projector, and one executive chair. The empty screen provides a trackable plane for deterministic repository text, while the composition deliberately excludes desktop and laptop computers.</p>
    </td>
  </tr>
</table>

<p align="center">
  <img src="scene/highrise-projection-office-scene.webp" alt="Generated high-rise office scene with city windows, a projection screen, ceiling projector, and executive chair" width="100%"><br>
  <em>🌇 Scene master locking architecture, projection plane, daylight, and blue-gold tone</em>
</p>

<table>
  <tr>
    <td width="88" align="center" valign="top"><strong>🧩<br>Agent</strong></td>
    <td valign="top">
      <strong>Storyboard generation</strong>
      <p>Map the two continuous shot groups onto a 2×2 board. Panels A and B establish the frontal presentation and held pointing gesture; panels C and D reverse to the seated boss for applause and the final thumbs-up. The board locks identities, wardrobe, screen direction, exact projection placement, and the action order before animation.</p>
    </td>
  </tr>
</table>

<p align="center">
  <img src="storyboard/two-shot-pairs-storyboard.webp" alt="Four-panel storyboard showing the projection report, pointing hold, applause, and thumbs-up" width="100%"><br>
  <em>🎥 Two first/last-frame pairs progressing from presentation to approval</em>
</p>

<table>
  <tr>
    <td width="88" align="center" valign="top"><strong>🎞️<br>Agent</strong></td>
    <td valign="top">
      <strong>Video output</strong>
      <p>Animate the two first/last-frame groups, retain the valid presentation and approval takes, and assemble them after a deterministic 2.125-second black title intro. In the final revision, the title fades fully before the presentation, no title remains in either character shot, and the audio stream is removed to meet the requested complete silence. The 7.5-second H.264 master passed technical and visual QC.</p>
      <p><a href="final.mp4"><strong>▶️ Play the 7.5-second final master</strong></a></p>
    </td>
  </tr>
</table>

## 📦 Selected output

- 👩‍💼 [Vera Lin entity sheet](entity/vera-lin-entity-sheet.webp)
- 👔 [Adrian Cho entity sheet](entity/adrian-cho-entity-sheet.webp)
- 🏙️ [High-rise projection office scene](scene/highrise-projection-office-scene.webp)
- 🧩 [Two-pair storyboard](storyboard/two-shot-pairs-storyboard.webp)
- 🎞️ [Compressed final video](final.mp4)
