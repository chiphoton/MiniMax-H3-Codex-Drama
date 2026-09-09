import { spawnSync } from 'node:child_process'
import { access } from 'node:fs/promises'
import { constants } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dataDirectory, DEFAULT_PORT } from '../src/config.js'
import { codexRuntimeAccess } from '../src/codex-environment.js'
import { codexExecutable } from '../src/codex-executable.js'
import { loadStorageLocation } from '../src/storage.js'

const root = fileURLToPath(new URL('../', import.meta.url))
const rows = []
const check = (name, status, detail) => rows.push({ name, status, detail })
let resolvedDataDir = dataDirectory()
try {
  resolvedDataDir = (await loadStorageLocation(resolvedDataDir)).dataDir
  check('Canvas storage', 'ok', resolvedDataDir)
} catch (error) { check('Canvas storage', 'required', error.message) }
const nodeParts = process.versions.node.split('.').map(Number)
const supported = (nodeParts[0] === 22 && nodeParts[1] >= 19) || nodeParts[0] >= 24
check('Node.js', supported ? 'ok' : 'required', process.version + (supported ? '' : '; install Node 22.19+ (22.x) or 24+'))
for (const [name, path] of [['Dependencies', 'node_modules/@openai/codex-sdk/package.json'], ['Browser build', 'dist/index.html']]) {
  try { await access(root + path, constants.R_OK); check(name, 'ok', 'present') }
  catch { check(name, 'required', 'Run node scripts/setup.mjs from the plugin directory') }
}
const codexCommand = codexExecutable()
const codexRuntime = codexRuntimeAccess()
check('Codex runtime access (this process)', codexRuntime.ok ? 'ok' : 'required', codexRuntime.detail)
const cli = spawnSync(codexCommand, ['--version'], { encoding: 'utf8', timeout: 10_000 })
check('Codex CLI', cli.status === 0 ? 'ok' : 'required', cli.status === 0 ? cli.stdout.trim() : 'Install Codex CLI or set CANVAS_CODEX_PATH to its executable')
if (cli.status === 0) {
  const login = spawnSync(codexCommand, ['login', 'status'], { encoding: 'utf8', timeout: 10_000 })
  check('Codex sign-in', login.status === 0 ? 'ok' : 'required', login.status === 0 ? 'Signed in; image-generation capability is checked on first use' : 'Run codex login interactively; do not paste credentials into chat')
}
for (const command of ['ffmpeg', 'ffprobe']) {
  const probe = spawnSync(command, ['-version'], { encoding: 'utf8', timeout: 5000 })
  check(command, probe.status === 0 ? 'ok' : 'optional', probe.status === 0 ? 'available' : 'Needed for local finishing with the Drama production plugin')
}
if (process.argv.includes('--probe')) {
  const targets = [['Canvas server', process.env.CANVAS_URL || `http://127.0.0.1:${process.env.CANVAS_PORT || DEFAULT_PORT}`, '/health'], ['ComfyUI', process.env.COMFYUI_URL || 'http://127.0.0.1:8188', '/system_stats']]
  for (const [name, address, suffix] of targets) {
    try {
      const url = new URL(address.includes('://') ? address : `http://${address}`)
      url.pathname = url.pathname.replace(/\/$/u, '') + suffix
      const response = await fetch(url, { signal: AbortSignal.timeout(3000) })
      check(name, response.ok ? 'ok' : 'optional', response.ok ? 'responding' : `HTTP ${response.status}`)
      if (name === 'Canvas server' && response.ok) {
        const health = await response.json()
        if (typeof health.dataDir === 'string') check('Canvas data folder (server)', 'ok', health.dataDir)
        const runtime = health.codexRuntime
        check('Codex runtime access (Canvas server)', runtime?.ok ? 'ok' : 'required', runtime?.detail ?? 'Restart Canvas with the updated server to check its runtime access')
      }
    } catch { check(name, 'optional', 'Not responding; start only if needed for this task') }
  }
}
const report = { ok: !rows.some(row => row.status === 'required'), dataDir: resolvedDataDir, checks: rows }
if (process.argv.includes('--json')) console.log(JSON.stringify(report, null, 2))
else {
  for (const row of rows) console.log(`${row.status.toUpperCase().padEnd(8)} ${row.name}: ${row.detail}`)
  console.log(`Data directory: ${report.dataDir}`)
}
if (!report.ok) process.exitCode = 1
