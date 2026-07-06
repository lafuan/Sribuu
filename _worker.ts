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

// --- Transactions: recent ---
app.get('/api/transactions', authMiddleware, async (c) => {
  try {
    const userId = c.get('userId') as number
    const { results } = await c.env.sribuu_db.prepare(
      `SELECT t.id, t.amount, t.notes, t.transaction_date, 
              c.name as category_name, c.icon as category_icon, c.color as category_color,
              p.name as payment_method_name
       FROM transactions t
       LEFT JOIN categories c ON t.category_id = c.id
       LEFT JOIN payment_methods p ON t.payment_method_id = p.id
       WHERE t.user_id = ?
       ORDER BY t.transaction_date DESC, t.created_at DESC
       LIMIT 50`
    ).bind(userId).all()
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
