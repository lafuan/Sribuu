import { Hono } from 'hono'
import { cors } from 'hono/cors'
import bcrypt from 'bcryptjs'

// --- Environment bindings ---
export interface Env {
  sribuu_db: D1Database
  JWT_SECRET: string
}

const app = new Hono<{ Bindings: Env; Variables: { userId: number; userEmail: string } }>()

// --- JWT helpers (Web Crypto API) ---
function b64url(input: ArrayBuffer): string {
  return btoa(String.fromCharCode(...new Uint8Array(input)))
    .replace(/=/g, '')
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
}

function fromB64url(str: string): Uint8Array {
  str = str.replace(/-/g, '+').replace(/_/g, '/')
  while (str.length % 4) str += '='
  return Uint8Array.from(atob(str), c => c.charCodeAt(0))
}

async function signJWT(payload: Record<string, unknown>, secret: string): Promise<string> {
  const header = b64url(new TextEncoder().encode(JSON.stringify({ alg: 'HS256', typ: 'JWT' })))
  const body = b64url(new TextEncoder().encode(JSON.stringify(payload)))
  const key = await crypto.subtle.importKey('raw', new TextEncoder().encode(secret), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign'])
  const sig = b64url(await crypto.subtle.sign('HMAC', key, new TextEncoder().encode(`${header}.${body}`)))
  return `${header}.${body}.${sig}`
}

async function verifyJWT(token: string, secret: string): Promise<Record<string, unknown> | null> {
  try {
    const parts = token.split('.')
    if (parts.length !== 3) return null
    const key = await crypto.subtle.importKey('raw', new TextEncoder().encode(secret), { name: 'HMAC', hash: 'SHA-256' }, false, ['verify'])
    const valid = await crypto.subtle.verify('HMAC', key, fromB64url(parts[2]), new TextEncoder().encode(`${parts[0]}.${parts[1]}`))
    if (!valid) return null
    const payload = JSON.parse(new TextDecoder().decode(fromB64url(parts[1])))
    if (payload.exp && payload.exp < Math.floor(Date.now() / 1000)) return null
    return payload
  } catch { return null }
}

// --- Auth middleware ---
async function authMiddleware(c: any, next: any) {
  const auth = c.req.header('Authorization')
  if (!auth?.startsWith('Bearer ')) return c.json({ error: 'Unauthorized' }, 401)
  const payload = await verifyJWT(auth.slice(7), c.env.JWT_SECRET)
  if (!payload) return c.json({ error: 'Invalid or expired token' }, 401)
  c.set('userId', payload.sub as number)
  c.set('userEmail', payload.email as string)
  await next()
}

// --- Middleware ---
app.use('*', cors())

// ============================================================
//  PUBLIC ROUTES
// ============================================================

app.get('/', (c) => c.text('Hello from Sribuu on Cloudflare Pages!'))

app.get('/api/health', (c) => c.json({ status: 'ok', platform: 'cloudflare-pages', timestamp: Date.now() }))

// --- Register ---
app.post('/api/auth/register', async (c) => {
  try {
    const { name, email, password } = await c.req.json()
    if (!name || !email || !password) {
      return c.json({ error: 'name, email, and password are required' }, 400)
    }
    if (password.length < 6) {
      return c.json({ error: 'Password must be at least 6 characters' }, 400)
    }

    // Check existing user
    const existing = await c.env.sribuu_db.prepare('SELECT id FROM users WHERE email = ?').bind(email).first()
    if (existing) return c.json({ error: 'Email already registered' }, 409)

    const hash = bcrypt.hashSync(password, 10)
    const { meta } = await c.env.sribuu_db.prepare(
      'INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)'
    ).bind(name, email, hash).run()

    const userId = meta.last_row_id
    const token = await signJWT({ sub: userId, email, name, iat: Math.floor(Date.now() / 1000), exp: Math.floor(Date.now() / 1000) + 86400 * 7 }, c.env.JWT_SECRET)

    return c.json({ user: { id: userId, name, email }, token }, 201)
  } catch (err) {
    console.error('Register error:', err)
    return c.json({ error: 'Registration failed' }, 500)
  }
})

// --- Login ---
app.post('/api/auth/login', async (c) => {
  try {
    const { email, password } = await c.req.json()
    if (!email || !password) return c.json({ error: 'email and password are required' }, 400)

    const user = await c.env.sribuu_db.prepare(
      'SELECT id, name, email, password_hash FROM users WHERE email = ?'
    ).bind(email).first() as any

    if (!user) return c.json({ error: 'Invalid email or password' }, 401)

    const valid = bcrypt.compareSync(password, user.password_hash)
    if (!valid) return c.json({ error: 'Invalid email or password' }, 401)

    const token = await signJWT({
      sub: user.id, email: user.email, name: user.name,
      iat: Math.floor(Date.now() / 1000),
      exp: Math.floor(Date.now() / 1000) + 86400 * 7
    }, c.env.JWT_SECRET)

    return c.json({ user: { id: user.id, name: user.name, email: user.email }, token })
  } catch (err) {
    console.error('Login error:', err)
    return c.json({ error: 'Login failed' }, 500)
  }
})

// ============================================================
//  PROTECTED ROUTES (require auth)
// ============================================================

// --- Me ---
app.get('/api/auth/me', authMiddleware, (c) => {
  return c.json({ id: c.get('userId'), email: c.get('userEmail') })
})

// --- Categories ---
app.get('/api/categories', authMiddleware, async (c) => {
  try {
    const userId = c.get('userId') as number
    const { results } = await c.env.sribuu_db.prepare(
      `SELECT id, name, icon, color, is_default, user_id 
       FROM categories WHERE is_active = 1 AND (user_id IS NULL OR user_id = ?)
       ORDER BY is_default DESC, name ASC`
    ).bind(userId).all()
    return c.json(results)
  } catch (err) {
    console.error('/api/categories error:', err)
    return c.json({ error: 'Failed to load categories' }, 500)
  }
})

// --- Payment methods ---
app.get('/api/payment-methods', authMiddleware, async (c) => {
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

// ============================================================
//  TRANSACTION CRUD
// ============================================================

const TX_COLS = `t.id, t.amount, t.notes, t.transaction_date,
  t.category_id, t.payment_method_id,
  c.name as category_name, c.icon as category_icon, c.color as category_color,
  p.name as payment_method_name`

// --- List transactions (with optional filters) ---
app.get('/api/transactions', authMiddleware, async (c) => {
  try {
    const userId = c.get('userId') as number
    const limit = Math.min(Number(c.req.query('limit')) || 50, 200)
    const offset = Number(c.req.query('offset')) || 0
    const catId = c.req.query('category_id')
    const month = c.req.query('month')
    const year = c.req.query('year')

    let sql = `SELECT ${TX_COLS} FROM transactions t
      LEFT JOIN categories c ON t.category_id = c.id
      LEFT JOIN payment_methods p ON t.payment_method_id = p.id
      WHERE t.user_id = ?`
    const binds: any[] = [userId]

    if (catId) { sql += ' AND t.category_id = ?'; binds.push(Number(catId)) }
    if (month) { sql += " AND strftime('%m', t.transaction_date) = ?"; binds.push(month.padStart(2, '0')) }
    if (year) { sql += " AND strftime('%Y', t.transaction_date) = ?"; binds.push(year) }

    sql += ' ORDER BY t.transaction_date DESC, t.created_at DESC LIMIT ? OFFSET ?'
    binds.push(limit, offset)

    const { results } = await c.env.sribuu_db.prepare(sql).bind(...binds).all()

    // Also get total count (without limit/offset)
    let countSql = 'SELECT COUNT(*) as total FROM transactions t WHERE t.user_id = ?'
    const countBinds: any[] = [userId]
    if (catId) { countSql += ' AND t.category_id = ?'; countBinds.push(Number(catId)) }
    if (month) { countSql += " AND strftime('%m', t.transaction_date) = ?"; countBinds.push(month.padStart(2, '0')) }
    if (year) { countSql += " AND strftime('%Y', t.transaction_date) = ?"; countBinds.push(year) }
    const { total } = await c.env.sribuu_db.prepare(countSql).bind(...countBinds).first() as any

    return c.json({ transactions: results, total, limit, offset })
  } catch (err) {
    console.error('/api/transactions error:', err)
    return c.json({ error: 'Failed to load transactions' }, 500)
  }
})

// --- Create transaction ---
app.post('/api/transactions', authMiddleware, async (c) => {
  try {
    const userId = c.get('userId') as number
    const { category_id, payment_method_id, amount, notes, transaction_date } = await c.req.json()

    if (!amount || !transaction_date) {
      return c.json({ error: 'amount and transaction_date are required' }, 400)
    }

    const { meta } = await c.env.sribuu_db.prepare(
      `INSERT INTO transactions (user_id, category_id, payment_method_id, amount, notes, transaction_date)
       VALUES (?, ?, ?, ?, ?, ?)`
    ).bind(userId, category_id || null, payment_method_id || null, amount, notes || null, transaction_date).run()

    const tx = await c.env.sribuu_db.prepare(
      `SELECT ${TX_COLS} FROM transactions t
       LEFT JOIN categories c ON t.category_id = c.id
       LEFT JOIN payment_methods p ON t.payment_method_id = p.id
       WHERE t.id = ?`
    ).bind(meta.last_row_id).first()

    return c.json(tx, 201)
  } catch (err) {
    console.error('POST /api/transactions error:', err)
    return c.json({ error: 'Failed to create transaction' }, 500)
  }
})

// --- Get single transaction ---
app.get('/api/transactions/:id', authMiddleware, async (c) => {
  try {
    const userId = c.get('userId') as number
    const id = c.req.param('id')

    const tx = await c.env.sribuu_db.prepare(
      `SELECT ${TX_COLS} FROM transactions t
       LEFT JOIN categories c ON t.category_id = c.id
       LEFT JOIN payment_methods p ON t.payment_method_id = p.id
       WHERE t.id = ? AND t.user_id = ?`
    ).bind(id, userId).first()

    if (!tx) return c.json({ error: 'Transaction not found' }, 404)
    return c.json(tx)
  } catch (err) {
    console.error('GET /api/transactions/:id error:', err)
    return c.json({ error: 'Failed to get transaction' }, 500)
  }
})

// --- Update transaction ---
app.put('/api/transactions/:id', authMiddleware, async (c) => {
  try {
    const userId = c.get('userId') as number
    const id = c.req.param('id')

    // Check ownership
    const existing = await c.env.sribuu_db.prepare(
      'SELECT id FROM transactions WHERE id = ? AND user_id = ?'
    ).bind(id, userId).first()
    if (!existing) return c.json({ error: 'Transaction not found' }, 404)

    const { category_id, payment_method_id, amount, notes, transaction_date } = await c.req.json()

    // Build dynamic UPDATE
    const fields: string[] = []
    const binds: any[] = []
    if (amount !== undefined) { fields.push('amount = ?'); binds.push(amount) }
    if (category_id !== undefined) { fields.push('category_id = ?'); binds.push(category_id || null) }
    if (payment_method_id !== undefined) { fields.push('payment_method_id = ?'); binds.push(payment_method_id || null) }
    if (notes !== undefined) { fields.push('notes = ?'); binds.push(notes) }
    if (transaction_date !== undefined) { fields.push('transaction_date = ?'); binds.push(transaction_date) }

    if (fields.length === 0) return c.json({ error: 'No fields to update' }, 400)

    fields.push("updated_at = datetime('now')")
    binds.push(id, userId)

    await c.env.sribuu_db.prepare(
      `UPDATE transactions SET ${fields.join(', ')} WHERE id = ? AND user_id = ?`
    ).bind(...binds).run()

    const tx = await c.env.sribuu_db.prepare(
      `SELECT ${TX_COLS} FROM transactions t
       LEFT JOIN categories c ON t.category_id = c.id
       LEFT JOIN payment_methods p ON t.payment_method_id = p.id
       WHERE t.id = ?`
    ).bind(id).first()

    return c.json(tx)
  } catch (err) {
    console.error('PUT /api/transactions/:id error:', err)
    return c.json({ error: 'Failed to update transaction' }, 500)
  }
})

// --- Delete transaction ---
app.delete('/api/transactions/:id', authMiddleware, async (c) => {
  try {
    const userId = c.get('userId') as number
    const id = c.req.param('id')

    const existing = await c.env.sribuu_db.prepare(
      'SELECT id FROM transactions WHERE id = ? AND user_id = ?'
    ).bind(id, userId).first()
    if (!existing) return c.json({ error: 'Transaction not found' }, 404)

    await c.env.sribuu_db.prepare(
      'DELETE FROM transactions WHERE id = ? AND user_id = ?'
    ).bind(id, userId).run()

    return c.json({ message: 'Transaction deleted' })
  } catch (err) {
    console.error('DELETE /api/transactions/:id error:', err)
    return c.json({ error: 'Failed to delete transaction' }, 500)
  }
})

// --- Error handler ---
app.onError((err, c) => {
  console.error('Worker Error:', err.message)
  return c.text(`Error: ${err.message}`, 500)
})

// Cloudflare Pages Advanced Mode
export default app
