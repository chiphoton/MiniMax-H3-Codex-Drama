import assert from 'node:assert/strict'
import { randomUUID } from 'node:crypto'
import { mkdtemp, rm } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import test from 'node:test'
import { ProjectStore } from '../src/project-store.js'
import { createDirectorRpc } from '../src/rpc.js'

test('tasks/list returns jobs and run summaries across saved and draft workflows without run graphs or configuration', async t => {
  const root = await mkdtemp(join(tmpdir(), 'canvas-tasks-'))
  t.after(() => rm(root, { recursive: true, force: true }))
  const store = new ProjectStore(root, 1024)
  await store.init()
  let first = await store.createProject({ name: 'First', sessionId: randomUUID() })
  const second = await store.createProject({ name: 'Second', sessionId: randomUUID(), unsaved: true })
  const run = { id: randomUUID(), projectId: first.id, status: 'completed', mode: 'all', batchSize: 1,
    completedJobs: 1, totalJobs: 1, nodeIds: ['removed-node'], startedAt: first.createdAt }
  first = await store.saveProject(first.id, { ...first, settings: { private: 'secret-settings' }, jobs: [{
    id: randomUUID(), projectId: first.id, nodeId: 'removed-node', workflowRunId: run.id,
    status: 'completed', progress: 1, phase: 'completed', providerId: 'test', operation: 'prompt-enhancer', createdAt: first.createdAt,
    result: { kind: 'text', text: 'Retained output' }, request: { private: 'secret-request' },
  }] }, first.revision)
  await store.saveVdRun(first.id, run, { name: first.name, settings: first.settings, graph: {
    ...first.graph, nodes: [{ id: 'removed-node', data: { kind: 'load-text', title: 'Old input', text: 'secret-snapshot' } }],
  } })
  await store.cacheDraft(second.id, { name: 'Second draft', settings: second.settings, graph: {
    ...second.graph, nodes: [{ id: 'draft-node', data: { title: 'Draft node', kind: 'load-text', text: 'secret-draft' } }],
  } })
  const before = await store.getProject(first.id)
  const rpc = createDirectorRpc({ store, providers: {}, jobs: {}, workflows: {} })
  const result = await rpc('tasks/list', {})
  assert.equal(result.ok, true)
  assert.equal(result.value.projects.length, 2)
  const a = result.value.projects.find(row => row.id === first.id)
  const b = result.value.projects.find(row => row.id === second.id)
  assert.deepEqual(a.runs, [run])
  assert.equal(a.jobs[0].result.text, 'Retained output')
  assert.equal(a.jobs[0].workflowRunId, run.id)
  assert.equal(b.name, 'Second draft')
  assert.deepEqual(b.nodes, [{ id: 'draft-node', title: 'Draft node' }])
  assert.doesNotMatch(JSON.stringify(result), /secret-|sessionId|snapshot|graph/)
  assert.deepEqual(await store.getProject(first.id), before)
  const reopened = new ProjectStore(root, 1024)
  await reopened.init()
  assert.deepEqual(await reopened.taskProjects(), result.value.projects)
  const abort = new AbortController(); abort.abort()
  await assert.rejects(store.taskProjects(abort.signal), { name: 'AbortError' })
  await store.deleteProject(first.id)
  assert.deepEqual((await store.taskProjects()).map(row => row.id), [second.id])
})
