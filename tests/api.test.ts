import { describe, it, expect, beforeEach } from 'vitest'
import app from '../_worker'
import { hashPassword, signJWT } from '../src/utils'

const JWT_SECRET = 'sribuu-test-secret-key'
const TEST_PASSWORD = 'password123'

// ============================================================
//  IN-MEMORY DATA STORE
// ============================================================

interface UserRow { id: number; name: string; email: string; password_hash: string }
interface TransactionRow { id: number; user_id: number; amount: number; description: string; transaction_date: string; category_id: number; type: string }
interface CategoryRow { id: number; name: string; icon: string; color: string; is_default: number; is_active: number; user_id: number | null }
interface RuleRow { id: number; user_id: number; name: string; description: string; condition: string; action: string; priority: number; is_active: number; created_at: string }

let nextUserId = 1
let nextTxId = 1
let nextRuleId = 1
let users: UserRow[] = []
let transactions: TransactionRow[] = []
let categories: CategoryRow[] = []
let rules: RuleRow[] = []

const defaultCategories: CategoryRow[] = [
  { id: 1, name: 'Food', icon: '🍔', color: '#FF6B6B', is_default: 1, is_active: 1, user_id: null },
  { id: 2, name: 'Transport', icon: '🚗', color: '#4ECDC4', is_default: 1, is_active: 1, user_id: null },
  { id: 3, name: 'Shopping', icon: '🛒', color: '#45B7D1', is_default: 1, is_active: 1, user_id: null },
]

function resetDb() {
  nextUserId = 1
  nextTxId = 1
  nextRuleId = 1
  users = []
  transactions = []
  categories = [...defaultCategories]
  rules = []
}

// ============================================================
//  MOCK D1
// ============================================================

function makeMockDb() {
  return {
    prepare(sql: string) {
      let binds: any[] = []
      let query = sql

      const stmt = {
        bind(...args: any[]) {
          binds = args
          return stmt
        },
        async first() {
          // --- Users ---
          if (query.includes('SELECT id FROM users WHERE email = ?')) {
            const u = users.find(u => u.email === binds[0])
            return u ? { id: u.id } : null
          }
          if (query.includes('SELECT id, name, email, password_hash FROM users WHERE email = ?')) {
            const u = users.find(u => u.email === binds[0])
            return u ? { ...u } : null
          }
          // --- Transaction existence check OR single tx fetch ---
          if (query.includes('FROM transactions t') && (query.includes('WHERE t.id = ? AND t.user_id = ?'))) {
            const [txId, userId] = binds
            const tx = transactions.find(t => t.id === txId && t.user_id === userId)
            if (!tx) return null
            // Full SELECT with JOIN (for GET /transactions/:id)
            if (query.includes('description as notes')) {
              const cat = categories.find(c => c.id === tx.category_id)
              return {
                id: tx.id, amount: tx.amount, notes: tx.description,
                transaction_date: tx.transaction_date, category_id: tx.category_id,
                payment_method_id: null,
                category_name: cat?.name ?? null,
                category_icon: cat?.icon ?? null,
                category_color: cat?.color ?? null,
              }
            }
            return { id: tx.id }
          }
          // --- Rule existence check ---
          if (query.includes('SELECT id FROM rules WHERE id = ? AND user_id = ?')) {
            const [ruleId, userId] = binds
            const r = rules.find(r => r.id === ruleId && r.user_id === userId)
            return r ? { id: r.id } : null
          }
          // --- Count query (transactions) ---
          if (query.includes('COUNT(*) as total')) {
            // Simplified: return matching count
            let filtered = [...transactions]
            if (query.includes('WHERE t.user_id = ?')) {
              filtered = filtered.filter(t => t.user_id === binds[0])
            }
            if (query.includes('strftime')) {
              // Basic month/year matching
              const monthIdx = query.includes('AND strftime') ? 1 : -1
              if (monthIdx > 0 && binds[monthIdx] && binds[monthIdx + 1]) {
                const month = binds[monthIdx].toString().padStart(2, '0')
                const year = binds[monthIdx + 1].toString()
                filtered = filtered.filter(t => {
                  const d = t.transaction_date
                  return d.startsWith(year + '-') && d.includes('-' + month + '-')
                })
              }
            }
            return { total: filtered.length }
          }
          // --- Stats queries ---
          if (query.includes('COALESCE(SUM(amount), 0) as total')) {
            let filtered = [...transactions]
            if (query.includes('WHERE user_id = ?')) {
              filtered = filtered.filter(t => t.user_id === binds[0])
            }
            if (query.includes('type')) {
              if (query.includes("type = 'income'")) {
                filtered = filtered.filter(t => t.type === 'income' || t.amount > 0)
              } else if (query.includes("type = 'expense'")) {
                filtered = filtered.filter(t => t.type === 'expense' || t.amount < 0)
              }
            }
            const total = filtered.reduce((sum, t) => sum + Math.abs(t.amount), 0)
            return { total }
          }
          return null
        },
        async all() {
          // --- Categories ---
          if (query.includes('FROM categories')) {
            let filtered = [...categories]
            if (query.includes('WHERE is_active = 1')) {
              filtered = filtered.filter(c => c.is_active === 1)
            }
            if (query.includes('AND (user_id IS NULL OR user_id = ?)')) {
              filtered = filtered.filter(c => c.user_id === null || c.user_id === binds[0])
            }
            return { results: filtered }
          }
          // --- Payment Methods ---
          if (query.includes('FROM payment_methods')) {
            // Static mock
            return { results: [
              { id: 1, name: 'Cash', icon: '💵', is_default: 1, is_active: 1 },
              { id: 2, name: 'Bank Transfer', icon: '🏦', is_default: 0, is_active: 1 },
            ]}
          }
          // --- Transactions (list / get single) ---
          if (query.includes('FROM transactions t') || query.includes('FROM transactions')) {
            let filtered = [...transactions]
            if (query.includes('WHERE t.user_id = ?') || query.includes('WHERE user_id = ?')) {
              const userId = binds[0]
              filtered = filtered.filter(t => t.user_id === userId)
            }
            if (query.includes('t.id = ?')) {
              const txBindIdx = query.includes('AND t.user_id = ?') ? 0 : 0
              filtered = filtered.filter(t => t.id === binds[0])
            }
            const results = filtered.map(t => ({
              id: t.id,
              amount: t.amount,
              notes: t.description,
              transaction_date: t.transaction_date,
              category_id: t.category_id,
              payment_method_id: null,
              category_name: categories.find(c => c.id === t.category_id)?.name || null,
              category_icon: categories.find(c => c.id === t.category_id)?.icon || null,
              category_color: categories.find(c => c.id === t.category_id)?.color || null,
            }))
            return { results }
          }
          // --- Rules (list / get single) ---
          if (query.includes('FROM rules')) {
            let filtered = [...rules]
            if (query.includes('WHERE id = ?')) {
              filtered = filtered.filter(r => r.id === binds[0])
            }
            return { results: filtered }
          }
          return { results: [] }
        },
        async run() {
          // --- INSERT user ---
          if (query.includes('INSERT INTO users')) {
            const [name, email, passwordHash] = binds
            const newUser: UserRow = { id: nextUserId++, name, email, password_hash: passwordHash }
            users.push(newUser)
            return { meta: { last_row_id: newUser.id } }
          }
          // --- INSERT transaction ---
          if (query.includes('INSERT INTO transactions')) {
            const [userId, amount, type, description, transactionDate, categoryId] = binds as any[]
            const newTx: TransactionRow = {
              id: nextTxId++, user_id: userId, amount, description,
              transaction_date: transactionDate, category_id: categoryId, type
            }
            transactions.push(newTx)
            return { meta: { last_row_id: newTx.id } }
          }
          // --- UPDATE transaction ---
          if (query.includes('UPDATE transactions SET')) {
            return { meta: { last_row_id: 0 } }
          }
          // --- DELETE transaction ---
          if (query.includes('DELETE FROM transactions')) {
            const [txId, userId] = binds
            transactions = transactions.filter(t => !(t.id === txId && t.user_id === userId))
            return { meta: { last_row_id: 0 } }
          }
          // --- INSERT rule ---
          if (query.includes('INSERT INTO rules')) {
            const [userId, name, desc, condition, action, priority] = binds as any[]
            const newRule: RuleRow = {
              id: nextRuleId++, user_id: userId,
              name: name, description: desc,
              condition: typeof condition === 'string' ? condition : JSON.stringify(condition),
              action: typeof action === 'string' ? action : JSON.stringify(action),
              priority, is_active: 1,
              created_at: new Date().toISOString()
            }
            rules.push(newRule)
            return { meta: { last_row_id: newRule.id } }
          }
          // --- UPDATE rule ---
          if (query.includes('UPDATE rules SET')) {
            return { meta: { last_row_id: 0 } }
          }
          // --- DELETE rule ---
          if (query.includes('DELETE FROM rules')) {
            const [ruleId, userId] = binds
            rules = rules.filter(r => !(r.id === ruleId && r.user_id === userId))
            return { meta: { last_row_id: 0 } }
          }
          return { meta: { last_row_id: 0 } }
        }
      }
      return stmt
    }
  }
}

// ============================================================
//  HELPERS
// ============================================================

async function genToken(overrides: any = {}): Promise<string> {
  return signJWT({
    sub: overrides.sub ?? 1,
    email: overrides.email ?? 'test@test.com',
    name: overrides.name ?? 'Test',
    iat: Math.floor(Date.now() / 1000),
    exp: Math.floor(Date.now() / 1000) + 3600,
    ...overrides
  }, JWT_SECRET)
}

function env(mockDb: any): any {
  return { sribuu_db: mockDb, JWT_SECRET }
}

// ============================================================
//  API TESTS
// ============================================================

describe('API Routes', () => {
  let mockDb: ReturnType<typeof makeMockDb>

  beforeEach(() => {
    resetDb()
    mockDb = makeMockDb() as any
  })

  // ============================================================
  //  HEALTH CHECK
  // ============================================================

  describe('GET /api/health', () => {
    it('returns ok status', async () => {
      const res = await app.request('/api/health')
      expect(res.status).toBe(200)
      const body: any = await res.json() as { status: string; platform: string; timestamp: number }
      expect(body.status).toBe('ok')
      expect(body.platform).toBe('cloudflare-pages')
      expect(body.timestamp).toBeGreaterThan(0)
    })
  })

  // ============================================================
  //  REGISTER
  // ============================================================

  describe('POST /api/auth/register', () => {
    it('registers a new user', async () => {
      const res = await app.request('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: 'Test', email: 'test@test.com', password: TEST_PASSWORD })
      }, env(mockDb))
      expect(res.status).toBe(201)
      const body: any = await res.json()
      expect(body.user.name).toBe('Test')
      expect(body.user.email).toBe('test@test.com')
      expect(body.token).toBeTruthy()
      expect(body.user.id).toBeGreaterThan(0)
    })

    it('rejects missing fields', async () => {
      const res = await app.request('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: 'Test' })
      }, env(mockDb))
      expect(res.status).toBe(400)
      const body: any = await res.json()
      expect(body.error).toContain('required')
    })

    it('rejects short password', async () => {
      const res = await app.request('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: 'Test', email: 'test@test.com', password: '12345' })
      }, env(mockDb))
      expect(res.status).toBe(400)
      const body: any = await res.json()
      expect(body.error).toContain('6 characters')
    })

    it('rejects duplicate email', async () => {
      const body = JSON.stringify({ name: 'Test', email: 'dup@test.com', password: TEST_PASSWORD })
      await app.request('/api/auth/register', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body }, env(mockDb))
      const res = await app.request('/api/auth/register', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body }, env(mockDb))
      expect(res.status).toBe(409)
      const data: any = await res.json()
      expect(data.error).toContain('already registered')
    })
  })

  // ============================================================
  //  LOGIN
  // ============================================================

  describe('POST /api/auth/login', () => {
    it('logs in with valid credentials', async () => {
      // Register first
      await app.request('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: 'Test', email: 'test@test.com', password: TEST_PASSWORD })
      }, env(mockDb))
      // Update stored user with a real password hash
      const hash = await hashPassword(TEST_PASSWORD)
      users[0].password_hash = hash

      const res = await app.request('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: 'test@test.com', password: TEST_PASSWORD })
      }, env(mockDb))
      expect(res.status).toBe(200)
      const body: any = await res.json()
      expect(body.user.name).toBe('Test')
      expect(body.user.email).toBe('test@test.com')
      expect(body.token).toBeTruthy()
    })

    it('rejects invalid email', async () => {
      const res = await app.request('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: 'nonexistent@test.com', password: TEST_PASSWORD })
      }, env(mockDb))
      expect(res.status).toBe(401)
    })

    it('rejects wrong password', async () => {
      await app.request('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: 'Test', email: 'test@test.com', password: TEST_PASSWORD })
      }, env(mockDb))
      users[0].password_hash = await hashPassword(TEST_PASSWORD)

      const res = await app.request('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: 'test@test.com', password: 'wrongpassword' })
      }, env(mockDb))
      expect(res.status).toBe(401)
    })

    it('rejects missing fields', async () => {
      const res = await app.request('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: 'test@test.com' })
      }, env(mockDb))
      expect(res.status).toBe(400)
    })
  })

  // ============================================================
  //  PROTECTED ROUTES
  // ============================================================

  describe('GET /api/auth/me', () => {
    it('returns user info with valid token', async () => {
      const token = await genToken({ sub: 1, email: 'test@test.com', name: 'Test' })
      const res = await app.request('/api/auth/me', {
        headers: { 'Authorization': `Bearer ${token}` }
      }, env(mockDb))
      expect(res.status).toBe(200)
      const body: any = await res.json()
      expect(body.id).toBe(1)
      expect(body.email).toBe('test@test.com')
    })

    it('rejects missing auth header', async () => {
      const res = await app.request('/api/auth/me', {}, env(mockDb))
      expect(res.status).toBe(401)
    })

    it('rejects invalid token', async () => {
      const res = await app.request('/api/auth/me', {
        headers: { 'Authorization': 'Bearer invalid-token' }
      }, env(mockDb))
      expect(res.status).toBe(401)
    })
  })

  // ============================================================
  //  CATEGORIES
  // ============================================================

  describe('GET /api/categories', () => {
    it('returns categories', async () => {
      const token = await genToken()
      const res = await app.request('/api/categories', {
        headers: { 'Authorization': `Bearer ${token}` }
      }, env(mockDb))
      expect(res.status).toBe(200)
      const body: any = await res.json()
      expect(Array.isArray(body)).toBe(true)
      expect(body.length).toBeGreaterThanOrEqual(3)
      expect(body[0].name).toBeDefined()
    })
  })

  // ============================================================
  //  PAYMENT METHODS
  // ============================================================

  describe('GET /api/payment-methods', () => {
    it('returns payment methods', async () => {
      const token = await genToken()
      const res = await app.request('/api/payment-methods', {
        headers: { 'Authorization': `Bearer ${token}` }
      }, env(mockDb))
      expect(res.status).toBe(200)
      const body: any = await res.json()
      expect(Array.isArray(body)).toBe(true)
      expect(body.length).toBe(2)
      expect(body[0].name).toBe('Cash')
    })
  })

  // ============================================================
  //  TRANSACTIONS CRUD
  // ============================================================

  describe('Transactions CRUD', () => {
    let token: string
    let userId: number

    beforeEach(async () => {
      userId = 1
      token = await genToken({ sub: userId, email: 'test@test.com', name: 'Test' })
    })

    it('creates a transaction', async () => {
      const res = await app.request('/api/transactions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({ amount: 50000, transaction_date: '2026-07-06', category_id: 1, notes: 'Lunch' })
      }, env(mockDb))
      expect(res.status).toBe(201)
      const body: any = await res.json()
      expect(body.amount).toBe(50000)
      expect(body.notes).toBe('Lunch')
      expect(body.transaction_date).toBe('2026-07-06')
    })

    it('lists transactions', async () => {
      // Create a transaction first
      await app.request('/api/transactions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({ amount: 75000, transaction_date: '2026-07-06', category_id: 2 })
      }, env(mockDb))

      const res = await app.request('/api/transactions', {
        headers: { 'Authorization': `Bearer ${token}` }
      }, env(mockDb))
      expect(res.status).toBe(200)
      const body: any = await res.json()
      expect(body.transactions).toBeDefined()
      expect(body.total).toBeGreaterThanOrEqual(1)
    })

    it('gets a single transaction', async () => {
      await app.request('/api/transactions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({ amount: 25000, transaction_date: '2026-07-06', category_id: 1 })
      }, env(mockDb))

      const res = await app.request('/api/transactions/1', {
        headers: { 'Authorization': `Bearer ${token}` }
      }, env(mockDb))
      expect(res.status).toBe(200)
      const body: any = await res.json()
      expect(body.amount).toBe(25000)
    })

    it('filters transactions by month/year', async () => {
      await app.request('/api/transactions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({ amount: 10000, transaction_date: '2026-01-15', category_id: 1 })
      }, env(mockDb))
      await app.request('/api/transactions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({ amount: 20000, transaction_date: '2026-02-20', category_id: 2 })
      }, env(mockDb))

      const res = await app.request('/api/transactions?month=2&year=2026', {
        headers: { 'Authorization': `Bearer ${token}` }
      }, env(mockDb))
      expect(res.status).toBe(200)
      const body: any = await res.json()
      expect(body.total).toBe(1) // Only February transaction
    })

    it('rejects unauthenticated requests', async () => {
      const res = await app.request('/api/transactions', {
        headers: { 'Authorization': 'Bearer invalid' }
      }, env(mockDb))
      expect(res.status).toBe(401)
    })
  })

  // ============================================================
  //  STATS
  // ============================================================

  describe('GET /api/stats/summary', () => {
    it('returns zero stats when no transactions', async () => {
      const token = await genToken()
      const res = await app.request('/api/stats/summary', {
        headers: { 'Authorization': `Bearer ${token}` }
      }, env(mockDb))
      expect(res.status).toBe(200)
      const body: any = await res.json()
      expect(body.income).toBe(0)
      expect(body.expense).toBe(0)
      expect(body.balance).toBe(0)
    })
  })
})
