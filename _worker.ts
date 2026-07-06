import { Hono } from 'hono'

const app = new Hono()

app.get('/', (c) => {
  return c.text('Hello from Sribuu on Cloudflare Pages!')
})

app.get('/api/health', (c) => {
  return c.json({ status: 'ok', timestamp: Date.now() })
})

app.onError((err, c) => {
  return c.text(`Error: ${err.message}`, 500)
})

// Pages Advanced Mode: export default with fetch()
// Replaces functions/ directory entirely
export default {
  fetch: app.fetch
}
