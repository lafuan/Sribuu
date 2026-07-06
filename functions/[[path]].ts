import { Hono } from 'hono'

const app = new Hono()

app.get('/', (c) => {
  return c.text('Hello from Sribuu on Cloudflare Pages!')
})

app.get('/api/health', (c) => {
  return c.json({ status: 'ok', platform: 'cloudflare-pages', timestamp: Date.now() })
})

app.onError((err, c) => {
  console.error('Pages Function Error:', err.message)
  return c.text(`Error: ${err.message}`, 500)
})

export const onRequest = app.fetch
