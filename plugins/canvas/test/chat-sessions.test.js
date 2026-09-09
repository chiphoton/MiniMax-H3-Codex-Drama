import assert from 'node:assert/strict'
import { mkdtemp, rm } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import test from 'node:test'
import { ChatSessions } from '../src/chat-sessions.js'
import { modelFixture } from './fixtures/codex-models.js'

test('Canvas chat resumes its saved Codex thread and retains project isolation', async t => {
  const root = await mkdtemp(join(tmpdir(), 'codex-canvas-chat-'))
  t.after(() => rm(root, { recursive: true, force: true }))
  const calls = []
  const thread = {
    async runStreamed(content) {
      calls.push(content)
      return { events: (async function* () {
        yield { type: 'thread.started', thread_id: 'sdk-thread-1' }
        yield { type: 'item.completed', item: { id: `answer-${calls.length}`, type: 'agent_message', text: 'Connect text to image.' } }
      })() }
    },
  }
  const createCodex = () => ({
    startThread(options) { calls.push(options); return thread },
    resumeThread(id, options) { calls.push({ id, ...options }); return thread },
  })
  let sessions = new ChatSessions(root, { codexModels: modelFixture(), createCodex })
  await sessions.init()
  const first = await sessions.create()
  const second = await sessions.create()
  await sessions.start(first.id, { text: 'Help with this graph', context: '{"nodes":[]}' })
  await Promise.all([...sessions.active.values()].map(task => task.promise))
  assert.equal(sessions.view(first.id).messages[1].text, 'Connect text to image.')
  assert.equal(sessions.view(second.id).messages.length, 0)
  assert.equal(sessions.view(first.id).threadId, undefined)
  await sessions.close()
  sessions = new ChatSessions(root, { codexModels: modelFixture(), createCodex })
  await sessions.init()
  await sessions.start(first.id, { text: 'Continue' })
  await Promise.all([...sessions.active.values()].map(task => task.promise))
  assert.ok(calls.some(call => call.id === 'sdk-thread-1' && call.model === 'gpt-5.6-sol'))
  assert.equal(sessions.view(first.id).messages.filter(message => message.role === 'user').length, 2)
  await sessions.close()
})

test('Canvas chat supports cancellation and rejects overlapping turns and invalid images', async t => {
  const root = await mkdtemp(join(tmpdir(), 'codex-canvas-cancel-'))
  t.after(() => rm(root, { recursive: true, force: true }))
  const sessions = new ChatSessions(root, { codexModels: modelFixture(), createCodex: () => ({ startThread: () => ({
    async runStreamed(_content, { signal }) {
      return { events: (async function* () {
        await new Promise((resolve, reject) => {
          if (signal.aborted) reject(signal.reason)
          else signal.addEventListener('abort', () => reject(signal.reason), { once: true })
        })
      })() }
    },
  }) }) })
  await sessions.init()
  const row = await sessions.create()
  await assert.rejects(sessions.start(row.id, { text: 'Invalid', images: [{ mimeType: 'image/png', data: 'not-base64' }] }), /encoding/u)
  assert.equal(sessions.view(row.id).running, false)
  await sessions.start(row.id, { text: 'Long request' })
  await assert.rejects(sessions.start(row.id, { text: 'Duplicate' }), /already running/u)
  await assert.rejects(sessions.selectModel(row.id, 'gpt-5.6-terra'), /current response/u)
  const pending = sessions.active.get(row.id).promise
  sessions.cancel(row.id)
  await pending
  assert.equal(sessions.view(row.id).running, false)
  assert.equal(sessions.view(row.id).error, 'Response cancelled.')
  await sessions.close()
})
