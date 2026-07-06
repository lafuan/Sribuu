import { Hono } from 'hono'

// Inisialisasi aplikasi Hono
const app = new Hono()

// Definisikan root route
app.get('/', (c) => {
  return c.text('Hello from Sribuu on Cloudflare Pages!')
})

// Export onRequest untuk Cloudflare Pages Functions
// [[path]] catch-all → semua request masuk ke Hono
export const onRequest = app.fetch
