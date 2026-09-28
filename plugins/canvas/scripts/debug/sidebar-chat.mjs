// Isolated QA: actual Canvas HTTP/SDK adapter, simulated Codex and providers, synthetic media.
// Run from the plugin root after npm run build. Requires FFmpeg. Ctrl-C removes the temporary data.
import { mkdtemp, mkdir, readFile, rm, writeFile } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { execFileSync } from 'node:child_process'
import { createCanvasServer } from '../../src/server.js'
import { fetchTestModels } from '../../test/fixtures/codex-models.js'
import { providerConnectionsFixture } from '../../test/fixtures/provider-connections.js'

const root = await mkdtemp(join(tmpdir(), 'canvas-sidebar-qa-'))
const providers = providerConnectionsFixture()
let app
try {
  app = await createCanvasServer({ dataDir: join(root, 'store'), providers: providers.providers,
    fetchCodexModels: fetchTestModels, providerOptions: { fetchImpl: providers.fetchImpl },
    createCodex: ({ config }) => {
      const run = () => ({ runStreamed: async () => ({ events: (async function* () {
        const { url, http_headers } = config.mcp_servers.canvas
        const command = async (command, args = {}) => {
          const response = await fetch(url, { method: 'POST', headers: { ...http_headers, 'Content-Type': 'application/json' },
            body: JSON.stringify({ jsonrpc: '2.0', id: command, method: 'tools/call', params: { name: 'vd_canvas', arguments: { command, args } } }) })
          const { result } = await response.json()
          if (result.isError) throw new Error(result.content[0].text)
          return JSON.parse(result.content[0].text)
        }
        const summary = await command('summary')
        yield { type: 'item.started', item: { id: 'qa-tool', type: 'mcp_tool_call', tool: 'vd_canvas', status: 'in_progress', arguments: { command: 'edit' } } }
        await command('edit', { expectedDraftRevision: summary.draftRevision,
          edits: [{ op: 'add', kind: 'load-text', position: { x: 70, y: 420 }, data: { title: 'Created through Codex MCP', text: 'Synthetic QA note. No live model or generation provider was called.' } }] })
        yield { type: 'item.completed', item: { id: 'qa-tool', type: 'mcp_tool_call', tool: 'vd_canvas', status: 'completed', arguments: { command: 'edit' } } }
        yield { type: 'item.completed', item: { id: `qa-answer-${Date.now()}`, type: 'agent_message', text: 'Simulated Codex: added a Text node through the authenticated Canvas tool.' } }
      })() }) })
      return { startThread: run, resumeThread: run }
    },
  })
  // No fixture action may reach the real Codex CLI or a paid provider.
  app.providers.codexPlan.check = () => {}
  app.providers.run = async () => { throw new Error('This QA fixture disables generation. Use chat to test a simulated canvas edit.') }
  const session = await app.sessions.create()
  const project = await app.store.createProject({ name: 'Synthetic Codex sidebar QA', sessionId: session.id })
  await mkdir(join(root, 'Shot references', 'Scenes'), { recursive: true })
  await writeFile(join(root, 'Shot references', 'Scenes', 'script.txt'), 'Synthetic scene: a paper boat crosses a pond.')
  for (const [name, args] of [
    ['color.png', ['-f', 'lavfi', '-i', 'color=c=royalblue:size=240x160', '-frames:v', '1']],
    ['tone.wav', ['-f', 'lavfi', '-i', 'sine=frequency=440:sample_rate=44100', '-t', '2']],
    ['bars.mp4', ['-f', 'lavfi', '-i', 'testsrc2=size=320x240:rate=24', '-t', '2', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-movflags', '+faststart']],
  ]) execFileSync('ffmpeg', ['-hide_banner', '-loglevel', 'error', ...args, join(root, name)])
  const image = (await readFile(join(root, 'color.png'))).toString('base64')
  for (let index = 0; index < 46; index++) await app.store.putAsset({ projectId: project.id, kind: 'image', mimeType: 'image/png',
    name: `scene-${String(index).padStart(2, '0')}.png`, origin: index < 23 ? 'output' : 'input', dataBase64: image })
  for (const [kind, name, mimeType] of [['video', 'bars.mp4', 'video/mp4'], ['audio', 'tone.wav', 'audio/wav']]) {
    await app.store.putAsset({ projectId: project.id, kind, name, mimeType, dataBase64: (await readFile(join(root, name))).toString('base64') })
  }
  await app.store.cacheDraft(project.id, { name: project.name, settings: project.settings, graph: { nodes: [
    { id: 'script', type: 'director', position: { x: 60, y: 70 }, data: { kind: 'load-text', title: 'Opening scene', text: 'A paper boat crosses a blue pond.', status: 'idle' } },
    { id: 'image', type: 'director', position: { x: 440, y: 70 }, data: { kind: 'load-image', title: 'Storyboard frame', mediaKind: 'image', status: 'idle' } },
  ], edges: [], viewport: { x: 15, y: 10, zoom: .85 } } })
  const url = await app.listen(0)
  console.log(JSON.stringify({ url, fixtureRoot: root, projectId: project.id, simulatedCodex: true }))
} catch (error) { await app?.close(); await rm(root, { recursive: true, force: true }); throw error }
for (const event of ['SIGINT', 'SIGTERM']) process.once(event, async () => {
  await app.close(); await rm(root, { recursive: true, force: true }); process.exit(0)
})
