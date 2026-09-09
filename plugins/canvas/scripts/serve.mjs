import { createCanvasServer } from '../src/server.js'
import { codexRuntimeAccess } from '../src/codex-environment.js'

try {
  const app = await createCanvasServer()
  const url = await app.listen()
  console.log(`Canvas: ${url}\nProject data: ${app.store.root}\nText and image defaults: Codex Plan`)
  const codexRuntime = codexRuntimeAccess()
  if (!codexRuntime.ok) console.warn(`Codex Plan unavailable: ${codexRuntime.detail}`)
  let stopping = false
  const stop = async () => {
    if (stopping) return
    stopping = true
    const timer = setTimeout(() => process.exit(1), 10_000)
    timer.unref()
    await app.close()
    clearTimeout(timer)
  }
  process.once('SIGINT', stop)
  process.once('SIGTERM', stop)
} catch (error) {
  console.error(`Canvas could not start: ${error.message}`)
  process.exitCode = 1
}
