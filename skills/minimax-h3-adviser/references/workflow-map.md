# MiniMax H3 workflow map

## Route by the role of the input

| User situation | Workflow | ComfyUI template | Specialist |
|---|---|---|---|
| No media; H3 invents the whole clip | Text to video | T2V | `minimax-h3-text-to-video` |
| One image is the literal first frame | First-frame animation | I2V | `minimax-h3-frame-to-video` |
| Two images are literal first and last frames | First/last-frame transition | I2V | `minimax-h3-frame-to-video` |
| Media supplies identity, design, style, motion, camera, rhythm, music, or voice | Reference to video | R2V | `minimax-h3-reference-to-video` |
| An existing video must change while unlisted content remains stable | Precise video edit | R2V reference-conditioned regeneration | `minimax-h3-video-editor` |

The asset's job decides the route. A portrait used as the literal opening composition is a first frame. The same portrait used only to preserve identity is a reference image.

The ComfyUI column is used only on explicit execution intent. The bundled official templates are T2V, I2V, and R2V; they do not provide a distinct surgical video-edit graph. A video-editor prompt therefore runs as R2V reference-conditioned regeneration and should not be described as pixel-stable source editing.

## Provider-neutral starting settings

- Output duration: prefer 5–15 seconds per generated clip.
- Resolution: use `768P` for faster iteration or `2K` for a final pass when the active workflow and hardware support it.
- Text-to-video ratios: start with `21:9`, `16:9`, `4:3`, `1:1`, `3:4`, or `9:16`.
- Image-to-video: follow the first-frame image's aspect ratio.
- Reference-to-video: use a fixed ratio or `adaptive` when the installed workflow supports it.
- Multimodal complexity budget: prefer no more than 9 images, 3 videos, 3 audio clips, or 12 files total.
- Reference video and audio: prefer 2–15 seconds per clip and no more than 15 seconds combined per modality.
- Do not use audio as the only reference type; include at least one image or video.
- Native audio can be directed with picture. Verify the installed workflow before promising a stream layout.
- Prefer prompt clarity over filling a large prompt capacity.

These values are production heuristics, not a remote API contract. The executor must validate the installed local workflow and models.

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
