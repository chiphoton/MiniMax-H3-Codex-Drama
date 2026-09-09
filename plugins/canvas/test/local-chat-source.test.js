import assert from 'node:assert/strict'
import { fileURLToPath } from 'node:url'
import test from 'node:test'
import { build } from 'esbuild'

const bundle = await build({ entryPoints: [fileURLToPath(new URL('../src/client/chat-source.ts', import.meta.url))], bundle: true, format: 'esm', platform: 'browser', write: false })
const { ProjectChatSource } = await import(`data:text/javascript;base64,${Buffer.from(bundle.outputFiles[0].contents).toString('base64')}`)
const settle = () => new Promise(resolve => setImmediate(resolve))
const result = (id, text, running = false) => ({ ok: true, value: { id, model: 'gpt-5.6-sol', messages: [{ id: text, role: 'assistant', text }], running, error: null } })

function director(sessionId) {
  let current = { project: { id: sessionId, sessionId } }
  const listeners = new Set()
  return {
    getSnapshot: () => current,
    currentContext: () => 'Canvas context',
    subscribe: listener => { listeners.add(listener); return () => listeners.delete(listener) },
    switchTo(id) { current = { ...current, project: { id, sessionId: id } }; for (const listener of listeners) listener() },
    setProviders(providers) { current = { ...current, providers }; for (const listener of listeners) listener() },
  }
}

test('a slow chat poll cannot replace the state returned after a new submission', async t => {
  let releaseOld
  let reads = 0
  const ctx = { connection: { rpc: { call: async (_channel, endpoint) => {
    if (endpoint === 'start') return { ok: true, value: { accepted: true } }
    if (reads++ === 0) return new Promise(resolve => { releaseOld = resolve })
    return result('first', 'Current response', true)
  } } } }
  const chat = new ProjectChatSource(ctx, director('first'))
  t.after(() => chat.dispose())
  await chat.send('A new question')
  releaseOld(result('first', 'Old response', false))
  await settle()
  assert.equal(chat.getSnapshot().running, true)
  assert.equal(chat.getSnapshot().messages[0].text, 'Current response')
})

test('the chat model picker follows catalog refreshes without changing the session or saved selection', async t => {
  const ctx = { connection: { rpc: { call: async () => result('first', 'Existing response') } } }
  const source = director('first')
  const chat = new ProjectChatSource(ctx, source)
  t.after(() => chat.dispose())
  await settle()
  assert.deepEqual(chat.getSnapshot().models.groups[0].models, [])
  source.setProviders([{ id: 'codex-plan', kind: 'codex-plan', model: 'future-default', modelDiscovery: { state: 'ready' }, codexModels: [
    { id: 'gpt-5.6-sol', displayName: 'Saved model', defaultReasoningEffort: 'low' },
    { id: 'future-default', displayName: 'New variant', defaultReasoningEffort: 'ultra' },
  ] }])
  assert.equal(chat.getSnapshot().sessionId, 'first')
  assert.deepEqual(chat.getSnapshot().models.current, { provider: 'codex-plan', model: 'gpt-5.6-sol', reasoningEffort: 'low' })
  assert.equal(chat.getSnapshot().models.groups[0].models[1].reasoning.defaultEffort, 'ultra')
  source.setProviders([{ id: 'codex-plan', kind: 'codex-plan', modelDiscovery: { state: 'error', message: 'Offline' }, codexModels: [] }])
  assert.equal(chat.getSnapshot().models.current.model, 'gpt-5.6-sol')
  assert.equal(chat.getSnapshot().models.routable, false)
  assert.equal(chat.getSnapshot().models.error, 'Offline')
  assert.equal(chat.getSnapshot().messages[0].text, 'Existing response')
})

test('switching projects discards delayed chat responses from the previous project', async t => {
  let releaseFirst
  const ctx = { connection: { rpc: { call: async (_channel, _endpoint, payload) => {
    if (payload.sessionId === 'first') return new Promise(resolve => { releaseFirst = resolve })
    return result('second', 'Second project')
  } } } }
  const source = director('first')
  const chat = new ProjectChatSource(ctx, source)
  t.after(() => chat.dispose())
  source.switchTo('second')
  await settle()
  releaseFirst(result('first', 'Private first project'))
  await settle()
  assert.equal(chat.getSnapshot().sessionId, 'second')
  assert.equal(chat.getSnapshot().messages[0].text, 'Second project')
})
