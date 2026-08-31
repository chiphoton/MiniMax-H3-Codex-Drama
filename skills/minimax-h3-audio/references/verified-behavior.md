# Verified 32x32 audio-proxy behavior

## Scope

Live verification was completed on 2026-08-31 against ComfyUI 0.30.0 through `http://127.0.0.1:8188` on a remote DGX Spark. The installed stack used:

- `minimax_h3_fl2va_int8_convrot.safetensors`
- `qwen3vl_32b_minimax_h3_int8_convrot.safetensors`
- `minimax_h3_video_vae_fp16.safetensors`
- `minimax_h3_audio_vae_fp32.safetensors`
- `minimax_h3_turbo_v4_step600_ema.safetensors` for Turbo

The graph keeps the joint H3 conditioning and sampler, fixes the visual latent to 32x32, removes video decoding and muxing, decodes the audio latent with `VAEDecodeAudio`, and writes FLAC with the core `SaveAudio` node.

## Technique provenance

- ComfyUI's H3 launch documentation establishes that the open workflow generates native audio and provides the official T2V, I2V, and R2V graph family: <https://blog.comfy.org/p/minimax-h3-day-0-support-in-comfyui>
- The 32x32 shortcut was reported publicly as a modification of the default H3 workflow for near-real-time audio generation: <https://www.reddit.com/r/comfyui/comments/1vhj6mz/minimax_h3_realtime_audio_generation_at_32x32/>
- A public audio-experiment graph independently demonstrates the same audio-focused direction: <https://huggingface.co/reverentelusarca/minimax-h3-comfyui-workflows/blob/main/MiniMax_H3_audio_experiment.json>
- This repository does not copy an arbitrary community graph. Its standard and Turbo assets are deterministic reductions of the pinned local T2V graphs named and hashed in `../../minimax-h3-comfyui/assets/workflows/manifest.json`, followed by live validation.

## Live cases

All requested categories completed successfully. Unless noted, cases were five seconds at 32 kHz stereo using Turbo with six steps.

| Case | Prompt ID | Runtime | Verification |
|---|---|---:|---|
| Woman, urgent news report | `f4c73a62-200b-48af-bdd8-2156349c6b76` | 12.26 s | Exact transcript |
| Woman, reassuring airline welcome | `ada00ea9-4602-438b-acd8-1ec23153087d` | 8.87 s | Exact meaning; ASR rendered “218” instead of “two eighteen” |
| Woman, angry confrontation | `8c311eb3-8564-4fe1-beb4-7361eedcb07f` | 9.28 s | Exact transcript; one clipped sample |
| Man, grave documentary narration | `cb400e6b-076f-4c93-a577-2eab34533781` | 10.09 s | Exact transcript |
| Man, breaking-news report | `cde22c6b-6f2-4b0a-8c44-cbc0b5d52cba` | 11.98 s | Exact transcript |
| Child, excited rocket scene | `ac6f912f-c954-4dcb-a4ab-7e379798554e` | 10.06 s | Exact words |
| Child, frightened night scene | `a6b403c4-794f-4e10-ba18-4eed33bf5e20` | 10.20 s | Exact transcript |
| Older woman, reflective memory | `97039f1c-acfc-4a4e-8a17-5942e30625ea` | 10.25 s | Exact transcript |
| Older man, wry story | `833edc4e-f04b-42fe-abfb-0192c1f91142` | 10.19 s | Exact transcript |
| Robot, station announcement | `72c6ef0f-37e6-4a3f-9c4d-98d375638706` | 9.94 s | Exact transcript |
| Dog and cat in a home | `805e32f1-3c39-4557-a9da-1fa683747954` | 9.18 s | Bark/meow/whine/purr/collar events separated; no dialogue |
| Farm animals at morning | `e9416d54-b44a-4621-a75c-e2b1c80c6a69` | 9.34 s | Rooster/cow/goat/bird-like event sequence present; no dialogue |
| Man, 15-second airline briefing | `b7eb19b9-075e-47f4-b6a6-02cfa3061ddb` | 13.57 s | Full script present; ASR normalized a written number |

A same-prompt baseline compared standard 20-step sampling (`168655d6-f30f-4392-8d8c-1ab5d466ab3c`, 32.33 s) with Turbo six-step sampling (`a3773b60-da44-4358-886c-6c539aa76aee`, 5.61 s). Both transcribed exactly. Turbo was about 5.8 times faster in this single matched run; this is not a general benchmark.

After repository integration, an API graph produced by `prepare_workflow.py --mode audio --turbo` was submitted directly to the live server. Prompt `0f3d2a61-ddaf-46b2-9e84-23bc32791504` was accepted with no node errors and completed successfully. Its output was a 5.175-second 32 kHz stereo FLAC; Whisper transcribed the locked sentence exactly, and signal measurement reported -11.3 LUFS integrated loudness and -2.0 dBTP true peak.

## Signal findings and limits

- All short clips decoded to 5.175 seconds; the long case decoded to 15.075 seconds. This reflects H3's 24 fps-compatible latent grid.
- Measured integrated loudness ranged from about -26.2 to -9.5 LUFS across the matrix. True peak ranged from about -11.2 to +0.1 dBTP.
- One speech clip contained one clipped sample. The standard baseline contained 24 clipped samples. Raw generations therefore require peak and clipping checks before delivery.
- Speech transcripts were exact at the word level in the tested scripts except for ASR number-format normalization. This does not guarantee exact text on every seed.
- Age, mood, and timbre judgments were manually spot-checked, not classified by an independent model. Animal events were checked by listening and spectrogram inspection, not by a formal bioacoustic classifier.
- These results demonstrate the workflow on the named stack and date; they do not claim voice identity control or dependable voice cloning.
