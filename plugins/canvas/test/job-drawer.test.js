import assert from 'node:assert/strict'
import { fileURLToPath } from 'node:url'
import { createRequire } from 'node:module'
import test from 'node:test'
import { build } from 'esbuild'
import { JSDOM } from 'jsdom'

const dom = new JSDOM('<div id="root"></div>', { url: 'http://localhost/', pretendToBeVisual: true })
test.after(() => dom.window.close())
for (const key of ['window', 'document', 'navigator', 'localStorage', 'Node', 'Element', 'HTMLElement']) {
  Object.defineProperty(globalThis, key, { value: dom.window[key], configurable: true })
}
globalThis.IS_REACT_ACT_ENVIRONMENT = true
window.confirm = () => true
const bundle = await build({ stdin: {
  resolveDir: fileURLToPath(new URL('../src/client/', import.meta.url)), loader: 'tsx', contents: `
    import React from 'react'; import {createRoot} from 'react-dom/client';
    import {JobDrawer} from './JobDrawer'; export {act} from 'react'; export {setLanguage} from './i18n';
    export function mount(snapshot, director) {const root=createRoot(document.getElementById('root'));
      const render=snapshot=>root.render(<JobDrawer snapshot={snapshot} director={director} onClose={()=>{}}/>);
      render(snapshot);return {render, unmount:()=>root.unmount()};}
  `,
}, bundle: true, format: 'cjs', platform: 'node', packages: 'external', write: false, define: { 'process.env.NODE_ENV': '"development"' } })
const compiled = { exports: {} }
new Function('require', 'module', 'exports', bundle.outputFiles[0].text)(createRequire(import.meta.url), compiled, compiled.exports)
const ui = compiled.exports

async function mount(t) {
  const jobs = [{ id: 'alpha-job', projectId: 'alpha', nodeId: 'same', workflowRunId: 'alpha-run', status: 'running', phase: 'working', progress: .5, providerId: 'fixture', createdAt: '2026-09-18T01:00:00.000Z' }]
  const run = { id: 'alpha-run', projectId: 'alpha', mode: 'all', status: 'running', startedAt: '2026-09-18T01:00:00.000Z', batchSize: 1, completedJobs: 0, totalJobs: 1 }
  const snapshot = { project: { id: 'beta' }, workflowRuns: [run], taskProjects: [
    { id: 'alpha', name: 'Alpha workflow', nodes: [{ id: 'same', title: 'Alpha generator' }], jobs, runs: [run] },
    { id: 'beta', name: 'Beta workflow', nodes: [{ id: 'same', title: 'Beta generator' }], runs: [], jobs: [{ ...jobs[0], id: 'beta-job', projectId: 'beta', workflowRunId: undefined, status: 'failed', createdAt: '2026-09-18T02:00:00.000Z' }] },
    { id: 'gamma', name: 'Queued workflow', nodes: [], jobs: [], runs: [{ ...run, id: 'gamma-run', projectId: 'gamma', status: 'queued', startedAt: '2026-09-18T03:00:00.000Z' }] },
  ] }
  const calls = []
  const director = Object.fromEntries(['refreshTasks', 'openVdWorkflow', 'cancelVdRun', 'cancelJob', 'runNode', 'deleteJob'].map(name => [name, async (...args) => { calls.push([name, ...args]) }]))
  let root
  await ui.act(async () => { ui.setLanguage('en'); root = ui.mount(snapshot, director) })
  t.after(() => { ui.act(() => root.unmount()) })
  return { snapshot, director, calls, root }
}
const button = (element, text) => [...element.querySelectorAll('button')].find(button => button.textContent === text)
function filter(id) { ui.act(() => { const select = document.querySelector('select'); select.value = id; select.dispatchEvent(new dom.window.Event('change', { bubbles: true })) }) }

test('Tasks starts with all workflows, shows queued runs without jobs, and retains its filter when switching canvas', async t => {
  const { snapshot, root } = await mount(t)
  assert.equal(document.querySelector('select').value, '')
  assert.equal(document.querySelectorAll('.vd-job-group').length, 3)
  assert.deepEqual([...document.querySelectorAll('.vd-job-workflow-name')].map(node => node.textContent), ['Queued workflow', 'Beta workflow', 'Alpha workflow'])
  assert.match(document.querySelector('.vd-job-list').textContent, /Alpha generator/)
  filter('alpha')
  assert.equal(document.querySelectorAll('.vd-job-group').length, 1)
  assert.doesNotMatch(document.querySelector('.vd-job-list').textContent, /Beta generator/)
  await ui.act(async () => root.render({ ...snapshot, project: { id: 'gamma' } }))
  assert.equal(document.querySelector('select').value, 'alpha')
  assert.equal(document.querySelectorAll('.vd-job-group').length, 1)
  filter('')
  assert.equal(document.querySelectorAll('.vd-job-group').length, 3)
})

test('Tasks cancellation, opening, retry and deletion use the job owning workflow', async t => {
  const { calls } = await mount(t)
  filter('alpha')
  await ui.act(async () => button(document, 'Cancel run').click())
  await ui.act(async () => button(document, 'Open workflow').click())
  assert.ok(calls.some(call => JSON.stringify(call) === JSON.stringify(['cancelVdRun', 'alpha-run', 'alpha'])))
  assert.ok(calls.some(call => JSON.stringify(call) === JSON.stringify(['openVdWorkflow', 'alpha-run', 'alpha'])))
  filter('beta')
  await ui.act(async () => button(document, 'Retry node').click())
  await ui.act(async () => button(document, 'Delete').click())
  assert.ok(calls.some(call => JSON.stringify(call) === JSON.stringify(['runNode', 'same', 'beta'])))
  assert.ok(calls.some(call => JSON.stringify(call) === JSON.stringify(['deleteJob', 'beta-job', 'beta'])))
})
