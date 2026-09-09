import { createRoot } from 'react-dom/client'
import { DirectorOverlay } from './App'
import { DirectorController } from './controller'
import { ProjectChatSource } from './chat-source'
import { createLocalContext } from './local-context'

async function start(): Promise<void> {
  const ctx = await createLocalContext()
  const director = new DirectorController(ctx)
  const chat = new ProjectChatSource(ctx, director)
  const root = createRoot(document.getElementById('root')!)
  director.open()
  root.render(<DirectorOverlay director={director} chat={chat} />)
  await director.start()
  window.addEventListener('beforeunload', event => {
    if (director.getSnapshot().dirty) { event.preventDefault(); event.returnValue = '' }
  })
  window.addEventListener('pagehide', () => { chat.dispose(); director.dispose() }, { once: true })
}

void start().catch(error => {
  document.getElementById('root')!.textContent = `Canvas could not connect: ${error.message}. Check the local server and reload.`
})
