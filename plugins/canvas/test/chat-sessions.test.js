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

test('resumed SDK turns can reuse item IDs without replacing earlier messages or tool results', async t => {
  const root = await mkdtemp(join(tmpdir(), 'codex-canvas-turn-ids-'))
  t.after(() => rm(root, { recursive: true, force: true }))
  let turn = 0
  const thread = { runStreamed: async () => {
    const current = ++turn
    return { events: (async function* () {
      yield { type: 'thread.started', thread_id: 'same-sdk-thread' }
      yield { type: 'item.started', item: { id: 'item_0', type: 'mcp_tool_call', tool: 'vd_canvas', status: 'in_progress', arguments: { command: 'summary' } } }
      yield { type: 'item.completed', item: { id: 'item_0', type: 'mcp_tool_call', tool: 'vd_canvas', status: 'completed', arguments: { command: 'summary' },
        result: { content: [{ type: 'text', text: `Result ${current}` }] } } }
      yield { type: 'item.started', item: { id: 'item_1', type: 'agent_message', text: 'Working' } }
      yield { type: 'item.completed', item: { id: 'item_1', type: 'agent_message', text: `Answer ${current}` } }
    })() }
  } }
  const createCodex = () => ({ startThread: () => thread, resumeThread: () => thread })
  let sessions = new ChatSessions(root, { codexModels: modelFixture(), createCodex })
  await sessions.init()
  const session = await sessions.create()
  for (const text of ['Build the workflow', 'Save without rerunning']) {
    await sessions.start(session.id, { text })
    await Promise.all([...sessions.active.values()].map(task => task.promise))
    await sessions.close()
    sessions = new ChatSessions(root, { codexModels: modelFixture(), createCodex })
    await sessions.init()
  }
  const messages = sessions.view(session.id).messages
  assert.equal(messages.length, 8)
  assert.equal(new Set(messages.map(message => message.id)).size, 8)
  assert.deepEqual(messages.filter(message => message.kind === 'assistant').map(message => message.text), ['Answer 1', 'Answer 2'])
  const calls = messages.filter(message => message.kind === 'tool-call')
  const results = messages.filter(message => message.kind === 'tool-result')
  assert.deepEqual(results.map(message => message.text), ['Result 1', 'Result 2'])
  assert.deepEqual(results.map(message => message.callId), calls.map(message => message.callId))
  assert.notEqual(calls[0].callId, calls[1].callId)
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

test('Codex transcripts retain model identity and local images across restart without cross-session reads', async t => {
  const root = await mkdtemp(join(tmpdir(), 'codex-canvas-transcript-'))
  t.after(() => rm(root, { recursive: true, force: true }))
  const data = Buffer.from('synthetic image').toString('base64')
  const createCodex = () => ({ startThread: () => ({ runStreamed: async () => ({ events: (async function* () {
    yield { type: 'item.completed', item: { id: 'inspect', type: 'mcp_tool_call', tool: 'vd_canvas', status: 'completed', arguments: { command: 'image' },
      result: { content: [{ type: 'text', text: 'Synthetic image' }, { type: 'image', mimeType: 'image/png', data }] } } }
    yield { type: 'item.completed', item: { id: 'answer', type: 'agent_message', text: '**Inspected** Image 1.' } }
  })() }) }) })
  let sessions = new ChatSessions(root, { codexModels: modelFixture(), createCodex })
  await sessions.init()
  const first = await sessions.create(); const other = await sessions.create()
  await sessions.start(first.id, { text: 'Inspect Image 1', images: [{ mimeType: 'image/png', name: 'synthetic.png', data }] })
  await Promise.all([...sessions.active.values()].map(task => task.promise))
  assert.equal(sessions.view(first.id).error, null)
  const messages = sessions.view(first.id).messages
  assert.equal(messages[0].text, 'Inspect Image 1')
  assert.equal(messages[1].toolCommand, 'image')
  assert.equal(messages[2].kind, 'tool-result')
  assert.deepEqual(messages[3].model, { provider: 'codex-plan', model: 'gpt-5.6-sol' })
  for (const message of [messages[0], messages[2]]) {
    const id = message.images[0].attachmentId
    assert.equal((await sessions.image(first.id, id)).data, data)
    await assert.rejects(sessions.image(other.id, id), /not found/)
  }
  await assert.rejects(sessions.image(first.id, '../outside.png'), /not found/)
  await sessions.close()
  sessions = new ChatSessions(root, { codexModels: modelFixture(), createCodex })
  await sessions.init()
  assert.equal((await sessions.image(first.id, messages[0].images[0].attachmentId)).data, data)
  assert.deepEqual(sessions.view(first.id).messages, messages)
  await sessions.close()
})
