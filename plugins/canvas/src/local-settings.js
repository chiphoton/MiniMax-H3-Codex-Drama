import { chmod, mkdir, readFile, rename, writeFile } from 'node:fs/promises'
import { dirname } from 'node:path'

/** Atomic, serialized local persistence for ProviderSettings' narrow write API. */
export async function localSettings(path) {
  let value = { providerOverrides: {} }
  try { value = JSON.parse(await readFile(path, 'utf8')); await chmod(path, 0o600) }
  catch (error) { if (error.code !== 'ENOENT') throw error }
  let tail = Promise.resolve()
  return {
    current: () => structuredClone(value),
    mutate(_namespace, operations) {
      const update = tail.then(async () => {
        const next = structuredClone(value)
        for (const operation of operations) {
          const [root, provider, field] = operation.path
          if (root !== 'providerOverrides' || ['__proto__', 'constructor', 'prototype'].includes(provider)
            || !['label', 'baseUrl', 'model', 'imageModel', 'apiKey', 'fastMode'].includes(field)) throw new Error('Invalid settings path')
          const overrides = next.providerOverrides ??= {}
          const target = overrides[provider] ??= {}
          if (operation.op === 'unset') delete target[field]
          else if (operation.op === 'set') target[field] = operation.value
          else throw new Error('Invalid settings operation')
        }
        await mkdir(dirname(path), { recursive: true, mode: 0o700 })
        await writeFile(`${path}.tmp`, `${JSON.stringify(next, null, 2)}\n`, { mode: 0o600 })
        await rename(`${path}.tmp`, path)
        value = next
      })
      tail = update.catch(() => {})
      return update
    },
  }
}
