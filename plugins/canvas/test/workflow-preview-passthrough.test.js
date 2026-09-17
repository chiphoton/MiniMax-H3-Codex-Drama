import assert from 'node:assert/strict'
import { randomUUID } from 'node:crypto'
import { mkdtemp, rm } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { fileURLToPath } from 'node:url'
import test from 'node:test'
import { build } from 'esbuild'
import { ProjectStore } from '../src/project-store.js'
import { ComfyWorkflowStore } from '../src/workflow-store.js'
import { VdNodeRegistry } from '../src/node-registry.js'
import { createDirectorRpc } from '../src/rpc.js'

const compiled = await build({ entryPoints: [fileURLToPath(new URL('../src/client/controller.ts', import.meta.url))],
  bundle: true, format: 'esm', platform: 'browser', write: false })
const { DirectorController } = await import(`data:text/javascript;base64,${Buffer.from(compiled.outputFiles[0].contents).toString('base64')}`)
const node = (id, data) => ({ id, type: 'director', position: { x: 0, y: 0 }, data: { title: id, status: 'idle', ...data } })
const edge = (id, source, target, sourcePortId = 'output', targetPortId = 'reference') => ({
  id, source, target, sourceHandle: 'out', targetHandle: targetPortId.startsWith('field:') ? `in:${targetPortId}` : 'in',
  data: { sourcePortId, targetPortId },
})
const preview = id => node(id, { kind: 'preview', nodeType: 'core.preview', nodeVersion: '1.0.0', previewCleared: true })
const workflowId = 'builtin-minimax-h3-reference-to-video-turbo'

async function fixture(t, graphFor) {
  const root = await mkdtemp(join(tmpdir(), 'canvas-preview-passthrough-'))
  const store = new ProjectStore(root, 1024)
  await store.init()
  const workflows = new ComfyWorkflowStore(root)
  await workflows.init()
  const nodes = new VdNodeRegistry(workflows)
  let project = await store.createProject({ name: 'Video-Gen reproduction', sessionId: randomUUID() })
  const putAsset = (kind, name) => store.putAsset({ projectId: project.id, kind, name,
    mimeType: kind === 'image' ? 'image/png' : 'video/mp4', dataBase64: Buffer.from(name).toString('base64') })
  const input = await putAsset('image', 'sketch.png')
  const image = await putAsset('image', 'generated-image.png')
  const video = await putAsset('video', 'generated-video.mp4')
  project = await store.saveProject(project.id, { ...project, graph: { ...project.graph, ...graphFor(input) } }, project.revision)
  const requests = [], jobs = new Map()
  const rpc = createDirectorRpc({ store, workflows, nodes, providers: { publicCatalog: () => [] }, jobs: {
    start: async request => {
      requests.push(request)
      const job = { id: randomUUID(), projectId: project.id, nodeId: request.nodeId, operation: request.operation, providerId: 'fixture',
        workflowRunId: request.workflowRunId, status: 'completed', phase: 'completed', progress: 1,
        createdAt: project.createdAt, updatedAt: project.updatedAt,
        result: request.operation === 'prompt-enhancer' ? { kind: 'text', text: 'Fresh enhanced prompt' }
          : { kind: 'assets', assets: [request.operation === 'image-generation' ? image : video] } }
      jobs.set(job.id, job)
      return job
    },
    get: async (_projectId, jobId) => jobs.get(jobId),
  } })
  const context = { connection: { rpc: { call: async (_channel, endpoint, payload, signal) => rpc(endpoint, payload, signal) } }, sessions: {
    list: { getSnapshot: () => ({ current: project.sessionId, byId: { [project.sessionId]: { id: project.sessionId } } }), subscribe: () => () => {} },
    binding: () => ({ session: { getSnapshot: () => ({}), rename: async () => ({ ok: true, value: {} }) } }), open: () => {},
  } }
  const controller = new DirectorController(context)
  t.after(async () => { await controller.flushDrafts(); controller.dispose(); await rm(root, { recursive: true, force: true }) })
  await controller.start()
  return { controller, requests, image, input }
}

function imageToVideoGraph(cleared = true) {
  return { nodes: [
    node('image', { kind: 'image-generation', providerId: 'fixture', prompt: 'Fixture image' }),
    node('preview', { ...preview('preview').data, previewCleared: cleared }),
    node('video', { kind: 'video-generation', providerId: 'fixture', workflowId, prompt: 'Fixture video' }),
  ], edges: [edge('to-preview', 'image', 'preview', 'output', 'media'), edge('to-video', 'preview', 'video', 'media', 'reference')] }
}

for (const cleared of [false, true]) test(`a fresh image passes through a ${cleared ? 'cleared' : 'normal'} Preview into the next video stage`, { timeout: 4000 }, async t => {
  const { controller, requests, image } = await fixture(t, () => imageToVideoGraph(cleared))
  await assert.doesNotReject(controller.runVdWorkflow({ mode: 'all' }))
  assert.deepEqual(requests.map(request => request.nodeId), ['image', 'video'])
  assert.equal(requests[1].mediaInputs[0].assetId, image.id)
  assert.equal(requests[1].mediaInputs[0].portId, 'reference')
  assert.equal(controller.getSnapshot().workflowRuns[0].status, 'completed')
})

test('fresh results pass through a chain of cleared Previews and reach Save and video nodes', { timeout: 4000 }, async t => {
  const { controller, requests, image } = await fixture(t, () => {
    const graph = imageToVideoGraph()
    graph.nodes.push(node('save', { kind: 'save', nodeType: 'core.save', nodeVersion: '1.0.0' }), preview('preview-2'))
    graph.edges = [graph.edges[0], edge('save', 'preview-2', 'save', 'media', 'media'),
      edge('relay', 'preview', 'preview-2', 'media', 'media'), edge('video', 'preview-2', 'video', 'media', 'reference')]
    return graph
  })
  await controller.runVdWorkflow({ mode: 'all' })
  assert.equal(requests.find(request => request.nodeId === 'video').mediaInputs[0].assetId, image.id)
  assert.equal(controller.getSnapshot().project.graph.nodes.find(node => node.id === 'preview-2').data.asset.id, image.id)
})

test('Video-Gen topology carries both a cleared image Preview and a connected prompt through real RPC validation', { timeout: 4000 }, async t => {
  const { controller, requests, image, input } = await fixture(t, input => {
    const graph = imageToVideoGraph()
    graph.nodes.push(node('sketch', { kind: 'load-sketch', asset: input, mediaKind: 'sketch' }),
      node('enhance', { kind: 'prompt-enhancer', providerId: 'fixture', prompt: 'Describe the image' }),
      preview('prompt-preview'), preview('video-preview'))
    const video = graph.nodes.find(node => node.id === 'video')
    video.data.prompt = ''
    video.data.fieldInputModes = { prompt: { mode: 'input' } }
    graph.edges.push(edge('sketch-image', 'sketch', 'image'), edge('image-prompt', 'image', 'enhance'),
      edge('prompt-field', 'enhance', 'video', 'output', 'field:prompt'), edge('prompt-preview', 'enhance', 'prompt-preview', 'output', 'media'),
      edge('video-preview', 'video', 'video-preview', 'result', 'media'))
    return graph
  })
  await controller.runVdWorkflow({ mode: 'all' })
  assert.deepEqual(requests.map(request => request.nodeId), ['image', 'enhance', 'video'])
  assert.equal(requests[0].mediaInputs[0].assetId, input.id)
  assert.equal(requests[1].mediaInputs[0].assetId, image.id)
  assert.equal(requests[2].mediaInputs.find(input => input.portId === 'reference').assetId, image.id)
  assert.equal(requests[2].prompt, 'Fresh enhanced prompt')
})

test('fresh output does not replace a frozen Preview’s retained reference', { timeout: 4000 }, async t => {
  const { controller, requests, input } = await fixture(t, input => {
    const graph = imageToVideoGraph(false)
    Object.assign(graph.nodes[1].data, { frozen: true, asset: input, mediaKind: 'image', status: 'completed' })
    return graph
  })
  await controller.runVdWorkflow({ mode: 'all' })
  assert.equal(requests.find(request => request.nodeId === 'video').mediaInputs[0].assetId, input.id)
  assert.equal(controller.getSnapshot().project.graph.nodes.find(node => node.id === 'preview').data.asset.id, input.id)
})
