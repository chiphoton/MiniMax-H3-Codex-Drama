import { createServer } from 'node:http'
import { readFile, realpath } from 'node:fs/promises'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'
import { Readable } from 'node:stream'
import { pipeline } from 'node:stream/promises'
import { ChatSessions } from './chat-sessions.js'
import { codexRuntimeAccess } from './codex-environment.js'
import { CodexModelCatalog } from './codex-model-catalog.js'
import { ExampleProjects } from './example-projects.js'
import { dataDirectory, defaultProviders, MAX_ASSET_BYTES, serverPort } from './config.js'
import { JobManager } from './jobs.js'
import { localSettings } from './local-settings.js'
import { VdNodeRegistry } from './node-registry.js'
import { ProviderSettings } from './provider-settings.js'
import { ProjectStore } from './project-store.js'
import { ProviderRuntime } from './providers.js'
import { createDirectorRpc } from './rpc.js'
import { ComfyWorkflowStore } from './workflow-store.js'
import { chooseDataFolder, copyCanvasData, folderOpenLabel, loadStorageLocation, openDataFolder, saveStorageLocation, storageError } from './storage.js'

const DEFAULT_DIST = fileURLToPath(new URL('../dist/', import.meta.url))
const STATIC_FILES = new Map([['/', ['index.html', 'text/html; charset=utf-8']], ['/client.js', ['client.js', 'text/javascript; charset=utf-8']], ['/client.js.map', ['client.js.map', 'application/json']], ['/client.js.LEGAL.txt', ['client.js.LEGAL.txt', 'text/plain']]])
const MAX_REQUEST_BYTES = Math.ceil(MAX_ASSET_BYTES * 4 / 3) + 4 * 1024 * 1024

function sendJson(response, status, value) {
  response.writeHead(status, { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' })
  response.end(JSON.stringify(value))
}

async function readJson(request) {
  let length = 0
  const chunks = []
  for await (const chunk of request) {
    length += chunk.length
    if (length > MAX_REQUEST_BYTES) throw Object.assign(new Error('Request is too large'), { status: 413 })
    chunks.push(chunk)
  }
  return JSON.parse(Buffer.concat(chunks).toString('utf8'))
}

async function createRuntime(dataDir, options) {
  const store = new ProjectStore(dataDir, MAX_ASSET_BYTES)
  await store.init()
  const codexModels = new CodexModelCatalog({ cachePath: join(store.root, 'codex-models.json'), fetchModels: options.fetchCodexModels })
  await codexModels.init()
  const workflows = new ComfyWorkflowStore(store.root)
  await workflows.init()
  const nodes = new VdNodeRegistry(workflows)
  const settings = await localSettings(join(store.root, 'provider-settings.json'))
  const baseProviders = options.providers ?? defaultProviders()
  let providers
  const providerSettings = new ProviderSettings({ providers: baseProviders, minimaxH3LicenseAccepted: options.minimaxH3LicenseAccepted ?? process.env.CANVAS_MINIMAX_H3_LICENSE_ACCEPTED !== 'false' }, resolved => providers?.configure(resolved.providers, resolved.minimaxH3LicenseAccepted))
  providerSettings.attach(settings, settings.current)
  providers = new ProviderRuntime({ store, ...providerSettings.resolved(), ...(options.providerOptions ?? {}), codexModels })
  const jobs = new JobManager(store, providers, { concurrency: options.jobConcurrency ?? 2 })
  await jobs.recover()
  const sessions = new ChatSessions(store.root, { createCodex: options.createCodex, codexModels, getProvider: () => providerSettings.resolved().providers.find(provider => provider.kind === 'codex-plan') })
  await sessions.init()
  const directorRpc = createDirectorRpc({ store, workflows, nodes, providers, jobs, providerSettings, registerAsset: async () => {} })
  const examples = new ExampleProjects(options.examplesDir)

  const rpc = async (channel, endpoint, payload = {}, signal) => {
    if (channel === '/video-director') return directorRpc(endpoint, payload, signal)
    if (channel === '/canvas-examples') {
      if (endpoint === 'list') return { ok: true, value: { examples: await examples.list() } }
      if (endpoint === 'get') return { ok: true, value: { archive: await examples.read(payload.id) } }
      throw new Error('Unknown examples endpoint')
    }
    if (channel !== '/canvas-sessions') throw new Error('Unknown RPC channel')
    let value
    switch (endpoint) {
      case 'list': value = { sessions: sessions.list() }; break
      case 'create': value = await sessions.create(payload.sessionId); break
      case 'get': value = sessions.view(payload.sessionId); break
      case 'rename': value = await sessions.rename(payload.sessionId, payload.title); break
      case 'model': value = await sessions.selectModel(payload.sessionId, payload.model); break
      case 'start': value = await sessions.start(payload.sessionId, payload); break
      case 'cancel': value = sessions.cancel(payload.sessionId); break
      default: throw new Error('Unknown session endpoint')
    }
    return { ok: true, value }
  }
  return { store, providers, jobs, sessions, codexModels, rpc }
}

async function activeWorkReason(runtime) {
  if (runtime.sessions.active.size > 0) return 'Wait for the current Codex chat response to finish before changing storage.'
  if (runtime.jobs.running > 0 || runtime.jobs.queue.length > 0) return 'Wait for generation jobs to finish or cancel them before changing storage.'
  for (const project of await runtime.store.listProjects()) {
    if ((await runtime.store.listVdRuns(project.id)).some(run => run.status === 'queued' || run.status === 'running')) {
      return 'Wait for canvas workflows to finish or cancel them before changing storage.'
    }
  }
  return null
}

/** A loopback HTTP host for the migrated engine; it does not need Harness. */
export async function createCanvasServer(options = {}) {
  const location = await loadStorageLocation(options.dataDir ?? dataDirectory())
  let runtime = await createRuntime(location.dataDir, options)
  const defaultDataDir = await realpath(dirname(location.settingsPath))
  let moving = false
  let choosing = false
  let closing = false
  let closePromise
  let movePromise
  const inFlight = new Set()

  const storageInfo = async () => {
    const blockedReason = moving ? 'Canvas data is being copied. Keep this window open.' : await activeWorkReason(runtime)
    return { dataDir: runtime.store.root, defaultDataDir, isDefault: await realpath(runtime.store.root) === defaultDataDir, openLabel: folderOpenLabel(), canChange: !blockedReason, blockedReason }
  }

  const moveStorage = async (payload, reset = false) => {
    if (moving || closing) throw storageError('Canvas is busy. Wait for the current storage operation to finish.', 409)
    if (payload?.expectedDataDir !== runtime.store.root) throw storageError('The data folder changed in another window. Refresh Storage settings and try again.', 409)
    moving = true
    movePromise = (async () => {
      // Stop accepting new operations and let current writes finish before copying.
      await Promise.allSettled([...inFlight])
      const blocked = await activeWorkReason(runtime)
      if (blocked) throw storageError(blocked, 409)
      const previousDataDir = runtime.store.root
      if (reset && await realpath(previousDataDir) === defaultDataDir) return { ...await storageInfo(), canChange: true, blockedReason: null, previousDataDir, backupDataDir: null }
      const { dataDir: destination, backupDataDir } = await copyCanvasData(previousDataDir, reset ? defaultDataDir : payload.dataDir, { replaceDefault: reset })
      let next
      try {
        next = await createRuntime(destination, options)
        await saveStorageLocation(location.settingsPath, destination)
      } catch (error) {
        await next?.sessions.close()
        await next?.codexModels.close()
        throw storageError(`Data was copied to ${destination}, but Canvas could not activate it. The original folder is still in use. ${error.message}`)
      }
      await runtime.codexModels.close()
      runtime = next
      return { ...await storageInfo(), canChange: true, blockedReason: null, previousDataDir, backupDataDir }
    })()
    try { return await movePromise }
    finally { moving = false; movePromise = undefined }
  }

  const rpc = async (channel, endpoint, payload = {}, signal) => {
    if (closing) throw storageError('Canvas is shutting down.', 503)
    if (channel === '/canvas-storage') {
      let value
      if (endpoint === 'info') value = await storageInfo()
      else if (endpoint === 'change') value = await moveStorage(payload)
      else if (endpoint === 'reset') value = await moveStorage(payload, true)
      else if (endpoint === 'choose') {
        if (moving || choosing) throw storageError('Wait for the current folder operation to finish.', 409)
        choosing = true
        try { value = { dataDir: await (options.chooseFolder ?? chooseDataFolder)(runtime.store.root, { language: payload.language, signal }) } }
        finally { choosing = false }
      }
      else if (endpoint === 'open') {
        if (moving) throw storageError('Wait for the data folder change to finish.', 409)
        await (options.openFolder ?? openDataFolder)(runtime.store.root)
        value = { opened: true }
      } else throw storageError('Unknown storage operation.')
      return { ok: true, value }
    }
    if (moving) throw storageError('Canvas data is being copied. Try again when the folder change finishes.', 503)
    const operation = runtime.rpc(channel, endpoint, payload, signal)
    inFlight.add(operation)
    try { return await operation } finally { inFlight.delete(operation) }
  }

  const server = createServer(async (request, response) => {
    response.setHeader('X-Content-Type-Options', 'nosniff')
    response.setHeader('Referrer-Policy', 'no-referrer')
    response.setHeader('Cross-Origin-Resource-Policy', 'same-origin')
    try {
      const address = server.address()
      const hosts = new Set([`127.0.0.1:${address.port}`, `localhost:${address.port}`])
      if (!hosts.has(request.headers.host)) return sendJson(response, 403, { error: 'Canvas accepts loopback hosts only' })
      const origin = `http://${request.headers.host}`
      // JSON RPC and same-origin validation prevent unrelated websites from using local credentials.
      if ((request.headers.origin && request.headers.origin !== origin)
        || request.headers['sec-fetch-site'] === 'cross-site') return sendJson(response, 403, { error: 'Cross-origin requests are not allowed' })
      const url = new URL(request.url, origin)
      if (request.method === 'GET' && url.pathname === '/health') return sendJson(response, 200, { ok: true, app: 'canvas', version: '0.2.0', dataDir: runtime.store.root, codexRuntime: codexRuntimeAccess() })
      if (request.method === 'POST' && url.pathname === '/api/rpc') {
        if (!request.headers['content-type']?.startsWith('application/json')) return sendJson(response, 415, { error: 'Use application/json' })
        const body = await readJson(request)
        const controller = new AbortController()
        response.on('close', () => { if (!response.writableEnded) controller.abort() })
        const result = await rpc(body.channel, body.endpoint, body.payload, controller.signal)
        return sendJson(response, 200, result)
      }
      if (request.method === 'GET' || request.method === 'HEAD') {
        const properties = /^\/api\/video-director\/assets\/([0-9a-f-]+)\/properties$/u.exec(url.pathname)
        if (properties && request.method === 'GET') {
          const controller = new AbortController()
          response.on('close', () => { if (!response.writableEnded) controller.abort() })
          const result = await rpc('/video-director', 'assets/properties', { assetId: properties[1] }, controller.signal)
          return sendJson(response, result.ok ? 200 : 503, result)
        }
        const asset = /^\/api\/video-director\/assets\/([0-9a-f-]+)$/u.exec(url.pathname)
        if (asset) {
          const result = await runtime.store.assetResponse(asset[1], new Request(url, { method: request.method, headers: request.headers }))
          response.writeHead(result.status, Object.fromEntries(result.headers))
          if (result.body) await pipeline(Readable.fromWeb(result.body), response)
          else response.end()
          return
        }
        const file = STATIC_FILES.get(url.pathname)
        if (file) {
          const bytes = await readFile(join(options.distDir ?? DEFAULT_DIST, file[0]))
          response.writeHead(200, { 'Content-Type': file[1], 'Content-Length': bytes.length, 'Cache-Control': 'no-cache', 'Content-Security-Policy': "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; media-src 'self' blob:; connect-src 'self'; frame-ancestors 'none'" })
          response.end(request.method === 'HEAD' ? undefined : bytes)
          return
        }
      }
      sendJson(response, 404, { error: 'Not found' })
    } catch (error) {
      if (response.headersSent) { response.destroy(); return }
      const message = error.code === 'ENOENT' ? 'Canvas file not found. Run npm run build before starting.' : String(error.message ?? error)
      sendJson(response, error.status ?? 400, { ok: false, error: { code: error.code ?? 'canvas/request-failed', message, details: {} } })
    }
  })
  return {
    server, rpc,
    get store() { return runtime.store },
    get providers() { return runtime.providers },
    get sessions() { return runtime.sessions },
    async listen(port = serverPort()) {
      await new Promise((resolve, reject) => { server.once('error', reject); server.listen(port, '127.0.0.1', () => { server.off('error', reject); resolve() }) })
      return `http://127.0.0.1:${server.address().port}`
    },
    async close() {
      if (closing) return closePromise
      closing = true
      closePromise = (async () => {
        await movePromise?.catch(() => {})
        await Promise.allSettled([...inFlight])
        const { store, sessions, jobs, codexModels } = runtime
        await sessions.close()
        await codexModels.close()
        for (const summary of await store.listProjects()) {
          const project = await store.getProject(summary.id)
          await Promise.all(project.jobs.filter(job => job.status === 'queued' || job.status === 'running').map(job => jobs.cancel(project.id, job.id)))
        }
        if (server.listening) await new Promise((resolve, reject) => { server.close(error => error ? reject(error) : resolve()); server.closeIdleConnections() })
      })()
      return closePromise
    },
  }
}
