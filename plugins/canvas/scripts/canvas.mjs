import { readFile } from 'node:fs/promises'

const args = process.argv.slice(2)
const endpoint = args.shift()
if (!endpoint || endpoint === '--help') {
  console.log('Usage: node scripts/canvas.mjs <RPC endpoint> [--file payload.json] [--url http://127.0.0.1:8765]\nExamples: health, projects/list, providers/list, workflows/list, nodes/list, projects/get, projects/create, projects/save\nPayloads are JSON objects. Mutating endpoints change the local Canvas. Generation uses the selected provider account.\nUse --channel /canvas-sessions for session list/create/get/start/cancel/model/rename.')
  process.exit(0)
}
const options = {}
for (let index = 0; index < args.length; index += 2) {
  if (!['--file', '--url', '--channel'].includes(args[index]) || !args[index + 1]) throw new Error(`Unknown or incomplete option: ${args[index]}`)
  options[args[index].slice(2)] = args[index + 1]
}
const address = new URL(options.url || process.env.CANVAS_URL || `http://127.0.0.1:${process.env.CANVAS_PORT || 8765}`)
if (address.protocol !== 'http:' || !['127.0.0.1', 'localhost'].includes(address.hostname)) throw new Error('Connect to a local Canvas HTTP server.')
const payload = options.file ? JSON.parse(await readFile(options.file, 'utf8')) : {}
try {
  const response = await fetch(new URL('/api/rpc', address), { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ channel: options.channel || '/video-director', endpoint, payload }), signal: AbortSignal.timeout(120_000) })
  const result = await response.json()
  if (!response.ok || !result.ok) throw new Error(result.error?.message ?? result.error ?? `HTTP ${response.status}`)
  console.log(JSON.stringify(result.value, null, 2))
} catch (error) { console.error(error.message); process.exitCode = 1 }
