import { Hono } from 'hono'
import { cors } from 'hono/cors'
import { STATIC_FILES } from './src/static'

// --- Environment bindings ---
export interface Env {
  sribuu_db: D1Database
  JWT_SECRET: string
}

// ============================================================
//  PASSWORD HASHING with Web Crypto API (no bcryptjs needed)
// ============================================================

const PBKDF2_ITERATIONS = 100000
const SALT_BYTES = 16
const KEY_LENGTH = 32

function base64url(buf: ArrayBuffer): string {
  const bytes = new Uint8Array(buf)
  let binary = ''
  for (let i = 0; i < bytes.length; i++) binary += String.fromCharCode(bytes[i])
  return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '')
}

function fromBase64url(s: string): Uint8Array {
  s = s.replace(/-/g, '+').replace(/_/g, '/')
  while (s.length % 4) s += '='
  const binary = atob(s)
  const bytes = new Uint8Array(binary.length)
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i)
  return bytes
}

async function hashPassword(password: string): Promise<string> {
  const salt = crypto.getRandomValues(new Uint8Array(SALT_BYTES))
  const key = await crypto.subtle.importKey('raw', new TextEncoder().encode(password), 'PBKDF2', false, ['deriveBits'])
  const hash = await crypto.subtle.deriveBits(
    { name: 'PBKDF2', salt, iterations: PBKDF2_ITERATIONS, hash: 'SHA-256' },
    key,
    KEY_LENGTH * 8
  )
  return `$pbkdf2-sha256$${PBKDF2_ITERATIONS}$${base64url(salt)}$${base64url(hash)}`
}

async function verifyPassword(password: string, stored: string): Promise<boolean> {
  const parts = stored.split('$')
  if (parts[0] !== '' || parts[1] !== 'pbkdf2-sha256') throw new Error('Unsupported hash format')
  const iterations = parseInt(parts[2], 10)
  const salt = fromBase64url(parts[3])
  const expectedHash = parts[4]
  const key = await crypto.subtle.importKey('raw', new TextEncoder().encode(password), 'PBKDF2', false, ['deriveBits'])
  const hash = await crypto.subtle.deriveBits(
    { name: 'PBKDF2', salt, iterations, hash: 'SHA-256' },
    key,
    KEY_LENGTH * 8
  )
  const hashStr = base64url(hash)
  // Constant-time comparison
  if (hashStr.length !== expectedHash.length) return false
  let result = 0
  for (let i = 0; i < hashStr.length; i++) result |= hashStr.charCodeAt(i) ^ expectedHash.charCodeAt(i)
  return result === 0
}

// ============================================================
//  JWT (Web Crypto + HMAC-SHA256)
// ============================================================

function base64urlEncode(obj: any): string {
  return base64url(new TextEncoder().encode(JSON.stringify(obj)))
}

function base64urlDecode<T>(s: string): T {
  return JSON.parse(new TextDecoder().decode(fromBase64url(s)))
}

async function signJWT(payload: Record<string, any>, secret: string): Promise<string> {
  const header = base64urlEncode({ alg: 'HS256', typ: 'JWT' })
  const body = base64urlEncode(payload)
  const key = await crypto.subtle.importKey('raw', new TextEncoder().encode(secret), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign'])
  const sig = await crypto.subtle.sign('HMAC', key, new TextEncoder().encode(`${header}.${body}`))
  return `${header}.${body}.${base64url(sig)}`
}

async function verifyJWT(token: string, secret: string): Promise<Record<string, any> | null> {
  const parts = token.split('.')
  if (parts.length !== 3) return null
  const [headerB64, bodyB64, sigB64] = parts
  try {
    const key = await crypto.subtle.importKey('raw', new TextEncoder().encode(secret), { name: 'HMAC', hash: 'SHA-256' }, false, ['verify'])
    const valid = await crypto.subtle.verify('HMAC', key, fromBase64url(sigB64), new TextEncoder().encode(`${headerB64}.${bodyB64}`))
    if (!valid) return null
    const payload = base64urlDecode<any>(bodyB64)
    if (payload.exp && payload.exp < Math.floor(Date.now() / 1000)) return null
    return payload
  } catch { return null }
}

// ============================================================
//  MIDDLEWARE
// ============================================================

const authMiddleware = async (c: any, next: any) => {
  const auth = c.req.header('Authorization')
  if (!auth || !auth.startsWith('Bearer ')) return c.json({ error: 'Unauthorized' }, 401)
  const token = auth.slice(7)
  const payload = await verifyJWT(token, c.env.JWT_SECRET)
  if (!payload) return c.json({ error: 'Invalid or expired token' }, 401)
  c.set('userId', payload.sub)
  c.set('userEmail', payload.email)
  c.set('userName', payload.name)
  await next()
}

// ============================================================
//  APP
// ============================================================

const app = new Hono<{ Bindings: Env }>()

app.use('/*', cors())

// --- Static File Serving ---
app.get('/', async (c) => {
  const file = STATIC_FILES['/index.html']
  if (file) return c.html(file.content)
  return c.text('Not Found', 404)
})

app.get('/app', async (c) => {
  const file = STATIC_FILES['/app.html']
  if (file) return c.html(file.content)
  return c.text('Not Found', 404)
})

// Generic route for static files served from /public
app.get('/:file{[a-z][a-z0-9._-]*}', async (c) => {
  const name = c.req.param('file')
  const key = '/' + name
  const file = STATIC_FILES[key]
  if (!file) return c.text('Not Found', 404)
  const ext = name.split('.').pop() || ''
  if (ext === 'json') return c.json(JSON.parse(file.content))
  return c.body(file.content, 200, { 'Content-Type': file.mime })
})

// --- Health Check ---
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

    const existing = await c.env.sribuu_db.prepare('SELECT id FROM users WHERE email = ?').bind(email).first()
    if (existing) return c.json({ error: 'Email already registered' }, 409)

    const hash = await hashPassword(password)
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

    const valid = await verifyPassword(password, user.password_hash)
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
    console.error('Categories error:', err)
    return c.json({ error: 'Failed to fetch categories' }, 500)
  }
})

// --- Payment Methods ---
app.get('/api/payment-methods', authMiddleware, async (c) => {
  try {
    const { results } = await c.env.sribuu_db.prepare(
      `SELECT id, name, icon, is_default, is_active
       FROM payment_methods WHERE is_active = 1
       ORDER BY is_default DESC, name ASC`
    ).all()
    return c.json(results)
  } catch (err) {
    console.error('Payment methods error:', err)
    return c.json({ error: 'Failed to fetch payment methods' }, 500)
  }
})

// --- Transactions ---
// Schema: id, user_id, category_id, payment_method_id, parent_transaction_id,
//         amount (INTEGER), notes (TEXT), attachment_path, transaction_date
// Income/expense determined by sign of amount (positive=expense? no, negative=expense in frontend)

app.get('/api/transactions', authMiddleware, async (c) => {
  try {
    const userId = c.get('userId') as number
    const url = new URL(c.req.url)
    const month = url.searchParams.get('month')
    const year = url.searchParams.get('year')
    const categoryId = url.searchParams.get('category_id')
    const limit = Math.min(parseInt(url.searchParams.get('limit') || '50'), 200)
    const offset = parseInt(url.searchParams.get('offset') || '0')

    // Old schema: description field, type column, no payment_method_id
    let query = 'SELECT t.id, t.amount, t.description as notes, t.transaction_date, t.category_id, NULL as payment_method_id, c.name as category_name, c.icon as category_icon, c.color as category_color FROM transactions t LEFT JOIN categories c ON t.category_id = c.id WHERE t.user_id = ?'
    const params: any[] = [userId]

    if (month && year) {
      query += ' AND strftime(\'%m\', t.transaction_date) = ? AND strftime(\'%Y\', t.transaction_date) = ?'
      params.push(month.padStart(2, '0'), year)
    }
    if (categoryId) { query += ' AND t.category_id = ?'; params.push(parseInt(categoryId)) }

    const countQuery = query.replace(/SELECT .+? FROM/, 'SELECT COUNT(*) as total FROM').replace(/ ORDER BY .+$/, '')
    const countParams = [...params]
    query += ' ORDER BY t.transaction_date DESC, t.id DESC LIMIT ? OFFSET ?'
    params.push(limit, offset)

    const [ { results }, { total } ] = await Promise.all([
      c.env.sribuu_db.prepare(query).bind(...params).all(),
      c.env.sribuu_db.prepare(countQuery).bind(...countParams).first()
    ])
    return c.json({ transactions: results, total: (total as any)?.total || 0 })
  } catch (err) {
    console.error('Transactions error:', err)
    return c.json({ error: 'Failed to fetch transactions' }, 500)
  }
})

app.post('/api/transactions', authMiddleware, async (c) => {
  try {
    const userId = c.get('userId') as number
    const body = await c.req.json()
    const { amount, transaction_date, category_id } = body

    if (!amount) return c.json({ error: 'amount is required' }, 400)
    // Old schema: description (maps to notes), type column, no payment_method_id
    const finalCategory = category_id || 1
    const notesText = body.notes ?? ''

    const { meta } = await c.env.sribuu_db.prepare(
      'INSERT INTO transactions (user_id, amount, type, description, transaction_date, category_id) VALUES (?, ?, ?, ?, ?, ?)'
    ).bind(userId, amount, 'expense', notesText, transaction_date || new Date().toISOString().split('T')[0], finalCategory).run()

    const { results } = await c.env.sribuu_db.prepare(
      'SELECT t.id, t.amount, t.description as notes, t.transaction_date, t.category_id, NULL as payment_method_id, c.name as category_name, c.icon as category_icon, c.color as category_color FROM transactions t LEFT JOIN categories c ON t.category_id = c.id WHERE t.id = ?'
    ).bind(meta.last_row_id).all()
    return c.json((results as any[])[0], 201)
  } catch (err) {
    console.error('Create transaction error:', err)
    return c.json({ error: 'Failed to create transaction' }, 500)
  }
})

app.get('/api/transactions/:id', authMiddleware, async (c) => {
  try {
    const userId = c.get('userId') as number
    const txId = parseInt(c.req.param('id'))
    const tx = await c.env.sribuu_db.prepare(
      `SELECT t.id, t.amount, t.description as notes, t.transaction_date, t.category_id, NULL as payment_method_id,
              c.name as category_name, c.icon as category_icon, c.color as category_color
       FROM transactions t
       LEFT JOIN categories c ON t.category_id = c.id
       WHERE t.id = ? AND t.user_id = ?`
    ).bind(txId, userId).first()
    if (!tx) return c.json({ error: 'Transaction not found' }, 404)
    return c.json(tx)
  } catch (err) {
    console.error('Get transaction error:', err)
    return c.json({ error: 'Failed to fetch transaction' }, 500)
  }
})

app.put('/api/transactions/:id', authMiddleware, async (c) => {
  try {
    const userId = c.get('userId') as number
    const txId = parseInt(c.req.param('id'))
    const body = await c.req.json()

    const existing = await c.env.sribuu_db.prepare('SELECT id FROM transactions WHERE id = ? AND user_id = ?').bind(txId, userId).first()
    if (!existing) return c.json({ error: 'Transaction not found' }, 404)

    const updates: string[] = []
    const params: any[] = []
    for (const [key, val] of Object.entries(body)) {
      if (['amount', 'transaction_date', 'category_id'].includes(key)) {
        updates.push(`${key} = ?`)
        params.push(val)
      } else if (key === 'notes') {
        updates.push('description = ?')
        params.push(val)
      }
    }
    if (updates.length === 0) return c.json({ error: 'No valid fields to update' }, 400)
    params.push(txId, userId)
    await c.env.sribuu_db.prepare(`UPDATE transactions SET ${updates.join(', ')} WHERE id = ? AND user_id = ?`).bind(...params).run()

    const { results } = await c.env.sribuu_db.prepare(
      'SELECT t.id, t.amount, t.description as notes, t.transaction_date, t.category_id, NULL as payment_method_id, c.name as category_name, c.icon as category_icon, c.color as category_color FROM transactions t LEFT JOIN categories c ON t.category_id = c.id WHERE t.id = ?'
    ).bind(txId).all()
    return c.json((results as any[])[0])
  } catch (err) {
    console.error('Update transaction error:', err)
    return c.json({ error: 'Failed to update transaction' }, 500)
  }
})

app.delete('/api/transactions/:id', authMiddleware, async (c) => {
  try {
    const userId = c.get('userId') as number
    const txId = parseInt(c.req.param('id'))
    const existing = await c.env.sribuu_db.prepare('SELECT id FROM transactions WHERE id = ? AND user_id = ?').bind(txId, userId).first()
    if (!existing) return c.json({ error: 'Transaction not found' }, 404)
    await c.env.sribuu_db.prepare('DELETE FROM transactions WHERE id = ? AND user_id = ?').bind(txId, userId).run()
    return c.json({ success: true })
  } catch (err) {
    console.error('Delete transaction error:', err)
    return c.json({ error: 'Failed to delete transaction' }, 500)
  }
})

// ============================================================
//  STATS & SUMMARY
// ============================================================

app.get('/api/stats/summary', authMiddleware, async (c) => {
  try {
    const userId = c.get('userId') as number
    const url = new URL(c.req.url)
    const month = url.searchParams.get('month')
    const year = url.searchParams.get('year')

    let incomeQuery = 'SELECT COALESCE(SUM(amount), 0) as total FROM transactions WHERE user_id = ? AND type = \'income\''
    let expenseQuery = 'SELECT COALESCE(SUM(amount), 0) as total FROM transactions WHERE user_id = ? AND type = \'expense\''
    const params: any[] = [userId]
    const params2: any[] = [userId]

    if (month && year) {
      const filter = ' AND strftime(\'%m\', transaction_date) = ? AND strftime(\'%Y\', transaction_date) = ?'
      incomeQuery += filter
      expenseQuery += filter
      params.push(month.padStart(2, '0'), year)
      params2.push(month.padStart(2, '0'), year)
    }

    const [income, expense] = await Promise.all([
      c.env.sribuu_db.prepare(incomeQuery).bind(...params).first(),
      c.env.sribuu_db.prepare(expenseQuery).bind(...params2).first()
    ])
    const incomeTotal = (income as any)?.total || 0
    const expenseTotal = (expense as any)?.total || 0
    return c.json({ income: incomeTotal, expense: expenseTotal, balance: incomeTotal - expenseTotal })
  } catch (err) {
    console.error('Stats error:', err)
    return c.json({ error: 'Failed to get summary' }, 500)
  }
})

// ============================================================
//  RULES ENGINE
// ============================================================

app.get('/api/rules', authMiddleware, async (c) => {
  try {
    const userId = c.get('userId') as number
    const { results } = await c.env.sribuu_db.prepare(
      'SELECT * FROM rules WHERE user_id = ? OR user_id IS NULL ORDER BY priority ASC, created_at DESC'
    ).bind(userId).all()
    return c.json(results)
  } catch (err) {
    console.error('Rules error:', err)
    return c.json({ error: 'Failed to fetch rules' }, 500)
  }
})

app.post('/api/rules', authMiddleware, async (c) => {
  try {
    const userId = c.get('userId') as number
    const { name, description, condition, action, priority } = await c.req.json()
    if (!name || !condition || !action) return c.json({ error: 'name, condition, and action are required' }, 400)
    const { meta } = await c.env.sribuu_db.prepare(
      'INSERT INTO rules (user_id, name, description, condition, action, priority) VALUES (?, ?, ?, ?, ?, ?)'
    ).bind(userId, name, description || '', JSON.stringify(condition), JSON.stringify(action), priority || 0).run()
    const { results } = await c.env.sribuu_db.prepare('SELECT * FROM rules WHERE id = ?').bind(meta.last_row_id).all()
    return c.json((results as any[])[0], 201)
  } catch (err) {
    console.error('Create rule error:', err)
    return c.json({ error: 'Failed to create rule' }, 500)
  }
})

app.put('/api/rules/:id', authMiddleware, async (c) => {
  try {
    const userId = c.get('userId') as number
    const ruleId = parseInt(c.req.param('id'))
    const existing = await c.env.sribuu_db.prepare('SELECT id FROM rules WHERE id = ? AND user_id = ?').bind(ruleId, userId).first()
    if (!existing) return c.json({ error: 'Rule not found' }, 404)
    const body = await c.req.json()
    const updates: string[] = []
    const params: any[] = []
    for (const [key, val] of Object.entries(body)) {
      if (['name', 'description', 'priority', 'is_active'].includes(key)) {
        updates.push(`${key} = ?`)
        params.push(val)
      } else if (key === 'condition' || key === 'action') {
        updates.push(`${key} = ?`)
        params.push(JSON.stringify(val))
      }
    }
    if (updates.length === 0) return c.json({ error: 'No valid fields to update' }, 400)
    params.push(ruleId, userId)
    await c.env.sribuu_db.prepare(`UPDATE rules SET ${updates.join(', ')} WHERE id = ? AND user_id = ?`).bind(...params).run()
    const { results } = await c.env.sribuu_db.prepare('SELECT * FROM rules WHERE id = ?').bind(ruleId).all()
    return c.json((results as any[])[0])
  } catch (err) {
    console.error('Update rule error:', err)
    return c.json({ error: 'Failed to update rule' }, 500)
  }
})

app.delete('/api/rules/:id', authMiddleware, async (c) => {
  try {
    const userId = c.get('userId') as number
    const ruleId = parseInt(c.req.param('id'))
    const existing = await c.env.sribuu_db.prepare('SELECT id FROM rules WHERE id = ? AND user_id = ?').bind(ruleId, userId).first()
    if (!existing) return c.json({ error: 'Rule not found' }, 404)
    await c.env.sribuu_db.prepare('DELETE FROM rules WHERE id = ? AND user_id = ?').bind(ruleId, userId).run()
    return c.json({ success: true })
  } catch (err) {
    console.error('Delete rule error:', err)
    return c.json({ error: 'Failed to delete rule' }, 500)
  }
})

// ============================================================
//  EXPORT
// ============================================================

export default app
