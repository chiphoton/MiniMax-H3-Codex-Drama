import assert from 'node:assert/strict'
import { mkdtemp, readFile, rm, stat } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import test from 'node:test'
import { request } from 'node:http'
import { createCanvasServer } from '../src/server.js'
import { defaultProviders } from '../src/config.js'
import { fetchTestModels } from './fixtures/codex-models.js'

async function host(t, options = {}) {
  const root = await mkdtemp(join(tmpdir(), 'codex-canvas-host-'))
  const app = await createCanvasServer({ fetchCodexModels: fetchTestModels, dataDir: root, providers: defaultProviders({}), ...options })
  const url = await app.listen(0)
  t.after(async () => { await app.close(); await rm(root, { recursive: true, force: true }) })
  const rpc = async (endpoint, payload = {}, channel = '/video-director') => {
    const response = await fetch(`${url}/api/rpc`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ channel, endpoint, payload }) })
    const result = await response.json()
    assert.equal(result.ok, true, JSON.stringify(result))
    return result.value
  }
  return { app, root, url, rpc }
}

test('standalone HTTP host persists Codex defaults, explicit overrides, and secret-safe settings', async t => {
  const { app, root, rpc } = await host(t)
  const session = await rpc('create', {}, '/canvas-sessions')
  const { project } = await rpc('projects/create', { name: 'Migrated project', sessionId: session.id })
  assert.equal(project.settings.defaultTextProvider, 'codex-plan')
  assert.equal(project.settings.defaultImageProvider, 'codex-plan')
  assert.equal(project.settings.defaultVideoProvider, 'comfyui')
  project.settings.defaultTextProvider = 'ollama'
  const saved = await rpc('projects/save', { projectId: project.id, project, expectedRevision: project.revision })
  assert.equal(saved.project.settings.defaultTextProvider, 'ollama')
  const updated = await rpc('providers/update', { providerId: 'openai', patch: { apiKey: 'unit-test-secret' } })
  assert.equal(updated.providers.find(provider => provider.id === 'openai').apiKeySet, true)
  assert.equal(JSON.stringify(updated).includes('unit-test-secret'), false)
  assert.equal((await stat(join(root, 'provider-settings.json'))).mode & 0o777, 0o600)
  const secretFile = JSON.parse(await readFile(join(root, 'provider-settings.json'), 'utf8'))
  assert.equal(secretFile.providerOverrides.openai.apiKey, 'unit-test-secret')
  await app.close()
  const reopened = await createCanvasServer({ fetchCodexModels: fetchTestModels, dataDir: root, providers: defaultProviders({}) })
  try {
    assert.equal((await reopened.store.getProject(project.id)).settings.defaultTextProvider, 'ollama')
    assert.equal(reopened.providers.publicCatalog().find(provider => provider.id === 'openai').apiKeySet, true)
    assert.equal(reopened.sessions.view(session.id).id, session.id)
  } finally { await reopened.close() }
})

test('HTTP host blocks foreign origins/hosts and serves project asset ranges', async t => {
  const { url, rpc } = await host(t)
  assert.equal((await fetch(`${url}/health`)).status, 200)
  assert.equal((await fetch(`${url}/health`, { headers: { Origin: 'https://unrelated.example' } })).status, 403)
  const foreignHostStatus = await new Promise((resolve, reject) => {
    const probe = request(`${url}/health`, { headers: { Host: 'unrelated.example' } }, response => {
      response.resume()
      resolve(response.statusCode)
    })
    probe.on('error', reject)
    probe.end()
  })
  assert.equal(foreignHostStatus, 403)
  assert.equal((await fetch(`${url}/api/rpc`, { method: 'POST', body: '{}' })).status, 415)
  const session = await rpc('create', {}, '/canvas-sessions')
  const { project } = await rpc('projects/create', { name: 'Media', sessionId: session.id })
  const { asset } = await rpc('assets/put', { projectId: project.id, kind: 'image', name: 'tiny.png', mimeType: 'image/png', dataBase64: Buffer.from('0123456789').toString('base64') })
  assert.equal(await (await fetch(new URL(asset.url, url))).text(), '0123456789')
  const ranged = await fetch(new URL(asset.url, url), { headers: { Range: 'bytes=2-5' } })
  assert.equal(ranged.status, 206)
  assert.equal(await ranged.text(), '2345')
  const head = await fetch(new URL(asset.url, url), { method: 'HEAD' })
  assert.equal(head.status, 200)
  assert.equal(await head.text(), '')
})

test('local provider integration executes text and imports an image through the selected Codex model', async t => {
  const selected = []
  const { app, rpc, url } = await host(t, { providerOptions: { createCodex: () => ({ startThread: options => {
    selected.push(options)
    return {
      run: async () => ({ finalResponse: 'Generated test text' }),
      runStreamed: async () => ({ events: (async function* () {
        yield { type: 'item.completed', item: { type: 'mcp_tool_call', result: { content: [{ type: 'image', mimeType: 'image/png', data: Buffer.from('test generated image').toString('base64') }] } } }
      })() }),
    }
  } }) } })
  const session = await rpc('create', {}, '/canvas-sessions')
  const { project } = await rpc('projects/create', { name: 'Provider integration', sessionId: session.id })
  const signal = new AbortController().signal
  const text = await app.providers.run({ operation: 'prompt-enhancer', providerId: project.settings.defaultTextProvider, prompt: 'Test prompt', projectId: project.id }, signal)
  assert.equal(text.text, 'Generated test text')
  const result = await app.providers.run({ operation: 'image-generation', providerId: project.settings.defaultImageProvider, prompt: 'Test image', projectId: project.id }, signal)
  assert.equal(result.assets.length, 1)
  assert.equal(await (await fetch(new URL(result.assets[0].url, url))).text(), 'test generated image')
  assert.deepEqual(selected.map(options => options.model), ['gpt-5.6-sol', 'gpt-5.6-sol'])
  assert.deepEqual(selected.map(options => options.sandboxMode), ['read-only', 'workspace-write'])
})

test('chat shares the live catalog and saved Fast setting with workflow providers', async t => {
  const calls = []
  const { app, root, rpc } = await host(t, { createCodex: clientOptions => ({ startThread: threadOptions => ({
    runStreamed: async () => {
      calls.push({ ...clientOptions, ...threadOptions })
      return { events: (async function* () { yield { type: 'item.completed', item: { id: 'test-answer', type: 'agent_message', text: 'Test answer' } } })() }
    },
  }) }) })
  const initial = (await rpc('providers/list')).providers.find(provider => provider.id === 'codex-plan')
  assert.deepEqual(initial.availableModels, [])
  assert.equal(initial.fastMode, false)
  const catalog = await rpc('providers/models', { providerId: 'codex-plan' })
  assert.ok(catalog.models.includes('future-model'))
  const session = await rpc('create', {}, '/canvas-sessions')
  await rpc('model', { sessionId: session.id, model: 'future-model' }, '/canvas-sessions')
  const reply = async () => {
    await rpc('start', { sessionId: session.id, text: 'Test' }, '/canvas-sessions')
    await Promise.all([...app.sessions.active.values()].map(task => task.promise))
    assert.equal(app.sessions.view(session.id).error, null)
  }
  await reply()
  await rpc('providers/update', { providerId: 'codex-plan', patch: { fastMode: true } })
  await reply()
  assert.deepEqual(calls.map(call => [call.model, call.modelReasoningEffort, call.serviceTier]), [
    ['future-model', 'max', 'default'], ['future-model', 'max', 'priority'],
  ])
  await app.close()
  const reopened = await createCanvasServer({ dataDir: root, providers: defaultProviders({}), fetchCodexModels: async () => { throw new Error('Offline') } })
  try {
    const provider = reopened.providers.publicCatalog().find(provider => provider.id === 'codex-plan')
    assert.equal(provider.fastMode, true)
    assert.equal(provider.codexCatalog.source, 'cache')
    assert.ok(provider.availableModels.includes('future-model'))
    assert.equal(reopened.sessions.view(session.id).model, 'future-model')
    const updated = await reopened.rpc('/video-director', 'providers/update', { providerId: 'codex-plan', patch: { fastMode: false } })
    assert.equal(updated.value.providers.find(provider => provider.id === 'codex-plan').fastMode, false)
  } finally { await reopened.close() }
})
