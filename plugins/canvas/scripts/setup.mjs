import { spawnSync } from 'node:child_process'
import { fileURLToPath } from 'node:url'

const root = fileURLToPath(new URL('../', import.meta.url))
const major = Number(process.versions.node.split('.')[0])
if (major < 22 || major === 23 || (major === 22 && Number(process.versions.node.split('.')[1]) < 19)) {
  console.error('Install Node.js 22.19+ (22.x) or 24+ before setting up Canvas.')
  process.exit(1)
}
const npm = process.platform === 'win32' ? 'npm.cmd' : 'npm'
for (const args of [['ci', '--include=dev', '--no-audit', '--no-fund'], ['run', 'build']]) {
  const result = spawnSync(npm, args, { cwd: root, stdio: 'inherit', shell: process.platform === 'win32' })
  if (result.error) { console.error(result.error.message); process.exit(1) }
  if (result.status !== 0) process.exit(result.status ?? 1)
}
console.log('Canvas is ready. Run npm run doctor, then npm start from this directory.')
