import { Hono } from 'hono'
import { cors } from 'hono/cors'

// --- Environment bindings ---
export interface Env {
  sribuu_db: D1Database
  // R2 binding akan ditambahkan nanti
  // ASSETS: R2Bucket
}

const app = new Hono<{ Bindings: Env }>()

// --- Middleware ---
app.use('*', cors())

// --- Root ---
app.get('/', (c) => {
  return c.text('Hello from Sribuu on Cloudflare Pages!')
})

// --- Health check ---
app.get('/api/health', (c) => {
  return c.json({ status: 'ok', platform: 'cloudflare-pages', timestamp: Date.now() })
})

// --- Categories: list all ---
app.get('/api/categories', async (c) => {
  try {
    const { results } = await c.env.sribuu_db.prepare(
      'SELECT id, name, icon, color, is_default, user_id FROM categories WHERE is_active = 1 ORDER BY is_default DESC, name ASC'
    ).all()
    return c.json(results)
  } catch (err) {
    console.error('/api/categories error:', err)
    return c.json({ error: 'Failed to load categories' }, 500)
  }
})

// --- Payment methods: list all ---
app.get('/api/payment-methods', async (c) => {
  try {
    const { results } = await c.env.sribuu_db.prepare(
      'SELECT id, name, icon FROM payment_methods WHERE is_active = 1 ORDER BY name ASC'
    ).all()
    return c.json(results)
  } catch (err) {
    console.error('/api/payment-methods error:', err)
    return c.json({ error: 'Failed to load payment methods' }, 500)
  }
})

// --- Transactions: recent (placeholder) ---
app.get('/api/transactions', async (c) => {
  try {
    const { results } = await c.env.sribuu_db.prepare(
      `SELECT t.id, t.amount, t.notes, t.transaction_date, 
              c.name as category_name, c.icon as category_icon, c.color as category_color,
              p.name as payment_method_name
       FROM transactions t
       LEFT JOIN categories c ON t.category_id = c.id
       LEFT JOIN payment_methods p ON t.payment_method_id = p.id
       ORDER BY t.transaction_date DESC, t.created_at DESC
       LIMIT 50`
    ).all()
    return c.json(results)
  } catch (err) {
    console.error('/api/transactions error:', err)
    return c.json({ error: 'Failed to load transactions' }, 500)
  }
})

// --- Error handler ---
app.onError((err, c) => {
  console.error('Worker Error:', err.message)
  return c.text(`Error: ${err.message}`, 500)
})

// Cloudflare Pages Advanced Mode
export default app
