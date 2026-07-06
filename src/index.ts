import { Hono } from 'hono'

// Inisialisasi aplikasi Hono
const app = new Hono()

// Definisikan route untuk root URL ('/')
app.get('/', (c) => {
  return c.text('Hello from Sribuu on Cloudflare Workers!')
})

// Export aplikasi agar bisa dijalankan oleh Cloudflare
export default app
