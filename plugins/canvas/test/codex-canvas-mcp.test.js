import assert from 'node:assert/strict'
import test from 'node:test'
import { mkdtemp, readFile, rm } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { createCanvasServer } from '../src/server.js'
import { CodexCanvasMcp } from '../src/codex-canvas-mcp.js'
import { fetchTestModels } from './fixtures/codex-models.js'

async function fixture(t, createCodex) {
  const root = await mkdtemp(join(tmpdir(), 'canvas-mcp-test-'))
  const app = await createCanvasServer({ dataDir: root, fetchCodexModels: fetchTestModels, createCodex })
  const url = await app.listen(0)
  t.after(async () => { await app.close(); await rm(root, { recursive: true, force: true }) })
  const session = await app.sessions.create()
  const project = await app.store.createProject({ name: 'Codex canvas', sessionId: session.id })
  return { app, root, url, session, project }
}

function client(config) {
  const { url, http_headers } = config.mcp_servers.canvas
  let sequence = 0
  const request = (message, headers = http_headers, method = 'POST') => fetch(url, {
    method, headers: { 'Content-Type': 'application/json', Accept: 'application/json, text/event-stream', ...headers },
    ...(method === 'POST' ? { body: JSON.stringify(message) } : {}),
  })
  const rpc = async (method, params) => (await request({ jsonrpc: '2.0', id: ++sequence, method, params })).json()
  const command = (command, args = {}, extra = {}) => rpc('tools/call', { name: 'vd_canvas', arguments: { command, args, ...extra } })
  return { request, rpc, command }
}

test('Codex SDK chat operates its linked workflow over authenticated MCP and revokes access after each turn', async t => {
  const configurations = []
  let project, other, url
  const { app, root, session, ...fixtureData } = await fixture(t, ({ config, serviceTier }) => {
    configurations.push(config)
    assert.equal(serviceTier, 'default')
    const stream = options => ({ runStreamed: async content => {
      assert.equal(options.sandboxMode, 'read-only')
      assert.match(content[0].text, /vd_canvas MCP/)
      const mcp = client(config)
      const initialize = await mcp.rpc('initialize', { protocolVersion: '2025-03-26', capabilities: {}, clientInfo: { name: 'test', version: '1' } })
      assert.equal(initialize.result.protocolVersion, '2025-03-26')
      assert.equal((await mcp.request({ jsonrpc: '2.0', method: 'notifications/initialized' })).status, 202)
      assert.equal((await mcp.rpc('tools/list')).result.tools[0].name, 'vd_canvas')
      assert.equal((await mcp.request({}, {}, 'GET')).status, 401)
      assert.equal((await mcp.request({}, config.mcp_servers.canvas.http_headers, 'GET')).status, 405)
      assert.equal((await mcp.request({}, { ...config.mcp_servers.canvas.http_headers, Origin: 'https://foreign.test' })).status, 403)
      const spoofed = await mcp.command('summary', {}, { projectId: other.id })
      assert.equal(spoofed.result.isError, true)
      const summary = JSON.parse((await mcp.command('summary', {}, { sessionId: other.sessionId })).result.content[0].text)
      assert.equal(summary.projectId, project.id, 'the capability, not tool arguments, selects the session')
      const edited = await mcp.command('edit', { expectedDraftRevision: summary.draftRevision,
        edits: [{ op: 'add', kind: 'prompt-enhancer', data: { title: `Plan ${configurations.length}`, prompt: 'Synthetic story' } }] })
      assert.equal(edited.result.isError, undefined, edited.result.content[0].text)
      const stale = await mcp.command('edit', { expectedDraftRevision: summary.draftRevision, edits: [{ op: 'rename', name: 'Stale edit' }] })
      assert.equal(stale.result.isError, true)
      return { events: (async function* () {
        yield { type: 'thread.started', thread_id: 'synthetic-codex-thread' }
        yield { type: 'item.completed', item: { id: `tool-${configurations.length}`, type: 'mcp_tool_call', tool: 'vd_canvas', status: 'completed', arguments: { command: 'edit' } } }
        yield { type: 'item.completed', item: { id: `answer-${configurations.length}`, type: 'agent_message', text: 'Added the plan node.' } }
      })() }
    } })
    return { startThread: stream, resumeThread: (_id, options) => stream(options) }
  })
  project = fixtureData.project; url = fixtureData.url
  other = await app.store.createProject({ name: 'Other workflow', sessionId: (await app.sessions.create()).id })
  for (let turn = 1; turn <= 2; turn++) {
    await app.sessions.start(session.id, { projectId: project.id, text: 'Build a plan' })
    await Promise.all([...app.sessions.active.values()].map(task => task.promise))
    assert.equal(app.sessions.view(session.id).error, null)
    const graph = (await app.store.getProject(project.id)).draft.graph
    assert.equal(graph.nodes.length, turn)
    assert.equal(graph.nodes[turn - 1].data.providerId, 'codex-plan')
    assert.equal((await client(configurations[turn - 1]).request({})).status, 401)
  }
  assert.notEqual(configurations[0].mcp_servers.canvas.http_headers.Authorization, configurations[1].mcp_servers.canvas.http_headers.Authorization)
  assert.equal(app.sessions.view(session.id).messages.filter(message => message.kind === 'tool-call').length, 2)
  const stored = await readFile(join(root, 'sessions', `${session.id}.json`), 'utf8')
  assert.equal(stored.includes('Bearer'), false)
  assert.equal((await app.store.getProject(other.id)).draft, undefined)
  assert.equal((await fetch(`${url}/mcp/canvas`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' })).status, 401)
})

test('cancelling a Codex turn revokes its MCP capability and stops in-flight commands', async t => {
  let ready, authorization, clientConfig
  const started = new Promise(resolve => { ready = resolve })
  const { app, session, project } = await fixture(t, ({ config }) => {
    clientConfig = config
    authorization = config.mcp_servers.canvas.http_headers.Authorization
    return { startThread: () => ({ runStreamed: async (_content, { signal }) => ({ events: (async function* () {
      ready()
      await new Promise((resolve, reject) => {
        if (signal.aborted) reject(signal.reason)
        else signal.addEventListener('abort', () => reject(signal.reason), { once: true })
      })
    })() }) }) }
  })
  await app.sessions.start(session.id, { projectId: project.id, text: 'Wait' })
  await started
  const pending = app.sessions.active.get(session.id).promise
  assert.ok(authorization.startsWith('Bearer '))
  app.sessions.cancel(session.id)
  await pending
  assert.equal((await client(clientConfig).request({})).status, 401)
  assert.equal(app.sessions.view(session.id).error, 'Response cancelled.')

  const controller = new AbortController()
  const bridge = new CodexCanvasMcp({ store: app.store, getUrl: () => 'http://127.0.0.1:8765', call: async (_endpoint, _input, signal) => {
    await new Promise((resolve, reject) => signal.addEventListener('abort', () => reject(new Error('Cancelled')), { once: true }))
  } })
  const scope = await bridge.open({ projectId: project.id, sessionId: session.id, signal: controller.signal })
  const token = scope.config.mcp_servers.canvas.http_headers.Authorization
  const command = bridge.handle(token, { jsonrpc: '2.0', id: 1, method: 'tools/call', params: { name: 'vd_canvas', arguments: { command: 'summary' } } })
  controller.abort()
  assert.equal((await command).result.isError, true)
  assert.equal(bridge.authorized(token), false)
})
