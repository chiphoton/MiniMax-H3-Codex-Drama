# MiniMax H3 prompt language palette

Use this as a choice menu, not a checklist. Offer only 3–6 candidates relevant to the current unknown, explain their effect in plain language, and recommend one.

## Visual preview map

Each atlas is optional. Show one only when it makes the user's choice easier. Resolve the path to an absolute path before embedding it in chat.

| Choice family | Preview asset | Cell order |
|---|---|---|
| Framing | `../assets/framing-atlas.png` | upper-left extreme close-up; upper-right close-up; lower-left medium; lower-right wide |
| Lens feel | `../assets/lens-atlas.png` | left wide-angle; center natural; right long-lens |
| Lighting | `../assets/lighting-atlas.png` | upper-left soft; upper-right hard side; lower-left rim; lower-right neon |
| Visual texture | `../assets/texture-atlas.png` | upper-left clean; upper-right 35 mm; lower-left phone; lower-right VHS |
| Camera motion | `../assets/camera-motion-atlas.png` | upper-left push-in; upper-right pull-back; lower-left tracking; lower-right orbit |
| Transitions | `../assets/transition-atlas.png` | upper-left match; upper-right whip; lower-left rack focus; lower-right physical wipe |

The sheets intentionally contain no embedded text. Pair the candidate names in the response with the stated cell positions; each cell acts as its preview thumbnail. Do not use visual previews for audio, performance, or constraints.

## Framing

| Candidate | Visible effect | Best when |
|---|---|---|
| Extreme close-up | Isolates a tiny detail; intense and tactile | Eyes, product mechanisms, texture, a reveal detail |
| Close-up | Prioritizes face or hero object | Emotion, dialogue, beauty, product detail |
| Medium shot | Balances expression with hands and gesture | Performance, interaction, demonstrations |
| Wide shot | Makes environment and spatial action legible | Establishing scale, choreography, atmosphere |

## Lens feel

| Candidate | Visible effect | Tradeoff |
|---|---|---|
| Wide-angle perspective | Expands depth and makes movement toward camera feel fast | Can distort faces near frame edges |
| Natural-lens perspective | Feels neutral and observational | Less stylized or dramatic |
| Long-lens compression | Flattens depth, isolates the subject, softens background | Makes large spatial movement feel smaller |

Prefer “lens feel” over claiming an exact focal length unless the user is deliberately directing cinematography.

## Camera motion

| Candidate | Visible effect | Avoid when |
|---|---|---|
| Locked-off | Stable frame; movement happens within composition | The scene needs an active reveal |
| Slow push-in | Gradually increases focus or tension | The ending needs more environmental context |
| Pull-back reveal | Starts intimate and exposes scale or context | Identity detail must stay dominant |
| Tracking shot | Travels with the subject | Subject path is unclear |
| Orbit | Reveals form around a person or product | Background continuity is fragile |
| Handheld follow | Feels immediate, documentary, or phone-captured | Premium polish or geometric precision is essential |
| Whip pan | Creates a fast directional transition | Legibility and gentle pacing matter |

Choose one principal motion per beat. Do not combine `locked-off` with movement instructions for the same camera and beat.

## Lighting

| Candidate | Visible effect | Best when |
|---|---|---|
| Soft diffused light | Gentle transitions, flattering skin and products | Natural portraits, calm ads, quiet drama |
| Hard side light | Deep shape and contrast; heightened tension | Noir, athletic products, dramatic reveals |
| Backlight with rim | Separates silhouette and catches haze, hair, or edges | Atmosphere, heroic entrances, translucent materials |
| Practical neon | Colored light appears motivated by visible fixtures | Night streets, clubs, cyber styling |
| High-key | Bright, low-shadow, clean and optimistic | Beauty, lifestyle, UI/product clarity |
| Low-key | Dark frame with selective highlights | Mystery, luxury, suspense |

## Visual texture

| Candidate | Visible effect | Best when |
|---|---|---|
| Clean commercial | Controlled highlights, crisp materials, minimal noise | Products, fashion, premium brand work |
| 35 mm film character | Fine grain, soft highlight halation, restrained color | Nostalgia, cinema, fashion campaigns |
| Documentary phone capture | Autofocus hesitation, exposure breathing, subtle hand tremor | Authenticity, found moments, social clips |
| Analog/VHS grunge | Scanlines, chromatic offset, gate jitter, signal interruption | Music visuals, retro or underground styling |
| Graphic motion design | Flat fields, masks, grids, sharp typography choreography | Titles, posters, UI, brand graphics |

Use only a few compatible texture cues. A long stack of unrelated artifacts reads as noise rather than style.

## Transitions

| Candidate | Visible effect | Prompt as |
|---|---|---|
| Hard cut | Immediate change and strong pace | Name the exact cut point or impact |
| Match transition | One shape, texture, or motion becomes another | Describe the shared visual feature and continuous camera path |
| Whip transition | Blur hides the cut during fast directional motion | State direction, peak blur, then the settle |
| Rack-focus reveal | Attention moves between depth planes | Name foreground, background, and focus timing |
| Physical wipe | An object crosses frame and hides the edit | Name the occluding object and reveal behind it |

Describe transitions as visible events, not only effect names.

## Performance candidates

- **Restrained naturalism**: micro-expressions, realistic blinking, minimal gesture. Recommend for close-ups and premium drama.
- **Controlled confidence**: economical movement, deliberate eye line, calm posture. Recommend for fashion and products.
- **Urgent realism**: faster breath, interrupted speech, reactive gesture without theatrical exaggeration. Recommend for short drama.
- **Playful spontaneity**: loose timing, quick reactions, small imperfections. Recommend for social and lifestyle work.

## Pacing candidates

- **Single sustained beat**: one action develops continuously.
- **Three-beat arc**: establish → change → settle; the safest default for 8–15 seconds.
- **Fast-cut montage**: several concise shots joined by hard, motivated cuts.
- **Held ending**: reserve the final 1–2 seconds for a stable hero frame or title.

## Audio candidates

- **Room tone**: the location's quiet baseline; makes the scene feel inhabited.
- **Foley-led**: close, synchronized object and clothing sounds; emphasizes physical detail.
- **Sparse cinematic score**: a few tonal elements with one timed impact; supports clarity.
- **Rhythmic edit cue**: percussion or pulse defines cut points and motion accents.
- **Dialogue-led**: protect speech clarity; keep music and effects subordinate.
- **Designed silence**: omit score and foreground only a few natural sounds for tension.

## Preservation and failure constraints

Choose constraints that target the likely failure:

- Preserve facial structure, hairstyle, age, wardrobe, and body proportions.
- Preserve exact product silhouette, materials, labels, and mechanical geometry.
- Keep the source camera path, timing, framing, and subject motion unchanged.
- Keep exactly the stated number of people or products.
- No extra text, logos, subtitles, watermarks, or invented UI.
- No abrupt morphing, tearing, black frames, duplicated limbs, or compositing seams.
- No cuts when the requested result is one continuous shot.
- Do not copy unrelated subject, setting, wardrobe, palette, or audio from a reference.

Prefer 2–5 targeted constraints over a generic negative-prompt dump.
