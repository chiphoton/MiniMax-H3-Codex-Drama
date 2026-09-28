import { ChatAttachmentRegistry } from './chat-attachments'
import type { DirectorController } from './controller'
import type { ChatMessage, ChatModelDirectoryState, ChatModelSelection, ChatSnapshot, ClientContext, ProviderDescriptor } from './types'

export interface ProjectChatMessage extends ChatMessage {
  kind: 'user' | 'assistant' | 'tool-call' | 'tool-result'
  toolName?: string
  callId?: string
  status: 'pending' | 'streaming' | 'complete' | 'error'
}

export interface ProjectChatSnapshot extends Omit<ChatSnapshot, 'messages'> {
  projectId: string | null
  messages: ProjectChatMessage[]
  models: ChatModelDirectoryState
}

interface LocalSession {
  id: string
  model: string | null
  messages: ProjectChatMessage[]
  running: boolean
  error: string | null
}

function modelDirectory(selectedModel: string | null, provider?: ProviderDescriptor): ChatModelDirectoryState {
  const model = selectedModel ?? provider?.model
  const available = provider?.codexModels ?? []
  const selected = available.find(candidate => candidate.id === model)
  const error = provider?.modelDiscovery?.message ?? provider?.codexCatalog?.error ?? null
  return {
    current: model ? { provider: 'codex-plan', model, reasoningEffort: selected?.defaultReasoningEffort } : null,
    routable: selected !== undefined,
    groups: [{ id: 'codex-plan', name: 'Codex Plan', models: available.map(model => ({ id: model.id, name: model.displayName, reasoning: { defaultEffort: model.defaultReasoningEffort } })) }],
    failures: [], status: provider?.modelDiscovery?.state ?? 'idle', error,
  }
}

async function encodeImage(file: File): Promise<{ mimeType: string; data: string }> {
  if (file.size > 20 * 1024 * 1024) throw new Error('Chat images must be 20 MB or smaller.')
  const bytes = new Uint8Array(await file.arrayBuffer())
  let binary = ''
  for (let offset = 0; offset < bytes.length; offset += 32768) binary += String.fromCharCode(...bytes.subarray(offset, offset + 32768))
  return { mimeType: file.type, data: btoa(binary) }
}

export class ProjectChatSource {
  private snapshot: ProjectChatSnapshot = { projectId: null, sessionId: null, messages: [], running: false, sending: false, error: null, models: modelDirectory(null) }
  private sessionModel: string | null = null
  private modelProvider?: ProviderDescriptor
  private listeners = new Set<() => void>()
  private timer: ReturnType<typeof setTimeout> | undefined
  private generation = 0
  private refreshVersion = 0
  private dismissedError: string | null = null
  private disposed = false
  private readonly attachmentRegistries = new Map<string, ChatAttachmentRegistry>()
  private release: () => void

  constructor(private ctx: ClientContext, private director: DirectorController) {
    this.release = director.subscribe(this.follow)
    this.follow()
  }

  getSnapshot = (): ProjectChatSnapshot => this.snapshot
  subscribe = (listener: () => void): (() => void) => { this.listeners.add(listener); return () => { this.listeners.delete(listener) } }
  private publish(patch: Partial<ProjectChatSnapshot>): void {
    if (this.disposed) return
    this.snapshot = { ...this.snapshot, ...patch }
    for (const listener of this.listeners) listener()
  }
  private async rpc<T>(endpoint: string, payload: unknown): Promise<T> {
    const result = await this.ctx.connection.rpc.call('/canvas-sessions', endpoint, payload)
    if (!result.ok) throw new Error(result.error.message)
    return result.value as T
  }
  private follow = (): void => {
    const { project, providers } = this.director.getSnapshot()
    const provider = providers?.find(candidate => candidate.kind === 'codex-plan')
    if (provider !== this.modelProvider) {
      this.modelProvider = provider
      this.publish({ models: modelDirectory(this.sessionModel, provider) })
    }
    if ((project?.sessionId ?? null) === this.snapshot.sessionId) return
    this.generation++
    this.dismissedError = null
    this.sessionModel = null
    clearTimeout(this.timer)
    this.publish({ projectId: project?.id ?? null, sessionId: project?.sessionId ?? null, messages: [], running: false, sending: false, error: null, models: modelDirectory(null, provider) })
    if (project) void this.refresh(this.generation)
  }
  private async refresh(generation: number): Promise<void> {
    const sessionId = this.snapshot.sessionId
    if (!sessionId || this.disposed || generation !== this.generation) return
    const version = ++this.refreshVersion
    try {
      const row = await this.rpc<LocalSession>('get', { sessionId })
      if (this.disposed || generation !== this.generation || version !== this.refreshVersion) return
      this.sessionModel = row.model
      this.publish({ messages: row.messages, running: row.running, error: row.error === this.dismissedError ? null : row.error, models: modelDirectory(row.model, this.modelProvider) })
    } catch (error) {
      if (generation === this.generation && version === this.refreshVersion) this.publish({ error: String((error as Error).message) })
    } finally {
      if (!this.disposed && generation === this.generation && version === this.refreshVersion) {
        clearTimeout(this.timer)
        this.timer = setTimeout(() => void this.refresh(generation), this.snapshot.running ? 750 : 3000)
      }
    }
  }
  attachments(): ChatAttachmentRegistry {
    const project = this.director.getSnapshot().project
    if (!project) throw new Error('Select a workflow first')
    const key = `${project.id}:${project.sessionId}`
    let registry = this.attachmentRegistries.get(key)
    if (!registry) {
      registry = new ChatAttachmentRegistry(input => this.director.chatReferences(input), project.id, project.sessionId)
      this.attachmentRegistries.set(key, registry)
    }
    return registry
  }

  async sendAttachments(text: string): Promise<void> {
    const project = this.director.getSnapshot().project
    if (this.snapshot.sending || this.snapshot.running) throw new Error('Wait for the current response to finish.')
    await this.director.prepareChatContext()
    if (this.director.getSnapshot().project?.sessionId !== project?.sessionId) throw new Error('The chat session changed during upload')
    const registry = this.attachments()
    const selected = registry.getSnapshot().filter(item => !item.sent || text.includes(item.alias))
    const prepared = await registry.prepare(selected)
    if (this.director.getSnapshot().project?.sessionId !== project?.sessionId) throw new Error('The chat session changed during upload')
    // Only explicitly used/new images enter this turn; other media stays on the Host.
    const images = prepared.filter(item => item.kind === 'image' && item.file && item.file.size <= 8 * 1024 * 1024).map(item => item.file!)
    const references = prepared.map(({ alias, kind, name, nodeId }) => ({ alias, kind, name, nodeId }))
    await this.send(text || references.map(item => item.alias).join(' '), images, JSON.stringify({ attachments: references }))
    await registry.markSent(prepared)
  }

  send = async (text: string, images: readonly File[] = [], attachmentContext = ''): Promise<void> => {
    const sessionId = this.snapshot.sessionId
    if (!sessionId) throw new Error('Select a workflow first.')
    if (this.snapshot.sending || this.snapshot.running) throw new Error('Wait for the current response to finish.')
    const generation = this.generation
    const projectId = this.snapshot.projectId
    const context = this.director.currentContext() + (attachmentContext ? `\n${attachmentContext}` : '')
    this.dismissedError = null
    this.publish({ sending: true, error: null })
    try {
      const encoded = await Promise.all(images.map(encodeImage))
      if (generation !== this.generation || this.disposed) throw new Error('The chat session changed during upload')
      await this.rpc('start', { sessionId, projectId, text, context, images: encoded })
      if (generation === this.generation) await this.refresh(generation)
    } catch (error) {
      if (generation === this.generation) this.publish({ error: (error as Error).message })
      throw error
    } finally {
      if (generation === this.generation) this.publish({ sending: false })
    }
  }
  selectModel = async (selection: ChatModelSelection): Promise<void> => {
    const generation = this.generation
    await this.rpc('model', { sessionId: this.snapshot.sessionId, model: selection.model })
    await this.refresh(generation)
  }
  cancel = async (): Promise<void> => {
    await this.rpc('cancel', { sessionId: this.snapshot.sessionId })
    await this.refresh(this.generation)
  }
  clearError = (): void => { this.dismissedError = this.snapshot.error; this.publish({ error: null }) }
  dispose = (): void => { this.disposed = true; this.generation++; clearTimeout(this.timer); this.release(); for (const registry of this.attachmentRegistries.values()) registry.dispose(); this.attachmentRegistries.clear(); this.listeners.clear() }
}
