# Qwen Image Edit ComfyUI installation

Use this guide for `$qwen-image-edit help` or when preflight identifies a missing connection, node, or model. Commands are examples for the user or another agent; never execute downloads, installs, or restarts without explicit permission.

## Required components

| Kind | Package or filename | Recorded version | Install location | Source |
|---|---|---:|---|---|
| ComfyUI core | Core nodes | `0.27.0` workflow metadata | ComfyUI installation | [ComfyUI](https://github.com/Comfy-Org/ComfyUI) |
| Custom nodes | `Comfyui-QwenEditUtils` | `2.0.7` | `ComfyUI/custom_nodes/Comfyui-QwenEditUtils/` | [GitHub](https://github.com/lrzjason/Comfyui-QwenEditUtils) |
| UI-only custom nodes | `rgthree-comfy` | `1.0.2606200020` | `ComfyUI/custom_nodes/rgthree-comfy/` | [GitHub](https://github.com/rgthree/rgthree-comfy) |
| Checkpoint | `Qwen-Rapid-AIO-NSFW-v19.safetensors` | exact file | `ComfyUI/models/checkpoints/` | [Hugging Face](https://huggingface.co/Phr00t/Qwen-Image-Edit-Rapid-AIO/blob/main/v19/Qwen-Rapid-AIO-NSFW-v19.safetensors) |
| LoRA | `consistence_edit_v2.safetensors` | exact file | `ComfyUI/models/loras/` | [Hugging Face](https://huggingface.co/lrzjason/Consistance_Edit_Lora/blob/main/consistence_edit_v2.safetensors) |

`rgthree-comfy` is needed to reproduce the bundled canvas comparer. It is not required for a headless API run. The Qwen checkpoint contains the model, CLIP/text encoder, and VAE used by `CheckpointLoaderSimple`; no separate encoder or VAE file is referenced.

## Model integrity

| File | Download size | SHA-256 |
|---|---:|---|
| `Qwen-Rapid-AIO-NSFW-v19.safetensors` | 28.4 GB | `ba71575515709c9912560d1176b2386eaa49294fedc6ce57b9734aa57e91e5ac` |
| `consistence_edit_v2.safetensors` | 614 MB | `49bc9cd21577ab8e359f8fdaa310e5cd9c4ab0ec989d1f1a7a207245e6190310` |

The pinned checkpoint repository is marked as containing adult/sensitive model capability. Operators remain responsible for lawful, consensual, and policy-compliant use.

## Manual setup

1. Install or update ComfyUI.
2. Install the two custom-node repositories below.
3. Put the exact checkpoint and LoRA filenames in their directories.
4. Restart ComfyUI and confirm it listens at `http://localhost:8188`.
5. Load the bundled `assets/workflows/qwen-image-edit.ui.json` once to verify that no nodes are missing.

## Example node-install commands

Set `COMFYUI_DIR` to the actual installation directory first:

```bash
export COMFYUI_DIR="/absolute/path/to/ComfyUI"
git clone https://github.com/lrzjason/Comfyui-QwenEditUtils.git "$COMFYUI_DIR/custom_nodes/Comfyui-QwenEditUtils"
git clone https://github.com/rgthree/rgthree-comfy.git "$COMFYUI_DIR/custom_nodes/rgthree-comfy"
```

If a directory already exists, update it according to its repository instructions rather than cloning over it.

## Example model-download commands

These commands transfer roughly 29 GB. Confirm disk space and permission before running them:

```bash
export COMFYUI_DIR="/absolute/path/to/ComfyUI"
curl -L --fail --continue-at - \
  "https://huggingface.co/Phr00t/Qwen-Image-Edit-Rapid-AIO/resolve/main/v19/Qwen-Rapid-AIO-NSFW-v19.safetensors" \
  -o "$COMFYUI_DIR/models/checkpoints/Qwen-Rapid-AIO-NSFW-v19.safetensors"
curl -L --fail --continue-at - \
  "https://huggingface.co/lrzjason/Consistance_Edit_Lora/resolve/main/consistence_edit_v2.safetensors" \
  -o "$COMFYUI_DIR/models/loras/consistence_edit_v2.safetensors"
```

Verify hashes:

```bash
shasum -a 256 \
  "$COMFYUI_DIR/models/checkpoints/Qwen-Rapid-AIO-NSFW-v19.safetensors" \
  "$COMFYUI_DIR/models/loras/consistence_edit_v2.safetensors"
```

## Shared plugin configuration

The skill reuses `~/.config/minimax-h3-comfyui/comfy-config.json` and optional `<project-root>/.config/comfy-config.json`. Add only the Qwen model keys you need:

```json
{
  "connection": {"address": "localhost:8188"},
  "runtime": {
    "return": true,
    "preview": true,
    "load_workflow": false,
    "wait_timeout_minutes": 60
  },
  "models": {
    "qwen_checkpoint": "Qwen-Rapid-AIO-NSFW-v19.safetensors",
    "qwen_lora": "consistence_edit_v2.safetensors"
  }
}
```

Restart the Codex task after installing or updating the plugin so its skills and pinned ComfyUI MCP server reload.
