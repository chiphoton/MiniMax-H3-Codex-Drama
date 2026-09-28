import { createCanvasServer } from '../../src/server.js'
import { fetchTestModels } from './codex-models.js'

export async function testHost(dataDir, options = {}) {
  const app = await createCanvasServer({ dataDir, fetchCodexModels: fetchTestModels, ...options })
  return { store: app.store, providers: app.providers, close: () => app.close(),
    rpc: (endpoint, payload, signal) => app.rpc('/video-director', endpoint, payload, signal) }
}
