import assert from 'node:assert/strict'
import { randomUUID } from 'node:crypto'
import { mkdtemp, rm } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import test from 'node:test'
import { build } from 'esbuild'
import { createCanvasServer } from '../src/server.js'
import { fetchTestModels } from './fixtures/codex-models.js'

const bundle = await build({ entryPoints: ['src/client/controller.ts'], bundle: true, format: 'esm', platform: 'browser', write: false })
const { DirectorController } = await import(`data:text/javascript;base64,${Buffer.from(bundle.outputFiles[0].text + '\n//# sourceURL=canvas-background-controller.js').toString('base64')}`)
const deferred = () => { let resolve; const promise = new Promise(done => { resolve = done }); return { promise, resolve } }
async function until(predicate) {
  for (let count = 0; count < 600; count++) {
    if (await predicate()) return
    await new Promise(resolve => setTimeout(resolve, 10))
  }
  assert.fail('Timed out waiting for the Canvas server')
}

async function fixture(t) {
  const root = await mkdtemp(join(tmpdir(), 'canvas-background-'))
  const options = { dataDir: join(root, 'data'), fetchCodexModels: fetchTestModels,
    providerOptions: { createCodex: () => ({ startThread: () => ({ run: async () => ({ finalResponse: 'Resumed result' }) }) }) } }
  const app = await createCanvasServer(options)
  const url = await app.listen(0)
  const transport = async (channel, endpoint, payload = {}, signal) => {
    const response = await fetch(`${url}/api/rpc`, { method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ channel, endpoint, payload }), signal })
    return response.json()
  }
  const call = async (endpoint, payload = {}, channel = '/video-director') => {
    const result = await transport(channel, endpoint, payload)
    if (!result.ok) throw Object.assign(new Error(result.error.message), result.error)
    return result.value
  }
  const projects = []
  for (const name of ['Alpha', 'Beta']) {
    const session = await app.sessions.create()
    let project = await app.store.createProject({ name, sessionId: session.id })
    project = await app.store.saveProject(project.id, { ...project, graph: { ...project.graph,
      nodes: ['first', 'second'].map(id => ({ id, type: 'director', position: { x: 0, y: 0 },
        data: { kind: 'prompt-enhancer', title: id, providerId: 'codex-plan', prompt: `${name} ${id}`, status: 'idle' } })),
      edges: [{ id: 'dependency', source: 'first', target: 'second' }],
    } }, project.revision)
    projects.push(project)
  }
  const starts = [], gate = deferred()
  app.providers.run = async (request, signal) => {
    starts.push(request)
    if (starts.length === 1) await new Promise((resolve, reject) => {
      const aborted = () => reject(signal.reason)
      if (signal.aborted) return aborted()
      signal.addEventListener('abort', aborted, { once: true })
      gate.promise.then(() => { signal.removeEventListener('abort', aborted); resolve() })
    })
    return { kind: 'text', text: `${request.prompt} result`, providerId: 'codex-plan' }
  }
  const controller = new DirectorController({ connection: { rpc: { call: transport } }, sessions: {
    list: { getSnapshot: () => ({ current: projects[0].sessionId, byId: Object.fromEntries(projects.map(p => [p.sessionId, { id: p.sessionId }])) }), subscribe: () => () => {} },
    binding: () => ({ session: { getSnapshot: () => ({}), rename: async () => ({ ok: true, value: {} }) } }), open: () => {},
  } })
  t.after(async () => { gate.resolve(); controller.dispose(); await controller.flushDrafts(); await app.close(); await rm(root, { recursive: true, force: true }) })
  await controller.start()
  const submit = async project => (await call('vd-runs/submit', { projectId: project.id, snapshot: project,
    runIds: [randomUUID()], options: { mode: 'all' } })).runs[0]
  return { root, app, options, controller, starts, gate, call, submit, a: projects[0], b: projects[1] }
}

test('Canvas executes captured stages and repeats globally after the browser closes, preserving later drafts', { timeout: 10000 }, async t => {
  const { app, controller, starts, gate, a, b, call, submit } = await fixture(t)
  const observed = controller.runVdWorkflow({ mode: 'all', batchSize: 2 })
  await until(() => starts.length === 1)
  controller.updateNode('first', { prompt: 'Later editable Alpha prompt' })
  await controller.selectProject(b.id)
  const beta = await submit(b)
  assert.equal((await app.store.getVdRun(b.id, beta.id)).status, 'queued')
  assert.equal(starts.length, 1)
  assert.equal((await call('info', {}, '/canvas-storage')).canChange, false)
  controller.dispose()
  gate.resolve()
  await observed
  await until(async () => (await call('vd-runs/list')).runs.every(run => run.status === 'completed'))
  assert.deepEqual(starts.map(request => request.prompt), ['Alpha first', 'Alpha second', 'Alpha first', 'Alpha second', 'Beta first', 'Beta second'])
  const alpha = await app.store.getProject(a.id)
  assert.equal(alpha.draft.graph.nodes[0].data.prompt, 'Later editable Alpha prompt')
  assert.equal(alpha.graph.nodes[0].data.prompt, 'Alpha first')
  assert.equal(alpha.jobs.length, 4)
  assert.equal((await app.store.getProject(b.id)).jobs.length, 2)
  const runs = (await call('vd-runs/list')).runs
  assert.equal(runs.length, 3)
  assert.ok(runs.every(run => run.scheduler === 'host' && run.completedJobs === 2))
})

test('cancelling a background Canvas workflow and its queued repeat releases the next project', { timeout: 10000 }, async t => {
  const { controller, app, gate, starts, a, b, call, submit } = await fixture(t)
  const active = await submit(a)
  await until(() => starts.length === 1)
  const queued = await submit(a)
  const beta = await submit(b)
  await controller.selectProject(b.id)
  await controller.refreshVdRuns()
  await controller.cancelVdRun(queued.id)
  await controller.cancelVdRun(active.id)
  gate.resolve()
  await until(async () => (await app.store.getVdRun(b.id, beta.id)).status === 'completed')
  assert.equal((await app.store.getVdRun(a.id, queued.id)).status, 'cancelled')
  assert.equal((await app.store.getVdRun(a.id, active.id)).status, 'cancelled')
  assert.deepEqual(starts.map(request => request.prompt), ['Alpha first', 'Beta first', 'Beta second'])
  assert.equal(controller.getSnapshot().project.id, b.id)
  await controller.refreshVdRuns()
  assert.equal(controller.getSnapshot().jobs.filter(job => job.projectId === b.id).length, 2)
  assert.equal((await call('info', {}, '/canvas-storage')).canChange, true)
})

test('Canvas shutdown cancels the active graph and restart recovers the accepted queued graph', { timeout: 10000 }, async t => {
  const { app, options, controller, starts, a, b, submit } = await fixture(t)
  const active = await submit(a)
  await until(() => starts.length === 1)
  const queued = await submit(b)
  controller.dispose()
  await app.close()
  assert.equal((await app.store.getVdRun(a.id, active.id)).status, 'cancelled')
  assert.equal((await app.store.getVdRun(b.id, queued.id)).status, 'queued')
  const reopened = await createCanvasServer(options)
  try {
    await until(async () => (await reopened.store.getVdRun(b.id, queued.id)).status === 'completed')
    assert.equal((await reopened.store.getProject(b.id)).jobs.length, 2)
    assert.equal((await reopened.store.getProject(a.id)).jobs.length, 1)
    assert.equal((await reopened.store.listVdRunJobs(b.id, queued.id)).length, 2)
  } finally { await reopened.close() }
})

test('storage changes preserve folders and nested media, and attach scheduling to the copied store', { timeout: 10000 }, async t => {
  const { root, app, controller, a, call } = await fixture(t)
  await app.store.organizeProjects({ action: 'create', name: 'Scenes', parentId: null, expectedRevision: app.store.folders.snapshot().revision })
  const folder = app.store.folders.snapshot().folders.find(row => row.name === 'Scenes').id
  await app.store.organizeProjects({ action: 'move', kind: 'project', id: a.id, parentId: folder, expectedRevision: app.store.folders.snapshot().revision })
  const asset = await app.store.putAsset({ projectId: a.id, origin: 'output', kind: 'image', name: 'frame.png', mimeType: 'image/png', dataBase64: Buffer.from('frame').toString('base64') })
  const layout = app.store.folders.snapshot()
  controller.dispose()
  const destination = join(root, 'moved')
  await call('change', { dataDir: destination, expectedDataDir: app.store.root }, '/canvas-storage')
  assert.deepEqual(app.store.folders.snapshot(), layout)
  assert.equal(app.store.asset(asset.id).origin, 'output')
  assert.match(app.store.asset(asset.id).filename, /^outputs\//u)
  const project = await app.store.getProject(a.id)
  const { runs } = await call('vd-runs/submit', { projectId: a.id, snapshot: project, runIds: [randomUUID()], options: { mode: 'all' } })
  await until(async () => (await app.store.getVdRun(a.id, runs[0].id)).status === 'completed')
  assert.equal((await app.store.getProject(a.id)).jobs.length, 2)
})
