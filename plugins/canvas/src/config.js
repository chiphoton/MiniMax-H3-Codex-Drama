import { homedir } from 'node:os'
import { join, resolve } from 'node:path'

export const DEFAULT_PORT = 8765
export const MAX_ASSET_BYTES = 200 * 1024 * 1024

export function dataDirectory(env = process.env) {
  return resolve(env.CANVAS_DATA_DIR || join(env.XDG_DATA_HOME || join(homedir(), '.local', 'share'), 'codex-canvas'))
}

export function defaultProviders(env = process.env) {
  const model = env.CANVAS_CODEX_MODEL || undefined
  return [
    { id: 'codex-plan', label: 'Codex Plan', kind: 'codex-plan', model, fastMode: false, timeoutMs: 600_000 },
    { id: 'comfyui', label: 'ComfyUI', kind: 'comfyui', baseUrl: env.COMFYUI_URL || 'http://127.0.0.1:8188' },
    { id: 'ollama', label: 'Ollama', kind: 'ollama', baseUrl: env.OLLAMA_URL || 'http://127.0.0.1:11434', model: env.OLLAMA_MODEL || 'qwen3-vl' },
    { id: 'openai', label: 'OpenAI-compatible', kind: 'openai-compatible', baseUrl: env.OPENAI_BASE_URL || 'https://api.openai.com/v1', model: env.OPENAI_MODEL || 'gpt-5.6-terra', imageModel: env.OPENAI_IMAGE_MODEL || 'gpt-image-2', requiresApiKey: true, apiKey: env.OPENAI_API_KEY },
  ]
}

export function serverPort(value = process.env.CANVAS_PORT ?? DEFAULT_PORT) {
  const port = Number(value)
  if (!Number.isInteger(port) || port < 0 || port > 65535) throw new Error('CANVAS_PORT must be an integer between 0 and 65535')
  return port
}
