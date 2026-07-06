import { test, expect, Page } from '@playwright/test'

const MOCK_TOKEN = 'eyJhbGciOiJIUzI1NiJ9.mock.jwt'
const MOCK_USER = { id: 1, name: 'Test User', email: 'test@sribuu.dev' }

/**
 * Set up API mocking for all endpoints the frontend calls.
 * Must be called BEFORE page.goto() so route handlers are ready.
 */
async function setupMockRoutes(page: Page) {
  // ── Auth: Login ──
  await page.route('**/api/auth/login', async (route) => {
    if (route.request().method() !== 'POST') { return route.continue() }
    return route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ token: MOCK_TOKEN, user: MOCK_USER }),
    })
  })

  // ── Auth: Register ──
  await page.route('**/api/auth/register', async (route) => {
    if (route.request().method() !== 'POST') { return route.continue() }
    return route.fulfill({
      status: 201,
      contentType: 'application/json',
      body: JSON.stringify({ token: MOCK_TOKEN, user: MOCK_USER }),
    })
  })

  // ── Categories ──
  await page.route('**/api/categories', async (route) => {
    if (route.request().method() !== 'GET') { return route.continue() }
    return route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([
        { id: 1, name: 'Food', icon: '🍕', color: '#FF5733', is_default: 1, user_id: null },
        { id: 2, name: 'Transport', icon: '🚗', color: '#33A1FF', is_default: 0, user_id: null },
        { id: 3, name: 'Shopping', icon: '🛒', color: '#FF33A1', is_default: 0, user_id: null },
      ]),
    })
  })

  // ── Payment Methods ──
  await page.route('**/api/payment-methods', async (route) => {
    if (route.request().method() !== 'GET') { return route.continue() }
    return route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([
        { id: 1, name: 'Cash', icon: '💵', is_default: 1, is_active: 1 },
        { id: 2, name: 'QRIS', icon: '📱', is_default: 0, is_active: 1 },
      ]),
    })
  })

  // ── Transactions (list, create, get-one, update, delete) ──
  await page.route('**/api/transactions**', async (route) => {
    const url = new URL(route.request().url())
    const path = url.pathname
    const method = route.request().method()
    const today = new Date().toISOString().split('T')[0]

    // GET /api/transactions  (list, possibly with query params)
    if (method === 'GET' && path.endsWith('/api/transactions')) {
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          transactions: [
            {
              id: 1, amount: -50000, description: 'Lunch', notes: 'Lunch',
              transaction_date: today, category_id: 1, payment_method_id: null,
              category_name: 'Food', category_icon: '🍕', category_color: '#FF5733',
            },
            {
              id: 2, amount: -20000, description: 'Bus fare', notes: 'Bus fare',
              transaction_date: today, category_id: 2, payment_method_id: null,
              category_name: 'Transport', category_icon: '🚗', category_color: '#33A1FF',
            },
          ],
          total: 2,
        }),
      })
    }

    // GET /api/transactions/:id  (single transaction)
    if (method === 'GET' && path.match(/^\/api\/transactions\/\d+$/)) {
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 1, amount: -50000, description: 'Lunch', notes: 'Lunch',
          transaction_date: today, category_id: 1, payment_method_id: null,
          category_name: 'Food', category_icon: '🍕', category_color: '#FF5733',
        }),
      })
    }

    // POST /api/transactions  (create)
    if (method === 'POST' && path.endsWith('/api/transactions')) {
      return route.fulfill({
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 3, amount: -75000, description: 'Dinner', notes: 'Dinner',
          transaction_date: today, category_id: 1, payment_method_id: null,
          category_name: 'Food', category_icon: '🍕', category_color: '#FF5733',
        }),
      })
    }

    // PUT /api/transactions/:id  (update)
    if (method === 'PUT' && path.match(/^\/api\/transactions\/\d+$/)) {
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 1, amount: -55000, description: 'Lunch updated', notes: 'Lunch updated',
          transaction_date: today, category_id: 1, payment_method_id: null,
          category_name: 'Food', category_icon: '🍕', category_color: '#FF5733',
        }),
      })
    }

    // DELETE /api/transactions/:id
    if (method === 'DELETE' && path.match(/^\/api\/transactions\/\d+$/)) {
      return route.fulfill({
        status: 200, contentType: 'application/json',
        body: JSON.stringify({ success: true }),
      })
    }

    return route.continue()
  })

  // ── Stats (the app calls API.getTransactions({ month, year }) which maps to same /api/transactions route) ──
  // Already handled by the transactions route above.
}

/**
 * Inject auth state into localStorage BEFORE the page's JS executes.
 * This eliminates the race condition between addInitScript and page scripts.
 */
async function setAuthLocalStorage(page: Page) {
  await page.addInitScript((args: { token: string; user: Record<string, unknown> }) => {
    localStorage.setItem('token', args.token)
    localStorage.setItem('user', JSON.stringify(args.user))
  }, { token: MOCK_TOKEN, user: MOCK_USER })
}

// ════════════════════════════════════════════════════════════════
//  TESTS
// ════════════════════════════════════════════════════════════════

test.describe('Page Load & Auth', () => {
  test('loads login form when not authenticated', async ({ page }) => {
    await setupMockRoutes(page)
    await page.goto('/', { waitUntil: 'networkidle' })
    await expect(page.locator('#login-email')).toBeVisible({ timeout: 5000 })
  })

  test('login form has email and password fields', async ({ page }) => {
    await setupMockRoutes(page)
    await page.goto('/', { waitUntil: 'networkidle' })
    await expect(page.locator('#login-email')).toBeVisible({ timeout: 5000 })
    await expect(page.locator('#login-password')).toBeVisible({ timeout: 5000 })
  })

  test('register tab switches to register form', async ({ page }) => {
    await setupMockRoutes(page)
    await page.goto('/', { waitUntil: 'networkidle' })
    const regTab = page.locator('button.auth-tab:has-text("Daftar")')
    await expect(regTab).toBeVisible({ timeout: 3000 })
    await regTab.click()
    await expect(page.locator('#reg-email')).toBeVisible({ timeout: 3000 })
    await expect(page.locator('#reg-password')).toBeVisible({ timeout: 3000 })
  })

  test('successful login stores token and redirects to /app', async ({ page }) => {
    await setupMockRoutes(page)
    await page.goto('/', { waitUntil: 'networkidle' })

    await page.locator('#login-email').fill('test@sribuu.dev')
    await page.locator('#login-password').fill('password123')
    await page.locator('#login-btn').click()

    await page.waitForURL('**/app', { timeout: 8000 })
    const token = await page.evaluate(() => localStorage.getItem('token'))
    const user = await page.evaluate(() => localStorage.getItem('user'))
    expect(token).toBe(MOCK_TOKEN)
    expect(JSON.parse(user || '{}').name).toBe('Test User')
  })
})

test.describe('Authenticated Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page)
    await setupMockRoutes(page)
    await page.goto('/app', { waitUntil: 'networkidle' })
  })

  test('shows user name in header', async ({ page }) => {
    await expect(page.locator('#user-name')).toHaveText('Test User', { timeout: 5000 })
  })

  test('shows transaction list with mocked data', async ({ page }) => {
    // Transactions render with category_name visible
    await expect(page.locator('.tx-category')).toContainText(['Food', 'Transport'], { timeout: 5000 })
    // Notes should also render
    await expect(page.locator('.tx-notes').first()).toContainText(/Lunch|Bus fare/, { timeout: 3000 })
  })

  test('shows expense summary in stats card', async ({ page }) => {
    await expect(page.locator('#month-expense')).toContainText(/Rp/, { timeout: 5000 })
    await expect(page.locator('#month-income')).toBeVisible({ timeout: 3000 })
    // The total amount should be rendered (Rp70.000 = 50000 + 20000)
    await expect(page.locator('#month-expense')).toContainText(/70/, { timeout: 3000 })
  })

  test('logout clears token and redirects to home', async ({ page }) => {
    // Click "Keluar" link in the bottom navigation
    const keluarLink = page.locator('a[href="#"]:has-text("Keluar")')
    await expect(keluarLink).toBeVisible({ timeout: 5000 })
    await keluarLink.click()

    // The app calls logout() -> removeItem('token') -> removeItem('user') -> location.href='/'
    // We verify the redirect landed on the login page. Note: addInitScript re-sets
    // localStorage on every navigation, so we check page content instead of storage.
    await page.waitForURL('/', { timeout: 5000 })
    await expect(page.locator('#login-email')).toBeVisible({ timeout: 5000 })
    await expect(page.locator('#login-password')).toBeVisible({ timeout: 3000 })
  })
})

test.describe('Error Handling', () => {
  test('handles API failure gracefully on dashboard', async ({ page }) => {
    await setAuthLocalStorage(page)
    // Force API failures
    await page.route('**/api/transactions**', async (route) => {
      await route.fulfill({ status: 500, body: 'Server Error' })
    })
    await page.route('**/api/categories', async (route) => {
      await route.fulfill({ status: 500, body: 'Server Error' })
    })
    await page.route('**/api/payment-methods', async (route) => {
      await route.fulfill({ status: 500, body: 'Server Error' })
    })
    await page.goto('/app', { waitUntil: 'networkidle' })

    // App should NOT crash — should show error placeholder
    await expect(page.locator('body')).toBeVisible({ timeout: 3000 })
    await expect(page.locator('.tx-list')).toContainText(/Gagal memuat transaksi/, { timeout: 5000 })
  })
})

test.describe('Visual & Layout', () => {
  test('app renders on mobile viewport (375px)', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 })
    await setAuthLocalStorage(page)
    await setupMockRoutes(page)
    await page.goto('/app', { waitUntil: 'networkidle' })
    await expect(page.locator('.app-container')).toBeVisible({ timeout: 5000 })
  })

  test('app renders on tablet viewport (768px)', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 })
    await setAuthLocalStorage(page)
    await setupMockRoutes(page)
    await page.goto('/app', { waitUntil: 'networkidle' })
    await expect(page.locator('.app-container')).toBeVisible({ timeout: 5000 })
  })

  test('page title is set for auth page', async ({ page }) => {
    await page.goto('/')
    const title = await page.title()
    expect(title.length).toBeGreaterThan(0)
  })

  test('page title is set for dashboard', async ({ page }) => {
    await setAuthLocalStorage(page)
    await setupMockRoutes(page)
    await page.goto('/app', { waitUntil: 'networkidle' })
    const title = await page.title()
    expect(title).toContain('Dashboard')
  })
})
