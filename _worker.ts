import { Hono } from 'hono'

const app = new Hono()

app.get('/', (c) => {
  return c.text('Hello from Sribuu on Cloudflare Pages!')
})

app.get('/api/health', (c) => {
  return c.json({ status: 'ok', platform: 'cloudflare-pages', timestamp: Date.now() })
})

app.onError((err, c) => {
  console.error('Worker Error:', err.message)
  return c.text(`Error: ${err.message}`, 500)
})

// Cloudflare Pages Advanced Mode: export default with fetch
export default app
