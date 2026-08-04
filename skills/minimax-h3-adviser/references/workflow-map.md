# MiniMax H3 workflow map

Checked against fal.ai on 2026-08-04. Treat provider settings as changeable facts; verify again if the user asks for current API accuracy.

## Route by the role of the input

| User situation | Workflow | fal endpoint | ComfyUI template | Specialist |
|---|---|---|---|---|
| No media; H3 invents the whole clip | Text to video | `minimax/h3/text-to-video` | T2V | `minimax-h3-text-to-video` |
| One image is the literal first frame | First-frame animation | `minimax/h3/image-to-video` | I2V | `minimax-h3-frame-to-video` |
| Two images are literal first and last frames | First/last-frame transition | `minimax/h3/image-to-video` | I2V | `minimax-h3-frame-to-video` |
| Media supplies identity, design, style, motion, camera, rhythm, music, or voice | Reference to video | `minimax/h3/reference-to-video` | R2V | `minimax-h3-reference-to-video` |
| An existing video must change while unlisted content remains stable | Precise video edit | `minimax/h3/reference-to-video` | R2V reference-conditioned regeneration | `minimax-h3-video-editor` |

The asset's job decides the route. A portrait used as the literal opening composition is a first frame. The same portrait used only to preserve identity is a reference image.

The ComfyUI column is used only on explicit execution intent. The bundled official templates are T2V, I2V, and R2V; they do not provide a distinct surgical video-edit graph. A video-editor prompt therefore runs as R2V reference-conditioned regeneration and should not be described as pixel-stable source editing.

## Current fal.ai capability notes

- Output duration: 5–15 seconds.
- Resolution: `768P` or `2K`.
- Native stereo audio is part of the H3 workflow described by fal.
- Text-to-video fixed ratios in the current schema: `21:9`, `16:9`, `4:3`, `1:1`, `3:4`, `9:16`.
- Image-to-video follows the first-frame image's aspect ratio.
- Reference-to-video accepts those fixed ratios plus `adaptive`.
- Reference-to-video: up to 9 images, 3 videos, and 3 audio clips, with no more than 12 files total.
- Reference video clips: 2–15 seconds each and no more than 15 seconds combined.
- Reference audio clips: 2–15 seconds each and no more than 15 seconds combined.
- Audio cannot be the only reference type; include at least one image or video.
- fal's prompting guide reports a prompt capacity up to 7,000 characters. Prefer clarity over filling the limit.

## Routing examples

- “Make a clay fox leap over a canyon; I have no assets.” → Text to video.
- “Animate this poster exactly as the opening frame.” → Frame to video.
- “Start with this empty street and end exactly on this crowded street.” → Frame to video.
- “Use this portrait for the actor and this clip only for camera motion.” → Reference to video.
- “Replace the sign in this source clip but keep everything else.” → Video editor.
- “My character changed clothes halfway through the result.” → Diagnose, then route based on how identity or wardrobe was supplied.

## Cross-workflow prompt priorities

Apply this order when instructions compete:

1. Exact source-frame or source-video invariants.
2. Explicit user must-haves and exact quoted text/dialogue.
3. Reference assignments and exclusions.
4. Timed actions and camera path.
5. Look, texture, and atmosphere.
6. Generic quality language.

Remove or rewrite lower-priority instructions that contradict higher-priority ones.

## Sources

- fal prompting guide and examples: <https://fal.ai/learn/devs/minimax-h3-prompting-guide>
- fal text-to-video schema: <https://fal.ai/models/minimax/h3/text-to-video/api>
- fal image-to-video schema: <https://fal.ai/models/minimax/h3/image-to-video/api>
- fal reference-to-video schema: <https://fal.ai/models/minimax/h3/reference-to-video/api>
