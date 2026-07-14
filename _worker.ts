import { Hono } from 'hono'
import { cors } from 'hono/cors'
import { STATIC_FILES } from './src/static'
import { hashPassword, verifyPassword, signJWT, verifyJWT, base64urlEncode, base64urlDecode } from './src/utils'

// --- Environment bindings ---
export interface Env {
  sribuu_db: D1Database
  JWT_SECRET: string
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

const app = new Hono<{ Bindings: Env; Variables: { userId: number; userEmail: string; userName: string } }>()

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
    const contentType = c.req.header('Content-Type') || ''
    if (!contentType.includes('application/json')) {
      return c.json({ error: 'Content-Type must be application/json' }, 415)
    }
    const { name, email, password } = await c.req.json()
    if (!name || !email || !password) {
      return c.json({ error: 'name, email, and password are required' }, 400)
    }
    if (password.length < 6) {
      return c.json({ error: 'Password must be at least 6 characters' }, 400)
    }
    if (password.length > 128) {
      return c.json({ error: 'Password must not exceed 128 characters' }, 400)
    }

    // Let the UNIQUE constraint handle duplicate emails — don't pre-check
    const hash = await hashPassword(password)
    const { meta } = await c.env.sribuu_db.prepare(
      'INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)'
    ).bind(name, email, hash).run()

    const userId = meta.last_row_id
    const token = await signJWT({ sub: userId, email, name, iat: Math.floor(Date.now() / 1000), exp: Math.floor(Date.now() / 1000) + 86400 * 7 }, c.env.JWT_SECRET)

    return c.json({ user: { id: userId, name, email }, token }, 201)
  } catch (err) {
    // Suppress UNIQUE constraint details — use a generic error message
    if (err instanceof Error && err.message?.includes?.('UNIQUE constraint failed')) {
      return c.json({ error: 'Registration failed. Please check your information and try again.' }, 400)
    }
    console.error('Register error:', err)
    return c.json({ error: 'Registration failed' }, 500)
  }
})

// --- Login ---
app.post('/api/auth/login', async (c) => {
  try {
    const contentType = c.req.header('Content-Type') || ''
    if (!contentType.includes('application/json')) {
      return c.json({ error: 'Content-Type must be application/json' }, 415)
    }
    const { email, password } = await c.req.json()
    if (!email || !password) return c.json({ error: 'email and password are required' }, 400)
    if (password.length > 128) {
      return c.json({ error: 'Invalid email or password' }, 401)
    }

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
// Income/expense determined by sign of amount (positive=income, negative=expense).
// The frontend is responsible for setting the correct sign based on user input.

app.get('/api/transactions', authMiddleware, async (c) => {
  try {
    const userId = c.get('userId') as number
    const url = new URL(c.req.url)
    const month = url.searchParams.get('month')
    const year = url.searchParams.get('year');
    const categoryId = url.searchParams.get('category_id');
    const limit = Math.min(parseInt(url.searchParams.get('limit') || '50'), 200);
    const offset = parseInt(url.searchParams.get('offset') || '0');

    let query = 'SELECT t.id, t.amount, t.notes, t.transaction_date, t.category_id, t.payment_method_id, c.name as category_name, c.icon as category_icon, c.color as category_color FROM transactions t LEFT JOIN categories c ON t.category_id = c.id WHERE t.user_id = ?'
    const params: any[] = [userId]

    if (month && year) {
      query += ' AND strftime(\'%m\', t.transaction_date) = ? AND strftime(\'%Y\', t.transaction_date) = ?'
      params.push(month.padStart(2, '0'), year)
    }
    if (categoryId) { query += ' AND t.category_id = ?'; params.push(parseInt(categoryId)) }

    const countQuery = query.replace(/SELECT .+? FROM/, 'SELECT COUNT(*) as total FROM').replace(/ ORDER BY .+$/, '')
    const countParams = [...params];

    query += ' ORDER BY t.transaction_date DESC, t.id DESC LIMIT ? OFFSET ?';
    params.push(limit, offset);

    const [ { results }, count ] = await Promise.all([
      c.env.sribuu_db.prepare(query).bind(...params).all(),
      c.env.sribuu_db.prepare(countQuery).bind(...countParams).first(),
    ])
    return c.json({ transactions: results, total: (count as any)?.total ?? 0 })
  } catch (err) {
    console.error('Transactions error:', err)
    return c.json({ error: 'Failed to fetch transactions' }, 500)
  }
})

app.post('/api/transactions', authMiddleware, async (c) => {
  try {
    const contentType = c.req.header('Content-Type') || ''
    if (!contentType.includes('application/json')) {
      return c.json({ error: 'Content-Type must be application/json' }, 415)
    }
    const userId = c.get('userId') as number
    const { amount, transaction_date, category_id, notes, payment_method_id } = await c.req.json()

    if (!amount) return c.json({ error: 'amount is required' }, 400)
    
    const finalCategory = category_id || 1
    const finalDate = transaction_date || new Date().toISOString().split('T')[0]

    const { meta } = await c.env.sribuu_db.prepare(
      'INSERT INTO transactions (user_id, amount, transaction_date, category_id, notes, payment_method_id) VALUES (?, ?, ?, ?, ?, ?)'
    ).bind(userId, amount, finalDate, finalCategory, notes || '', payment_method_id || null).run()

    const { results } = await c.env.sribuu_db.prepare(
      'SELECT t.id, t.amount, t.notes, t.transaction_date, t.category_id, t.payment_method_id, c.name as category_name, c.icon as category_icon, c.color as category_color FROM transactions t LEFT JOIN categories c ON t.category_id = c.id WHERE t.id = ?'
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
      `SELECT t.id, t.amount, t.notes, t.transaction_date, t.category_id, t.payment_method_id,
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
    const contentType = c.req.header('Content-Type') || ''
    if (!contentType.includes('application/json')) {
      return c.json({ error: 'Content-Type must be application/json' }, 415)
    }
    const userId = c.get('userId') as number
    const txId = parseInt(c.req.param('id'))
    const body = await c.req.json()

    const existing = await c.env.sribuu_db.prepare('SELECT id FROM transactions WHERE id = ? AND user_id = ?').bind(txId, userId).first()
    if (!existing) return c.json({ error: 'Transaction not found' }, 404)

    const updates: string[] = []
    const params: any[] = []
    // Use a fixed list of allowed fields to prevent injection
    const allowedFields = ['amount', 'transaction_date', 'category_id', 'notes', 'payment_method_id'];
    for (const key of allowedFields) {
      if (body.hasOwnProperty(key)) {
        updates.push(`${key} = ?`)
        params.push(body[key])
      }
    }
    if (updates.length === 0) return c.json({ error: 'No valid fields to update' }, 400)
    params.push(txId, userId)
    await c.env.sribuu_db.prepare(`UPDATE transactions SET ${updates.join(', ')} WHERE id = ? AND user_id = ?`).bind(...params).run()

    const { results } = await c.env.sribuu_db.prepare(
      'SELECT t.id, t.amount, t.notes, t.transaction_date, t.category_id, t.payment_method_id, c.name as category_name, c.icon as category_icon, c.color as category_color FROM transactions t LEFT JOIN categories c ON t.category_id = c.id WHERE t.id = ?'
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

    let incomeQuery = 'SELECT COALESCE(SUM(amount), 0) as total FROM transactions WHERE user_id = ? AND amount >= 0'
    let expenseQuery = 'SELECT COALESCE(SUM(amount), 0) as total FROM transactions WHERE user_id = ? AND amount < 0'
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
    const incomeTotal = (income as any)?.total || 0;
    const expenseTotal = Math.abs((expense as any)?.total || 0); // Return positive value for expense
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
    const { name, match_keywords, category_id, payment_method_id, is_active, priority } = await c.req.json()
    if (!name || !match_keywords || !category_id) {
      return c.json({ error: 'name, match_keywords, and category_id are required' }, 400)
    }
    const { meta } = await c.env.sribuu_db.prepare(
      'INSERT INTO rules (user_id, name, match_keywords, category_id, payment_method_id, is_active, priority) VALUES (?, ?, ?, ?, ?, ?, ?)'
    ).bind(
      userId, name, match_keywords, category_id,
      payment_method_id || null, is_active !== undefined ? is_active : 1, priority || 0
    ).run()
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
    const allowedFields = ['name', 'match_keywords', 'category_id', 'payment_method_id', 'is_active', 'priority']
    for (const key of allowedFields) {
        if (body.hasOwnProperty(key)) {
            updates.push(`${key} = ?`)
            params.push(body[key])
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
