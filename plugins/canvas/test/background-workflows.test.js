import assert from 'node:assert/strict'
import { randomUUID } from 'node:crypto'
import { mkdtemp, rm } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { fileURLToPath } from 'node:url'
import test from 'node:test'
import { build } from 'esbuild'
import { ProjectStore } from '../src/project-store.js'
import { VdNodeRegistry } from '../src/node-registry.js'
import { createDirectorRpc } from '../src/rpc.js'

const bundle = await build({ entryPoints: [fileURLToPath(new URL('../src/client/controller.ts', import.meta.url))],
  bundle: true, format: 'esm', platform: 'browser', write: false })
const { DirectorController } = await import(`data:text/javascript;base64,${Buffer.from(bundle.outputFiles[0].contents).toString('base64')}`)
const ok = value => ({ ok: true, value })
function deferred() { let resolve; const promise = new Promise(done => { resolve = done }); return { promise, resolve } }
async function until(predicate) {
  for (let count = 0; count < 400; count++) {
    if (predicate()) return
    await new Promise(resolve => setTimeout(resolve, 5))
  }
  assert.fail('Timed out waiting for the workflow')
}

async function fixture(t, { hold = () => false } = {}) {
  const root = await mkdtemp(join(tmpdir(), 'canvas-background-'))
  const store = new ProjectStore(root, 1024)
  await store.init()
  const projects = []
  for (const name of ['Alpha', 'Beta', 'Unvisited']) {
    let project = await store.createProject({ name, sessionId: randomUUID() })
    project = await store.saveProject(project.id, { ...project, settings: { private: 'secret-setting' }, graph: {
      ...project.graph,
      nodes: ['first', 'second'].map((id, index) => ({ id, type: 'director', position: { x: index * 400, y: 0 },
        data: { kind: 'prompt-enhancer', title: `${name} ${id}`, providerId: 'test-provider', prompt: `${name} ${id}`, status: 'idle' } })),
      edges: [{ id: 'edge', source: 'first', sourceHandle: 'out', target: 'second', targetHandle: 'in',
        data: { sourcePortId: 'output', targetPortId: 'reference' } }],
    } }, project.revision)
    projects.push(project)
  }
  const [a, b, c] = projects
  const starts = [], calls = []
  const hooks = {}
  const workflows = { list: () => [] }
  const rpc = createDirectorRpc({ store, providers: {}, workflows, nodes: new VdNodeRegistry(workflows), jobs: {} })
  const sessions = { current: a.sessionId, byId: Object.fromEntries(projects.map(p => [p.sessionId, { id: p.sessionId }])) }
  async function persist(job) {
    const project = await store.getProject(job.projectId)
    await store.updateProject(job.projectId, { jobs: [...project.jobs.filter(row => row.id !== job.id), structuredClone(job)] })
  }
  const context = { sessions: {
    list: { getSnapshot: () => sessions, subscribe: () => () => {} },
    binding: () => ({ session: { getSnapshot: () => ({}), rename: async () => ok({}) } }),
    open: id => { sessions.current = id },
    create: async ({ sessionId = randomUUID() } = {}) => { sessions.byId[sessionId] = { id: sessionId }; return sessionId },
  }, connection: { rpc: { call: async (_channel, endpoint, payload, signal) => {
    calls.push({ endpoint, payload })
    if (hooks[endpoint]) { const result = await hooks[endpoint](payload, signal); if (result !== undefined) return result }
    if (endpoint === 'providers/list') return ok({ providers: [] })
    if (endpoint === 'workflows/list') return ok({ workflows: [] })
    if (endpoint === 'nodes/list') return ok({ nodeDefinitions: [] })
    if (endpoint === 'jobs/start') {
      const request = payload.snapshot.request
      const now = new Date().toISOString()
      const entry = { request, gate: deferred(), job: {
        id: randomUUID(), projectId: payload.projectId, nodeId: payload.nodeId, clientRunId: payload.clientRunId,
        operation: 'prompt-enhancer', providerId: request.providerId, runSequence: starts.length + 1,
        workflowRunId: request.workflowRunId, workflowRunMode: request.workflowRunMode,
        batchIndex: request.batchIndex, batchSize: request.batchSize,
        status: 'running', phase: 'working', progress: .5, createdAt: now, updatedAt: now,
      } }
      starts.push(entry)
      if (!hold(entry, starts)) entry.gate.resolve()
      await persist(entry.job)
      return ok({ job: structuredClone(entry.job) })
    }
    if (endpoint === 'jobs/get' || endpoint === 'jobs/cancel') {
      const entry = starts.find(row => row.job.id === payload.jobId)
      assert.equal(payload.projectId, entry.job.projectId, 'job actions must use their source workflow')
      if (endpoint === 'jobs/cancel') {
        entry.job = { ...entry.job, status: 'cancelled', phase: 'cancelled' }
        await persist(entry.job)
        entry.gate.resolve()
      } else {
        await entry.gate.promise
        if (entry.job.status === 'running') {
          entry.job = { ...entry.job, status: 'completed', phase: 'completed', progress: 1,
            result: { kind: 'text', providerId: 'test-provider', text: `${entry.request.prompt} result` } }
          await persist(entry.job)
        }
      }
      return ok({ job: structuredClone(entry.job) })
    }
    if (endpoint === 'jobs/delete') {
      const project = await store.getProject(payload.projectId)
      await store.updateProject(project.id, { jobs: project.jobs.filter(job => job.id !== payload.jobId) })
      return ok({})
    }
    return rpc(endpoint, payload, signal)
  } } } }
  const controller = new DirectorController(context)
  await controller.start()
  await controller.refreshTasks()
  t.after(async () => {
    for (const entry of starts) entry.gate.resolve()
    await controller.flushDrafts()
    controller.dispose()
    await rm(root, { recursive: true, force: true })
  })
  return { a, b, c, controller, store, starts, hooks, calls, context }
}

test('background workflows retain stages, batches, queued snapshots and results while another workflow with the same node IDs runs', { timeout: 8000 }, async t => {
  const app = await fixture(t, { hold: (_entry, starts) => starts.length === 1 })
  const { a, b, controller, starts, store } = app
  const first = controller.runVdWorkflow({ mode: 'all', batchSize: 2 })
  await until(() => starts.length === 1)
  controller.updateNode('first', { prompt: 'Queued Alpha prompt' })
  const queued = controller.runVdWorkflow({ mode: 'all' })
  const alphaDone = Promise.all([first, queued])
  controller.updateNode('first', { prompt: 'Later editable Alpha prompt' })
  await controller.selectProject(b.id)
  assert.equal(controller.getSnapshot().phase, 'ready')
  const betaRunId = await controller.runVdWorkflow({ mode: 'all' })
  const betaGraph = structuredClone(controller.getSnapshot().project.graph)
  assert.equal(starts.filter(row => row.job.projectId === a.id).length, 1, 'Alpha remains blocked while Beta completes independently')
  assert.equal(controller.getSnapshot().workflowRuns.find(run => run.id === betaRunId).status, 'completed')
  await controller.selectProject(a.id)
  assert.equal(controller.getSnapshot().project.graph.nodes.find(n => n.id === 'first').data.prompt, 'Later editable Alpha prompt')
  assert.equal(controller.getSnapshot().project.graph.nodes.find(n => n.id === 'first').data.status, 'running')
  await controller.selectProject(b.id)
  starts[0].gate.resolve()
  const alphaRunIds = await alphaDone
  assert.equal(controller.getSnapshot().project.id, b.id)
  assert.deepEqual(JSON.parse(JSON.stringify(controller.getSnapshot().project.graph)), JSON.parse(JSON.stringify(betaGraph)), 'background results never change the visible canvas')
  const alphaStarts = starts.filter(row => row.job.projectId === a.id)
  assert.deepEqual(alphaStarts.map(row => row.request.prompt), ['Alpha first', 'Alpha second', 'Alpha first', 'Alpha second', 'Queued Alpha prompt', 'Alpha second'])
  assert.deepEqual(alphaStarts.map(row => row.request.batchIndex), [0, 0, 1, 1, 0, 0])
  for (const index of [1, 3, 5]) assert.equal(JSON.parse(alphaStarts[index].request.context)[0].text, `${alphaStarts[index - 1].request.prompt} result`)
  await controller.flushDrafts()
  const persisted = await store.getProject(a.id)
  assert.equal(persisted.graph.nodes[0].data.prompt, 'Alpha first', 'background results do not commit the editable graph')
  assert.equal(persisted.draft.graph.nodes.find(n => n.id === 'first').data.prompt, 'Later editable Alpha prompt')
  assert.equal(persisted.draft.graph.nodes.find(n => n.id === 'first').data.result.text, 'Queued Alpha prompt result')
  await controller.refreshTasks()
  assert.deepEqual(controller.getSnapshot().workflowRuns.filter(run => run.projectId === a.id).map(run => run.id).sort(), alphaRunIds.sort())
  assert.equal(controller.getSnapshot().taskProjects.find(p => p.id === a.id).jobs.length, 6)
  await controller.selectProject(a.id)
  assert.equal(controller.getSnapshot().project.graph.nodes.find(n => n.id === 'first').data.result.text, 'Queued Alpha prompt result')
  assert.equal(controller.getSnapshot().dirty, true)
})

test('cancelling a background workflow and its queued run leaves the current workflow running', { timeout: 8000 }, async t => {
  const { a, b, controller, starts } = await fixture(t, { hold: () => true })
  const first = controller.runVdWorkflow({ mode: 'all' }).catch(error => error)
  await until(() => starts.length === 1)
  const runId = controller.getSnapshot().workflowRuns[0].id
  const queued = controller.runVdWorkflow({ mode: 'all' }).catch(error => error)
  const queuedId = controller.getSnapshot().workflowRuns[0].id
  await controller.selectProject(b.id)
  const second = controller.runVdWorkflow({ mode: 'all' }).catch(error => error)
  await until(() => starts.length === 2)
  const secondId = controller.getSnapshot().workflowRuns.find(run => run.projectId === b.id).id
  await assert.rejects(controller.deleteProject(a.id), /finish or cancel/)
  await controller.cancelVdRun(queuedId, a.id)
  await queued
  await controller.cancelVdRun(runId, a.id)
  await first
  assert.equal(starts.length, 2, 'cancelled background runs cannot submit a next stage')
  assert.equal(controller.getSnapshot().project.id, b.id)
  assert.equal(controller.getSnapshot().project.graph.nodes[0].data.status, 'running')
  assert.equal(controller.getSnapshot().workflowRuns.find(run => run.id === secondId).status, 'running')
  assert.ok(controller.getSnapshot().workflowRuns.filter(run => run.projectId === a.id).every(run => run.status === 'cancelled'))
  await controller.cancelVdRun(secondId, b.id)
  await second
})

test('a delayed direct job submission and result survive creating a new canvas', { timeout: 8000 }, async t => {
  const { a, controller, hooks, starts } = await fixture(t, { hold: () => true })
  const gate = deferred()
  hooks['jobs/start'] = async () => { await gate.promise }
  const direct = controller.runNode('first')
  await controller.createProject('New while running')
  const newId = controller.getSnapshot().project.id
  gate.resolve()
  await direct
  starts[0].gate.resolve()
  await until(() => controller.getSnapshot().taskProjects.find(row => row.id === a.id).jobs[0]?.status === 'completed')
  assert.equal(controller.getSnapshot().project.id, newId)
  assert.equal(controller.getSnapshot().project.graph.nodes.length, 0)
  await controller.selectProject(a.id)
  assert.equal(controller.getSnapshot().project.graph.nodes[0].data.result.text, 'Alpha first result')
})

test('a result arriving during a workflow reload wins over the stale project response', { timeout: 8000 }, async t => {
  const { a, b, controller, hooks, starts, store } = await fixture(t, { hold: () => true })
  await controller.runNode('first')
  await controller.selectProject(b.id)
  const requested = deferred(), release = deferred()
  hooks['projects/get'] = async payload => {
    if (payload.projectId !== a.id) return
    const stale = await store.getProject(a.id)
    requested.resolve()
    await release.promise
    return ok({ project: stale })
  }
  const switching = controller.selectProject(a.id)
  await requested.promise
  starts[0].gate.resolve()
  await until(() => controller.getSnapshot().taskProjects.find(row => row.id === a.id).jobs[0]?.status === 'completed')
  release.resolve()
  await switching
  assert.equal(controller.getSnapshot().project.graph.nodes[0].data.status, 'completed')
  assert.equal(controller.getSnapshot().project.graph.nodes[0].data.result.text, 'Alpha first result')
})

test('global task refresh and background actions retain the owning workflow and never rewind newer jobs', { timeout: 8000 }, async t => {
  const { a, b, c, controller, hooks, starts, store, calls } = await fixture(t, { hold: () => true })
  await controller.runNode('first')
  const requested = deferred(), release = deferred()
  hooks['tasks/list'] = async () => {
    const stale = await store.taskProjects()
    requested.resolve()
    await release.promise
    return ok({ projects: stale })
  }
  const refreshing = controller.refreshTasks()
  await requested.promise
  await controller.selectProject(b.id)
  starts[0].gate.resolve()
  await until(() => controller.getSnapshot().taskProjects.find(row => row.id === a.id).jobs[0]?.status === 'completed')
  release.resolve()
  await refreshing
  assert.equal(controller.getSnapshot().taskProjects.find(row => row.id === a.id).jobs[0].status, 'completed')
  delete hooks['tasks/list']
  await controller.refreshTasks()
  assert.equal(controller.getSnapshot().taskProjects.length, 3)
  assert.ok(controller.getSnapshot().taskProjects.some(row => row.id === c.id), 'unvisited workflows are listed too')
  const jobId = starts[0].job.id
  await controller.deleteJob(jobId, a.id)
  assert.equal(controller.getSnapshot().project.id, b.id)
  assert.equal(controller.getSnapshot().taskProjects.find(row => row.id === a.id).jobs.length, 0)
  assert.deepEqual(calls.findLast(row => row.endpoint === 'jobs/delete').payload, { projectId: a.id, jobId })
})

test('history export and opening target an unvisited workflow while another workflow continues running', { timeout: 8000 }, async t => {
  const { a, c, controller, store, starts } = await fixture(t, { hold: () => true })
  const currentRun = controller.runVdWorkflow({ mode: 'all' }).catch(error => error)
  await until(() => starts.length === 1)
  const currentRunId = controller.getSnapshot().workflowRuns[0].id
  const history = { id: randomUUID(), projectId: c.id, mode: 'all', status: 'completed',
    batchSize: 1, nodeIds: ['first', 'second'], totalJobs: 2, completedJobs: 2, startedAt: c.createdAt }
  await store.saveVdRun(c.id, history, { name: c.name, graph: c.graph, settings: c.settings })
  await controller.refreshTasks()
  const exported = JSON.parse((await controller.exportVdWorkflow(history.id, c.id)).text)
  assert.equal(controller.getSnapshot().project.id, a.id, 'export does not switch canvases')
  assert.equal(exported.project.graph.nodes[0].data.prompt, 'Unvisited first')
  await controller.openVdWorkflow(history.id, c.id)
  assert.equal(controller.getSnapshot().project.id, c.id)
  assert.equal(controller.getSnapshot().project.graph.nodes[0].data.prompt, 'Unvisited first')
  assert.equal(controller.getSnapshot().workflowRuns.find(run => run.id === currentRunId).status, 'running')
  await controller.cancelVdRun(currentRunId, a.id)
  await currentRun
})
