import assert from 'node:assert/strict'
import { randomUUID } from 'node:crypto'
import { mkdir, mkdtemp, readFile, realpath, rename, rm, stat, symlink, writeFile } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import test from 'node:test'
import { createCanvasServer } from '../src/server.js'
import { defaultProviders } from '../src/config.js'
import { fetchTestModels } from './fixtures/codex-models.js'
import { chooseDataFolder, openDataFolder } from '../src/storage.js'

async function fixture(t, options = {}) {
  const root = await realpath(await mkdtemp(join(tmpdir(), 'canvas-storage-test-')))
  const source = join(root, 'source')
  const app = await createCanvasServer({ fetchCodexModels: fetchTestModels, dataDir: source, providers: defaultProviders({}), ...options })
  const url = await app.listen(0)
  t.after(async () => { await app.close(); await rm(root, { recursive: true, force: true }) })
  const request = async (channel, endpoint, payload = {}) => {
    const response = await fetch(`${url}/api/rpc`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ channel, endpoint, payload }),
    })
    return { status: response.status, ...await response.json() }
  }
  const rpc = async (channel, endpoint, payload) => {
    const result = await request(channel, endpoint, payload)
    assert.equal(result.ok, true, JSON.stringify(result))
    return result.value
  }
  return { root, source, app, url, rpc, request }
}

async function seed(rpc) {
  const session = await rpc('/canvas-sessions', 'create')
  const { project } = await rpc('/video-director', 'projects/create', { name: 'Storage migration', sessionId: session.id })
  project.graph.nodes.push({ id: randomUUID(), type: 'director', position: { x: 10, y: 20 }, data: {
    kind: 'prompt-enhancer', title: 'Saved prompt', providerId: 'codex-plan', prompt: 'A bridge at dusk', status: 'idle',
  } })
  await rpc('/video-director', 'projects/save', { projectId: project.id, project, expectedRevision: project.revision })
  const { asset } = await rpc('/video-director', 'assets/put', {
    projectId: project.id, kind: 'image', name: 'saved.png', mimeType: 'image/png', dataBase64: Buffer.from('saved image bytes').toString('base64'),
  })
  await rpc('/video-director', 'providers/update', { providerId: 'openai', patch: { apiKey: 'storage-test-secret' } })
  return { project, session, asset }
}

test('Storage opens the active folder, copies projects/media/settings/history, and remembers repeated changes after restart', async t => {
  const opened = []
  const { root, source, app, url, rpc } = await fixture(t, { openFolder: async path => { opened.push(path) } })
  const { project, session, asset } = await seed(rpc)
  const runId = randomUUID()
  await app.store.saveVdRun(project.id, {
    id: runId, projectId: project.id, status: 'completed', mode: 'all', batchSize: 1, completedJobs: 1, totalJobs: 1,
    nodeIds: [project.graph.nodes[0].id], startedAt: new Date().toISOString(),
  }, project)
  const relativeProject = join('projects', project.id, 'project.json')
  const originalProject = await readFile(join(source, relativeProject), 'utf8')
  assert.equal((await rpc('/canvas-storage', 'info')).dataDir, source)
  await rpc('/canvas-storage', 'open')
  assert.deepEqual(opened, [source])

  const destination = join(root, 'Canvas Data')
  const changed = await rpc('/canvas-storage', 'change', { dataDir: destination, expectedDataDir: source })
  assert.equal(changed.dataDir, destination)
  assert.equal(changed.previousDataDir, source)
  assert.equal(app.store.root, destination)
  assert.equal(await readFile(join(destination, relativeProject), 'utf8'), originalProject)
  assert.equal(await readFile(join(source, relativeProject), 'utf8'), originalProject)
  assert.equal((await app.store.getVdRun(project.id, runId)).snapshot.graph.nodes[0].data.prompt, 'A bridge at dusk')
  assert.equal((await rpc('/canvas-sessions', 'get', { sessionId: session.id })).id, session.id)
  assert.equal(await (await fetch(new URL(asset.url, url))).text(), 'saved image bytes')
  assert.equal((await stat(join(destination, 'provider-settings.json'))).mode & 0o777, 0o600)
  assert.equal(JSON.stringify(changed).includes('storage-test-secret'), false)
  await rpc('/canvas-storage', 'open')
  assert.deepEqual(opened, [source, destination])

  const { project: afterMove } = await rpc('/video-director', 'projects/create', { name: 'New location only', sessionId: session.id })
  assert.ok(await stat(join(destination, 'projects', afterMove.id, 'project.json')))
  await assert.rejects(stat(join(source, 'projects', afterMove.id)), { code: 'ENOENT' })

  const second = join(root, 'Second Data Folder')
  await mkdir(second)
  await rpc('/canvas-storage', 'change', { dataDir: second, expectedDataDir: destination })
  await assert.rejects(stat(join(second, '.canvas-storage.json')), { code: 'ENOENT' })
  assert.equal((await (await fetch(`${url}/health`)).json()).dataDir, second)
  await app.close()
  const restarted = await createCanvasServer({ fetchCodexModels: fetchTestModels, dataDir: source, providers: defaultProviders({}) })
  try {
    assert.equal(restarted.store.root, second)
    assert.equal((await restarted.store.getProject(afterMove.id)).name, 'New location only')
    assert.equal((await restarted.store.assetBytes(asset.id)).data.toString(), 'saved image bytes')
  } finally { await restarted.close() }

  await rename(second, `${second}-offline`)
  await assert.rejects(createCanvasServer({ fetchCodexModels: fetchTestModels, dataDir: source }), /saved Canvas data folder is unavailable/u)
})

test('Storage rejects nonempty, overlapping, relative and stale destinations without overwriting files', async t => {
  const { root, source, rpc, request } = await fixture(t)
  await seed(rpc)
  const occupied = join(root, 'occupied')
  await mkdir(occupied)
  await writeFile(join(occupied, 'keep.txt'), 'Do not overwrite')
  const alias = join(root, 'source-alias')
  await symlink(source, alias, 'junction')
  for (const destination of ['relative/path', source, join(source, 'nested'), root, occupied, alias]) {
    const result = await request('/canvas-storage', 'change', { dataDir: destination, expectedDataDir: source })
    assert.equal(result.ok, false, destination)
    assert.equal(result.status, 400, destination)
    assert.equal((await rpc('/canvas-storage', 'info')).dataDir, source)
  }
  const stale = await request('/canvas-storage', 'change', { dataDir: join(root, 'new'), expectedDataDir: occupied })
  assert.equal(stale.status, 409)
  assert.equal(await readFile(join(occupied, 'keep.txt'), 'utf8'), 'Do not overwrite')
  await assert.rejects(stat(join(source, '.canvas-storage.json')), { code: 'ENOENT' })
})

test('Storage keeps the original active if the persistent location cannot be committed', async t => {
  const { root, source, app, rpc, request } = await fixture(t)
  const { project } = await seed(rpc)
  await mkdir(join(source, '.canvas-storage.json'))
  const destination = join(root, 'copy')
  const result = await request('/canvas-storage', 'change', { dataDir: destination, expectedDataDir: source })
  assert.equal(result.ok, false)
  assert.match(result.error.message, /original folder is still in use/u)
  assert.equal(app.store.root, source)
  assert.equal((await rpc('/video-director', 'projects/get', { projectId: project.id })).project.name, 'Storage migration')
  assert.ok(await stat(join(destination, 'projects', project.id, 'project.json')))
})

test('Storage refuses relocation during a chat response or an active canvas workflow', async t => {
  const gate = Promise.withResolvers()
  const { root, source, app, rpc, request } = await fixture(t, { createCodex: () => ({ startThread: () => ({
    runStreamed: async () => ({ events: (async function* () {
      await gate.promise
      yield { type: 'item.completed', item: { id: 'answer', type: 'agent_message', text: 'Done' } }
    })() }),
  }) }) })
  t.after(() => gate.resolve())
  const { session, project } = await seed(rpc)
  await rpc('/canvas-sessions', 'start', { sessionId: session.id, text: 'Controlled test response' })
  try {
    const blocked = await request('/canvas-storage', 'change', { dataDir: join(root, 'new'), expectedDataDir: source })
    assert.equal(blocked.status, 409)
    assert.match(blocked.error.message, /chat response/u)
    assert.equal((await rpc('/canvas-storage', 'info')).canChange, false)
  } finally { gate.resolve(); await Promise.all([...app.sessions.active.values()].map(task => task.promise)) }
  await app.store.saveVdRun(project.id, {
    id: randomUUID(), projectId: project.id, status: 'running', mode: 'all', batchSize: 1, completedJobs: 0, totalJobs: 1,
    nodeIds: [project.graph.nodes[0].id], startedAt: new Date().toISOString(),
  }, project)
  const blocked = await request('/canvas-storage', 'change', { dataDir: join(root, 'new'), expectedDataDir: source })
  assert.equal(blocked.status, 409)
  assert.match(blocked.error.message, /canvas workflows/u)
  await assert.rejects(stat(join(root, 'new')), { code: 'ENOENT' })
})

test('Storage drains an in-flight save and blocks new writes while switching', async t => {
  const { root, source, app, rpc } = await fixture(t)
  const { project } = await seed(rpc)
  const gate = Promise.withResolvers()
  const entered = Promise.withResolvers()
  const save = app.store.saveProject.bind(app.store)
  app.store.saveProject = async (...args) => { entered.resolve(); await gate.promise; return save(...args) }
  const current = await app.store.getProject(project.id)
  current.name = 'Saved before copying'
  const saving = app.rpc('/video-director', 'projects/save', { projectId: project.id, project: current, expectedRevision: current.revision })
  await entered.promise
  const moving = app.rpc('/canvas-storage', 'change', { dataDir: join(root, 'new'), expectedDataDir: source })
  try {
    await assert.rejects(app.rpc('/video-director', 'projects/create', {}), /data is being copied/u)
  } finally { gate.resolve() }
  assert.equal((await saving).ok, true)
  assert.equal((await moving).ok, true)
  assert.equal((await app.store.getProject(project.id)).name, 'Saved before copying')
})

test('Native folder opening uses platform commands with a literal path argument', async () => {
  for (const [platform, command] of [['darwin', 'open'], ['win32', 'explorer.exe'], ['linux', 'xdg-open']]) {
    const calls = []
    const path = platform === 'win32' ? 'C:\\Canvas Data\\$(literal)' : '/tmp/Canvas Data/$(literal)'
    await openDataFolder(path, { platform, launch: async (...args) => { calls.push(args) } })
    assert.equal(calls[0][0], command)
    assert.deepEqual(calls[0][1], [path])
    assert.equal(calls[0][2].shell, false)
  }
})

test('Reset brings the latest projects and media back to the default and keeps both previous folders as backups', async t => {
  const { root, source, app, rpc } = await fixture(t)
  const { project, session, asset } = await seed(rpc)
  assert.equal((await rpc('/canvas-storage', 'info')).isDefault, true)
  const destination = join(root, 'Selected folder')
  await rpc('/canvas-storage', 'change', { dataDir: destination, expectedDataDir: source })
  assert.equal((await rpc('/canvas-storage', 'info')).defaultDataDir, source)
  assert.equal((await rpc('/canvas-storage', 'info')).isDefault, false)
  const current = await app.store.getProject(project.id)
  current.name = 'Latest canvas edits'
  await rpc('/video-director', 'projects/save', { projectId: project.id, project: current, expectedRevision: current.revision })
  const { project: extra } = await rpc('/video-director', 'projects/create', { name: 'Created after moving', sessionId: session.id })
  await writeFile(join(source, 'keep.txt'), 'Original default folder contents')

  const reset = await rpc('/canvas-storage', 'reset', { expectedDataDir: destination, dataDir: '/ignored-client-path' })
  assert.equal(reset.dataDir, source)
  assert.equal(reset.defaultDataDir, source)
  assert.equal(reset.isDefault, true)
  assert.equal(reset.previousDataDir, destination)
  assert.ok(reset.backupDataDir.startsWith(`${source}.backup-`))
  assert.equal(await readFile(join(reset.backupDataDir, 'keep.txt'), 'utf8'), 'Original default folder contents')
  assert.equal(JSON.parse(await readFile(join(reset.backupDataDir, 'projects', project.id, 'project.json'), 'utf8')).name, 'Storage migration')
  assert.equal(JSON.parse(await readFile(join(destination, 'projects', project.id, 'project.json'), 'utf8')).name, 'Latest canvas edits')
  assert.equal((await app.store.getProject(project.id)).name, 'Latest canvas edits')
  assert.equal((await app.store.assetBytes(asset.id)).data.toString(), 'saved image bytes')
  assert.equal((await rpc('/canvas-sessions', 'get', { sessionId: session.id })).id, session.id)
  assert.equal((await rpc('/canvas-storage', 'reset', { expectedDataDir: source })).backupDataDir, null)
  await app.close()
  const restarted = await createCanvasServer({ fetchCodexModels: fetchTestModels, dataDir: source, providers: defaultProviders({}) })
  try {
    assert.equal(restarted.store.root, source)
    assert.equal((await restarted.store.getProject(extra.id)).name, 'Created after moving')
    const movedAgain = join(root, 'Moved again')
    await restarted.rpc('/canvas-storage', 'change', { dataDir: movedAgain, expectedDataDir: source })
    assert.equal(restarted.store.root, movedAgain)
  } finally { await restarted.close() }
})

test('Folder selection cancels without changing data, and only one native dialog can be open', async t => {
  const gate = Promise.withResolvers()
  const entered = Promise.withResolvers()
  const choices = []
  const { root, source, rpc, request } = await fixture(t, { chooseFolder: async (path, options) => {
    choices.push({ path, language: options.language })
    entered.resolve()
    return gate.promise
  } })
  const selection = rpc('/canvas-storage', 'choose', { language: 'zh' })
  await entered.promise
  try {
    assert.equal((await request('/canvas-storage', 'choose')).status, 409)
    assert.equal((await rpc('/canvas-storage', 'info')).dataDir, source)
  } finally { gate.resolve(null) }
  assert.deepEqual(await selection, { dataDir: null })
  assert.deepEqual(choices, [{ path: source, language: 'zh' }])
  await assert.rejects(stat(join(source, '.canvas-storage.json')), { code: 'ENOENT' })
  const selectedApp = await createCanvasServer({ fetchCodexModels: fetchTestModels, dataDir: source, chooseFolder: async () => join(root, 'Chosen by user') })
  try {
    const result = await selectedApp.rpc('/canvas-storage', 'choose')
    assert.equal(result.value.dataDir, join(root, 'Chosen by user'))
    assert.equal(selectedApp.store.root, source)
  } finally { await selectedApp.close() }
})

test('Native folder choosers keep paths out of executable scripts and handle cancellation and Linux fallback', async () => {
  for (const platform of ['darwin', 'win32', 'linux']) {
    const path = platform === 'win32' ? "C:\\Canvas Data\\'$(literal)" : "/tmp/Canvas Data/'$(literal)"
    const calls = []
    const selected = await chooseDataFolder(path, { platform, language: 'zh', launch: async (...args) => {
      calls.push(args)
      return { stdout: '/tmp/chosen folder/\n' }
    } })
    assert.equal(selected, '/tmp/chosen folder')
    const [command, args, options] = calls[0]
    assert.equal(options.shell, false)
    if (platform === 'darwin') {
      assert.equal(command, 'osascript')
      assert.equal(args[1].includes(path), false)
      assert.equal(args[2], path)
    } else if (platform === 'win32') {
      assert.equal(command, 'powershell.exe')
      assert.equal(Buffer.from(args.at(-1), 'base64').toString('utf16le').includes(path), false)
      assert.equal(options.env.CANVAS_FOLDER_PICKER_PATH, path)
    } else assert.ok(args.includes(`--filename=${path}/`))
    assert.equal(await chooseDataFolder(path, { platform, launch: async () => ({ stdout: '' }) }), null)
  }
  const calls = []
  assert.equal(await chooseDataFolder('/tmp', { platform: 'linux', launch: async command => {
    calls.push(command)
    throw Object.assign(new Error('fixture'), { code: command === 'zenity' ? 'ENOENT' : 1 })
  } }), null)
  assert.deepEqual(calls, ['zenity', 'kdialog'])
  await assert.rejects(chooseDataFolder('/tmp', { platform: 'linux', launch: async () => { throw Object.assign(new Error('missing'), { code: 'ENOENT' }) } }), /Install Zenity or KDialog/u)
})
