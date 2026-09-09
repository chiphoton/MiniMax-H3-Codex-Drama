import { mkdir, writeFile } from 'node:fs/promises'
import { fileURLToPath } from 'node:url'
import { build } from 'esbuild'

const root = fileURLToPath(new URL('../', import.meta.url))
await mkdir(`${root}dist`, { recursive: true })
await build({
  absWorkingDir: root,
  entryPoints: ['src/client/index.tsx'],
  outfile: 'dist/client.js',
  bundle: true,
  format: 'esm',
  platform: 'browser',
  target: ['es2022'],
  jsx: 'automatic',
  loader: { '.css': 'text' },
  define: { 'process.env.NODE_ENV': '"production"' },
  sourcemap: true,
  minify: true,
  legalComments: 'linked',
})
await writeFile(`${root}dist/index.html`, `<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="referrer" content="no-referrer"><title>Codex Drama · Canvas</title><style>body{margin:0;background:#080b12;color:#e8edf5;font:14px system-ui}#root>p{padding:24px}</style></head><body><div id="root"><p>Loading Canvas…</p></div><script type="module" src="/client.js"></script></body></html>\n`)
console.log('Built Canvas into dist/')
