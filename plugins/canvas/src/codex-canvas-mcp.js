import { randomBytes } from 'node:crypto'
import { canvasTool } from './canvas-agent.js'
import { libraryTool } from './library-agent.js'
import { qualityTool } from './quality-agent.js'
import { workspaceTool } from './workspace-agent.js'

const bearerToken = authorization => typeof authorization === 'string' && authorization.startsWith('Bearer ') ? authorization.slice(7) : undefined

/** Per-turn capabilities connect the SDK to the current runtime without exposing credentials to the browser. */
export class CodexCanvasMcp {
  constructor({ store, call, getUrl }) {
    this.store = store
    this.call = call
    this.getUrl = getUrl
    this.tokens = new Map()
    const host = { store, rpc: call }
    this.tools = [canvasTool(host), libraryTool(host), workspaceTool(host), qualityTool(host)]
  }

  async open({ projectId, sessionId, imageInput, signal }) {
    if (!projectId) {
      const projects = (await this.store.listProjects()).filter(project => project.sessionId === sessionId)
      if (projects.length !== 1) return null // Unbound legacy adviser conversations remain usable.
      projectId = projects[0].id
    }
    const project = await this.store.getProject(projectId)
    if (project.sessionId !== sessionId) throw new Error('Canvas tools require the workflow linked to this conversation.')
    const url = this.getUrl()
    if (!url) throw new Error('Start the Canvas HTTP server before sending canvas instructions.')
    signal.throwIfAborted()
    const token = randomBytes(32).toString('hex')
    const scope = { projectId, sessionId, imageInput, signal, requests: new Map() }
    const close = () => {
      this.tokens.delete(token)
      signal.removeEventListener('abort', close)
      for (const controller of scope.requests.values()) controller.abort()
    }
    this.tokens.set(token, scope)
    signal.addEventListener('abort', close, { once: true })
    return { close, config: { mcp_servers: { canvas: { url: `${url}/mcp/canvas`,
      http_headers: { Authorization: `Bearer ${token}` }, enabled_tools: this.tools.map(tool => tool.name),
      // The noninteractive SDK cannot answer MCP approval prompts. Trust only
      // these per-turn, project-scoped tools; content/run access is checked by
      // Canvas on every call. Other MCP servers keep their own approval policy.
      tools: Object.fromEntries(this.tools.map(tool => [tool.name, { approval_mode: 'approve' }])),
      tool_timeout_sec: 600 } } } }
  }

  authorized(authorization) { return this.tokens.has(bearerToken(authorization)) }

  /** Streamable HTTP, stateless JSON responses; the bearer capability owns the project/session. */
  async handle(authorization, message, requestSignal) {
    const scope = this.tokens.get(bearerToken(authorization))
    if (!scope || scope.signal.aborted) throw Object.assign(new Error('Canvas tool session expired'), { status: 401 })
    const id = message?.id ?? null
    const error = (code, message) => ({ jsonrpc: '2.0', id, error: { code, message } })
    const result = value => ({ jsonrpc: '2.0', id, result: value })
    if (!message || message.jsonrpc !== '2.0' || typeof message.method !== 'string' || Array.isArray(message)) return error(-32600, 'Invalid Request')
    if (message.id === undefined) {
      if (message.method === 'notifications/cancelled') scope.requests.get(message.params?.requestId)?.abort()
      return null
    }
    switch (message.method) {
      case 'initialize': return result({ protocolVersion: ['2024-11-05', '2025-03-26', '2025-06-18', '2025-11-25'].includes(message.params?.protocolVersion)
        ? message.params.protocolVersion : '2025-11-25', capabilities: { tools: {} }, serverInfo: { name: 'codex-canvas', version: '0.6.0' } })
      case 'ping': return result({})
      case 'tools/list': return result({ tools: this.tools.map(({ name, description, parameters }) => ({ name, description,
        inputSchema: { ...parameters, required: ['command'], properties: { ...parameters.properties,
          projectId: { type: 'string', description: 'Optional workflow ID; must match this conversation.' } } } })) })
      case 'tools/call': {
        const tool = this.tools.find(tool => tool.name === message.params?.name)
        if (!tool) return error(-32602, 'Unknown tool')
        const controller = new AbortController()
        scope.requests.set(id, controller)
        try {
          const input = message.params.arguments ?? {}
          if (input.projectId && input.projectId !== scope.projectId) throw new Error('Canvas tool can only access its owning workflow')
          if (tool.name === 'vd_canvas' && input.command === 'image' && !scope.imageInput) throw new Error('Select an image-capable chat model for visual quality control')
          const signal = AbortSignal.any([scope.signal, controller.signal, ...(requestSignal ? [requestSignal] : [])])
          const value = await tool.execute({ ...input, projectId: scope.projectId }, { sessionId: scope.sessionId, signal })
          return result({ content: value.image
            ? [{ type: 'text', text: value.name }, { type: 'image', mimeType: value.image.mediaType, data: value.image.data }]
            : [{ type: 'text', text: JSON.stringify(value) }] })
        } catch (failure) {
          return result({ isError: true, content: [{ type: 'text', text: failure.message }] })
        } finally { scope.requests.delete(id) }
      }
      default: return error(-32601, 'Method not found')
    }
  }
}
