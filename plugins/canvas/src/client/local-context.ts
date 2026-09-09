import type { ClientContext, RemoteResult, SessionBinding } from './types'

export async function canvasRpc<T>(channel: string, endpoint: string, payload: unknown = {}, signal?: AbortSignal): Promise<RemoteResult<T>> {
  const response = await fetch('/api/rpc', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ channel, endpoint, payload }),
    signal,
  })
  const result = await response.json() as RemoteResult<T>
  if (!response.ok && !('ok' in result)) throw new Error(`Canvas request failed (${response.status})`)
  return result
}

export async function sessionRpc<T>(endpoint: string, payload: unknown = {}, signal?: AbortSignal): Promise<T> {
  const result = await canvasRpc<T>('/canvas-sessions', endpoint, payload, signal)
  if (!result.ok) throw new Error(result.error.message)
  return result.value
}

export async function createLocalContext(): Promise<ClientContext> {
  const listeners = new Set<() => void>()
  const bindings = new Map<string, SessionBinding>()
  let snapshot: { current?: string; byId: Record<string, { id: string; title?: string }> } = { byId: {} }
  const publish = (): void => { for (const listener of listeners) listener() }
  const install = (session: { id: string; title?: string }): void => {
    snapshot = { ...snapshot, byId: { ...snapshot.byId, [session.id]: session } }
    bindings.set(session.id, {
      session: {
        getSnapshot: () => ({ id: session.id }),
        subscribe: () => () => {},
        rename: async title => {
          const result = await canvasRpc<{ title: string; seq: number }>('/canvas-sessions', 'rename', { sessionId: session.id, title })
          if (result.ok) { snapshot = { ...snapshot, byId: { ...snapshot.byId, [session.id]: { id: session.id, title } } }; publish() }
          return result
        },
      },
    })
  }
  const { sessions } = await sessionRpc<{ sessions: Array<{ id: string; title: string }> }>('list')
  for (const session of sessions) install(session)
  return {
    connection: { rpc: { call: canvasRpc } },
    sessions: {
      list: { getSnapshot: () => snapshot, subscribe: listener => { listeners.add(listener); return () => { listeners.delete(listener) } } },
      create: async options => {
        const session = await sessionRpc<{ id: string; title: string }>('create', options ?? {})
        install(session)
        publish()
        return session.id
      },
      open: sessionId => { snapshot = { ...snapshot, current: sessionId }; publish() },
      binding: sessionId => bindings.get(sessionId),
    },
  }
}
