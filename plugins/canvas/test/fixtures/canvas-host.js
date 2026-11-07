import { createCanvasServer } from '../../src/server.js'
import { fetchTestModels } from './codex-models.js'

export async function testHost(dataDir, options = {}) {
  const app = await createCanvasServer({ dataDir, fetchCodexModels: fetchTestModels, ...options })
  return { get store() { return app.store }, get providers() { return app.providers }, get nodes() { return app.nodes }, get workflows() { return app.workflows }, close: () => app.close(),
    rpc: (endpoint, payload, signal) => endpoint.startsWith('storage/') ? app.rpc('/canvas-storage', endpoint.slice(8), payload, signal) : app.rpc('/video-director', endpoint, payload, signal) }
}
