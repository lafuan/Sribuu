// ============================================================
// Sribuu — Y2K Console Chrome Finance SPA
// Design: Nintendo 2001 → Sribuu green/teal adaptation
// ============================================================

// ─── Safe localStorage (handles private browsing quarantine) ──
const ls = {
  getItem(k, fallback = null) { try { return localStorage.getItem(k) } catch { return fallback } },
  setItem(k, v) { try { localStorage.setItem(k, v) } catch {} },
  removeItem(k) { try { localStorage.removeItem(k) } catch {} },
}
const lsGet = (k, fb = null) => { try { return localStorage.getItem(k) } catch { return fb } }

// ─── API Client ──────────────────────────────────────────────
const API = {
  async request(method, path, body) {
    const opts = { method, headers: {} }
    const token = ls.getItem('token')
    if (token) opts.headers['Authorization'] = `Bearer ${token}`
    if (body) { opts.headers['Content-Type'] = 'application/json'; opts.body = JSON.stringify(body) }
    const res = await fetch(path, opts)
    const data = await res.json()
    if (!res.ok) throw new Error(data.error || 'Request failed')
    return data
  },
  register: (name, email, password) => API.request('POST', '/api/auth/register', { name, email, password }),
  login: (email, password) => API.request('POST', '/api/auth/login', { email, password }),
  me: () => API.request('GET', '/api/auth/me'),
  getTransactions: (params) => {
    const q = new URLSearchParams(params || {}).toString()
    return API.request('GET', `/api/transactions${q ? '?' + q : ''}`)
  },
  getTransaction: (id) => API.request('GET', `/api/transactions/${id}`),
  createTransaction: (data) => API.request('POST', '/api/transactions', data),
  updateTransaction: (id, data) => API.request('PUT', `/api/transactions/${id}`, data),
  deleteTransaction: (id) => API.request('DELETE', `/api/transactions/${id}`),
  getCategories: () => API.request('GET', '/api/categories'),
  getPaymentMethods: () => API.request('GET', '/api/payment-methods'),
  getMonthlyStats: (params) => {
    const q = new URLSearchParams(params || {}).toString()
    return API.request('GET', `/api/stats/summary${q ? '?' + q : ''}`)
  },
}

// ─── Helpers ─────────────────────────────────────────────────
function escapeHtml(str) {
  if (str == null) return ''
  const div = document.createElement('div')
  div.textContent = str
  return div.innerHTML
}

function formatMoney(n) {
  return n.toLocaleString('id-ID', { minimumFractionDigits: 0, maximumFractionDigits: 0 })
}

function formatDate(dateStr) {
  const d = new Date(dateStr + 'T00:00:00')
  const months = ['Jan','Feb','Mar','Apr','Mei','Jun','Jul','Agu','Sep','Okt','Nov','Des']
  return `${d.getDate()} ${months[d.getMonth()]} ${d.getFullYear()}`
}

function hexToRgba(hex, alpha) {
  const r = parseInt(hex.slice(1,2), 16) * 17
  const g = parseInt(hex.slice(2,3), 16) * 17
  const b = parseInt(hex.slice(3,4), 16) * 17
  return `rgba(${r},${g},${b},${alpha})`
}

// ─── State ───────────────────────────────────────────────────
let categories = []
let paymentMethods = []
let currentFilter = {}
let allTransactions = []

// ─── Toast ───────────────────────────────────────────────────
function showToast(msg, type = 'info') {
  const el = document.getElementById('toast')
  el.textContent = msg
  el.className = `toast show ${type}`
  clearTimeout(el._timer)
  el._timer = setTimeout(() => el.classList.remove('show'), 2500)
}

// ─── Auth ────────────────────────────────────────────────────
function isLoggedIn() { return !!ls.getItem('token') }

function logout() {
  ls.removeItem('token')
  ls.removeItem('user')
  window.location.href = '/'
}

// ─── App Shell ───────────────────────────────────────────────
function renderAppShell() {
  const user = JSON.parse(ls.getItem('user') || '{}')
  const initial = (user.name || '?').charAt(0).toUpperCase()
  return `
    <!-- Nav Bar -->
    <header class="nav-bar halftone">
      <div class="logo"><em>S</em>RIBUU</div>
      <button class="user-badge" onclick="showLogout()" aria-label="User menu">
        <span>${escapeHtml(user.name || '')}</span>
        <div class="avatar">${escapeHtml(initial)}</div>
      </button>
    </header>

    <!-- Balance Hero -->
    <div class="balance-hero" id="balance-hero">
      <div class="month-badge" id="month-badge">${getMonthLabel()}</div>
      <div class="balance-label">Saldo Bulan Ini</div>
      <div class="balance-amount" id="balance-amount">Rp0</div>
      <div class="stats-row">
        <div class="stat-item">Pemasukan<br><span class="income-val" id="stat-income">Rp0</span></div>
        <div class="stat-item">Pengeluaran<br><span class="expense-val" id="stat-expense">Rp0</span></div>
        <div class="stat-item">Transaksi<br><span class="count-val" id="stat-count">0</span></div>
      </div>
    </div>

    <!-- Quick Actions -->
    <div class="quick-actions">
      <button class="qa-btn primary" onclick="openAddTx()">+ TAMBAH</button>
      <button class="qa-btn secondary" onclick="openMonthPicker()" aria-label="Filter bulan"><span role="img" aria-hidden="true">📅</span> FILTER BULAN</button>
    </div>

    <!-- Section Header -->
    <div class="section-header">
      <h2><span role="img" aria-label="Transaksi">📋</span> Transaksi <span id="tx-count"></span></h2>
      <button class="filter-btn" onclick="document.getElementById('filter-bar').scrollIntoView({behavior:'smooth'})">Kategori</button>
    </div>

    <!-- Filter Chips -->
    <div class="filter-bar" id="filter-bar"></div>

    <!-- Transaction List -->
    <div class="tx-list" id="tx-list">
      <div class="tx-empty"><span class="empty-icon" role="img" aria-label="Catatan">📒</span>Memuat transaksi...</div>
    </div>

    <!-- Bottom Nav -->
    <nav class="bottom-nav halftone">
      <button class="active" data-nav="beranda"><span class="nav-icon" role="img" aria-label="Beranda">🏠</span>Beranda</button>
      <button onclick="openAddTx()" data-nav="tambah"><span class="nav-icon" role="img" aria-label="Tambah">➕</span>Tambah</button>
      <button onclick="if(confirm('Keluar dari akun ini?'))logout()" data-nav="keluar"><span class="nav-icon" role="img" aria-label="Keluar">🚪</span>Keluar</button>
    </nav>

    <!-- Transaction Modal -->
    <div class="modal-overlay" id="tx-modal" onclick="if(event.target===this)closeModal()">
      <div class="modal">
        <div class="modal-header">
          <h2 id="modal-title">TRANSAKSI BARU</h2>
          <button class="modal-close" onclick="closeModal()">✕</button>
        </div>
        <div class="modal-body">
          <form id="tx-form" onsubmit="event.preventDefault();submitTx()">
            <input type="hidden" id="tx-id">
            <div class="form-group">
              <label>Jenis</label>
              <div class="type-switch">
                <input type="radio" id="type-expense" name="transaction_type" value="expense" checked>
                <label for="type-expense">Pengeluaran</label>
                <input type="radio" id="type-income" name="transaction_type" value="income">
                <label for="type-income">Pemasukan</label>
              </div>
            </div>
            <div class="form-group">
              <label>Tanggal</label>
              <input type="date" id="tx-date" required>
            </div>
            <div class="form-group">
              <label>Jumlah (Rp)</label>
              <input type="number" id="tx-amount" min="0" step="1000" placeholder="15000" required>
            </div>
            <div class="form-group">
              <label>Kategori</label>
              <select id="tx-category"></select>
            </div>
            <div class="form-group">
              <label>Metode Bayar</label>
              <select id="tx-payment"></select>
            </div>
            <div class="form-group">
              <label>Catatan</label>
              <textarea id="tx-notes" placeholder="Contoh: Nasi goreng + es teh" rows="2"></textarea>
            </div>
            <button type="submit" class="btn-submit" id="tx-submit">Simpan</button>
            <button type="button" class="btn-delete" id="tx-delete" style="display:none" onclick="deleteTx()">Hapus</button>
          </form>
        </div>
      </div>
    </div>

    <!-- Toast -->
    <div class="toast" id="toast"></div>
  `
}

function getMonthLabel() {
  const months = ['Januari','Februari','Maret','April','Mei','Juni','Juli','Agustus','September','Oktober','November','Desember']
  const now = new Date()
  return `${months[now.getMonth()]} ${now.getFullYear()}`
}

// ─── Auth Page ───────────────────────────────────────────────
function renderAuthPage() {
  return `
  <div class="auth-page">
    <div class="auth-box">
      <div class="auth-logo">
        <div class="logo-pill">SRIBUU</div>
        <p>Catat & kelola keuangan harian</p>
      </div>
      <div class="auth-tabs">
        <button class="auth-tab active" data-tab="login">Masuk</button>
        <button class="auth-tab" data-tab="register">Daftar</button>
      </div>
      <form class="auth-form" id="auth-login-form" onsubmit="handleLogin(event)">
        <input type="email" id="login-email" placeholder="Email" required autocomplete="email">
        <input type="password" id="login-password" placeholder="Password" required autocomplete="current-password">
        <div class="auth-error" id="login-error"></div>
        <button type="submit" class="btn" id="login-btn">Masuk</button>
      </form>
      <form class="auth-form" id="auth-register-form" style="display:none" onsubmit="handleRegister(event)">
        <input type="text" id="reg-name" placeholder="Nama" required autocomplete="name">
        <input type="email" id="reg-email" placeholder="Email" required autocomplete="email">
        <input type="password" id="reg-password" placeholder="Password (min 6 karakter)" required minlength="6" autocomplete="new-password">
        <div class="auth-error" id="reg-error"></div>
        <button type="submit" class="btn" id="reg-btn">Daftar</button>
      </form>
    </div>
  </div>`
}

function switchAuthTab(tab) {
  document.querySelectorAll('.auth-tab').forEach(t => t.classList.remove('active'))
  document.getElementById('auth-login-form').style.display = tab === 'login' ? '' : 'none'
  document.getElementById('auth-register-form').style.display = tab === 'register' ? '' : 'none'
  document.querySelector(`.auth-tab[data-tab="${tab}"]`)?.classList.add('active')
  document.getElementById('login-error').style.display = 'none'
  document.getElementById('reg-error').style.display = 'none'
}

function showAuthError(id, msg) {
  const el = document.getElementById(id)
  el.textContent = msg
  el.style.display = 'block'
}

async function handleLogin(e) {
  e.preventDefault()
  const btn = document.getElementById('login-btn')
  btn.disabled = true; btn.textContent = 'Memproses...'
  document.getElementById('login-error').style.display = 'none'
  try {
    const data = await API.login(
      document.getElementById('login-email').value,
      document.getElementById('login-password').value
    )
    ls.setItem('token', data.token)
    ls.setItem('user', JSON.stringify(data.user))
    window.location.href = '/app'
  } catch (e) {
    showAuthError('login-error', e.message)
  }
  btn.disabled = false; btn.textContent = 'Masuk'
}

async function handleRegister(e) {
  e.preventDefault()
  const btn = document.getElementById('reg-btn')
  btn.disabled = true; btn.textContent = 'Memproses...'
  document.getElementById('reg-error').style.display = 'none'
  try {
    const data = await API.register(
      document.getElementById('reg-name').value,
      document.getElementById('reg-email').value,
      document.getElementById('reg-password').value
    )
    ls.setItem('token', data.token)
    ls.setItem('user', JSON.stringify(data.user))
    window.location.href = '/app'
  } catch (e) {
    showAuthError('reg-error', e.message)
  }
  btn.disabled = false; btn.textContent = 'Daftar'
}

// ─── Transaction Rendering ──────────────────────────────────
function getCatIcon(cat) { return cat?.icon || '📦' }
function getCatColor(cat) { return cat?.color || '#6366f1' }
function getCatName(cat) { return cat?.category_name || cat?.name || 'Uncategorized' }

function renderTx(tx) {
  const isExpense = tx.amount < 0
  const absAmt = Math.abs(tx.amount)
  const icon = tx.category_icon || '📦'
  const catName = tx.category_name || 'Uncategorized'
  return `
    <div class="tx-item ${isExpense ? 'expense' : 'income'}" data-tx-id="${tx.id}">
      <div class="tx-icon">${escapeHtml(icon)}</div>
      <div class="tx-info">
        <div class="tx-category">${escapeHtml(catName)}</div>
        ${tx.notes ? `<div class="tx-notes">${escapeHtml(tx.notes)}</div>` : ''}
      </div>
      <div class="tx-right">
        <div class="tx-amount">${isExpense ? '-' : '+'}Rp${formatMoney(absAmt)}</div>
        <div class="tx-date">${formatDate(tx.transaction_date)}</div>
      </div>
    </div>`
}

// ─── Data Loading ───────────────────────────────────────────
async function loadTransactions() {
  try {
    const data = await API.getTransactions(currentFilter)
    allTransactions = data.transactions || []
    const list = document.getElementById('tx-list')
    const totalEl = document.getElementById('tx-count')
    if (allTransactions.length === 0) {
      list.innerHTML = '<div class="tx-empty"><span class="empty-icon" role="img" aria-label="Catatan">📒</span>Belum ada transaksi.<br><button class="empty-action" onclick="openAddTx()">+ Tambah Transaksi</button></div>'
    } else {
      list.innerHTML = allTransactions.map(renderTx).join('')
    }
    if (totalEl) totalEl.textContent = allTransactions.length > 0 ? `(${data.total || allTransactions.length})` : ''
  } catch (e) {
    document.getElementById('tx-list').innerHTML = '<div class="tx-empty">⚠️ Gagal memuat transaksi</div>'
  }
}

async function loadMeta() {
  try {
    categories = await API.getCategories()
    paymentMethods = await API.getPaymentMethods()
    renderFilterChips()
  } catch (e) { /* pass */ }
}

function renderFilterChips() {
  const filterBar = document.getElementById('filter-bar')
  if (!filterBar) return
  let html = '<button class="filter-chip active" data-cat="">Semua</button>'
  categories.forEach(c => {
    html += `<button class="filter-chip" data-cat="${c.id}">${escapeHtml(c.icon || '')} ${escapeHtml(c.name)}</button>`
  })
  filterBar.innerHTML = html
}

function setFilter(f) {
  currentFilter = f
  document.querySelectorAll('#filter-bar .filter-chip').forEach(chip => {
    const catId = chip.dataset.cat
    chip.classList.toggle('active', (!f.category_id && !catId) || (catId && Number(catId) === f.category_id))
  })
  loadTransactions()
}

function updateMonthlyStatsUI(income, expense, count, balance) {
  document.getElementById('stat-income').textContent = `Rp${formatMoney(income || 0)}`
  document.getElementById('stat-expense').textContent = `Rp${formatMoney(expense || 0)}`
  document.getElementById('stat-count').textContent = count || 0
  document.getElementById('balance-amount').textContent = `Rp${formatMoney(balance || 0)}`
}

async function loadMonthlyStats() {
  try {
    const now = new Date()
    const month = String(now.getMonth() + 1).padStart(2, '0')
    const year = now.getFullYear()
    const data = await API.getMonthlyStats({ month, year })
    updateMonthlyStatsUI(data.income, data.expense, data.count, data.balance)
  } catch (e) { /* pass */ }
}

// ─── Modal: Add / Edit Transaction ──────────────────────────
async function openAddTx() {
  const modal = document.getElementById('tx-modal')
  document.getElementById('modal-title').textContent = 'TRANSAKSI BARU'
  document.getElementById('tx-form').reset()
  document.getElementById('tx-id').value = ''
  document.getElementById('tx-submit').textContent = 'Simpan'
  document.getElementById('tx-delete').style.display = 'none'
  await populateSelects()
  document.getElementById('tx-date').value = new Date().toISOString().split('T')[0]
  modal.classList.add('open')
}

async function openEditTx(id) {
  try {
    const tx = await API.getTransaction(id)
    const modal = document.getElementById('tx-modal')
    document.getElementById('modal-title').textContent = 'EDIT TRANSAKSI'
    document.getElementById('tx-id').value = id
    document.getElementById('tx-submit').textContent = 'Update'
    document.getElementById('tx-delete').style.display = 'block'
    await populateSelects()
    document.getElementById('tx-date').value = tx.transaction_date
    document.getElementById('tx-amount').value = Math.abs(tx.amount)
    document.getElementById('type-expense').checked = tx.amount < 0
    document.getElementById('type-income').checked = tx.amount >= 0
    document.getElementById('tx-category').value = tx.category_id || ''
    document.getElementById('tx-payment').value = tx.payment_method_id || ''
    document.getElementById('tx-notes').value = tx.notes || ''
    modal.classList.add('open')
  } catch (e) {
    showToast('Gagal memuat transaksi', 'error')
  }
}

async function populateSelects() {
  try {
    if (categories.length === 0) categories = await API.getCategories()
    if (paymentMethods.length === 0) paymentMethods = await API.getPaymentMethods()
    const catEl = document.getElementById('tx-category')
    catEl.innerHTML = '<option value="">Pilih kategori</option>' +
      categories.map(c => `<option value="${c.id}">${escapeHtml(c.icon || '')} ${escapeHtml(c.name)}</option>`).join('')
    const payEl = document.getElementById('tx-payment')
    payEl.innerHTML = '<option value="">Pilih metode</option>' +
      paymentMethods.map(p => `<option value="${p.id}">${escapeHtml(p.icon || '')} ${escapeHtml(p.name)}</option>`).join('')
  } catch (e) { /* pass */ }
}

async function submitTx() {
  const id = document.getElementById('tx-id').value
  const btn = document.getElementById('tx-submit')
  btn.disabled = true
  try {
    const type = document.querySelector('input[name="transaction_type"]:checked').value
    let amount = Number(document.getElementById('tx-amount').value)
    if (type === 'expense') amount = -Math.abs(amount)
    const data = {
      amount,
      transaction_date: document.getElementById('tx-date').value,
      category_id: document.getElementById('tx-category').value || null,
      payment_method_id: document.getElementById('tx-payment').value || null,
      notes: document.getElementById('tx-notes').value || null,
    }
    if (!data.amount || !data.transaction_date) {
      showToast('Jumlah dan tanggal wajib diisi', 'error')
      btn.disabled = false
      return
    }
    if (id) {
      await API.updateTransaction(id, data)
      showToast('Transaksi diupdate', 'success')
    } else {
      await API.createTransaction(data)
      showToast('Transaksi ditambahkan', 'success')
    }
    closeModal()
    loadTransactions()
    loadMonthlyStats()
  } catch (e) {
    showToast(e.message || 'Gagal menyimpan', 'error')
  }
  btn.disabled = false
}

async function deleteTx() {
  const id = document.getElementById('tx-id').value
  if (!id || !confirm('Hapus transaksi ini?')) return
  try {
    await API.deleteTransaction(id)
    showToast('Transaksi dihapus', 'success')
    closeModal()
    loadTransactions()
    loadMonthlyStats()
  } catch (e) {
    showToast('Gagal menghapus', 'error')
  }
}

function closeModal() {
  document.getElementById('tx-modal').classList.remove('open')
}

function showLogout() {
  if (confirm('Keluar dari akun ini?')) logout()
}

function openMonthPicker() {
  const now = new Date()
  const month = prompt('Bulan (1-12):', now.getMonth() + 1)
  if (month === null) return
  const year = prompt('Tahun (contoh: 2026):', now.getFullYear())
  if (year === null) return
  setFilter({ month, year })
}

// ─── Init ────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', function() {
  const app = document.getElementById('app')
  if (!app) return

  // Check if we're on the auth page or the app page
  const isAuthPage = window.location.pathname === '/' || window.location.pathname.endsWith('index.html')

  if (isAuthPage && !isLoggedIn()) {
    app.innerHTML = renderAuthPage()
  } else if (isAuthPage && isLoggedIn()) {
    window.location.href = '/app'
  } else {
    // App page
    if (!isLoggedIn()) { window.location.href = '/'; return }
    app.innerHTML = renderAppShell()
    loadMeta()
    loadTransactions()
    loadMonthlyStats()

    // Event delegation — replaces insecure inline onclick with data-* attrs
    document.addEventListener('click', function(e) {
      // Auth tab click → switch form
      const authTab = e.target.closest('.auth-tab')
      if (authTab && authTab.dataset.tab) {
        switchAuthTab(authTab.dataset.tab)
        return
      }
      // Transaction item click → open edit
      const txItem = e.target.closest('.tx-item')
      if (txItem && txItem.dataset.txId) {
        openEditTx(Number(txItem.dataset.txId))
        return
      }
      // Filter chip click → set filter
      const filterChip = e.target.closest('.filter-chip')
      if (filterChip) {
        const catId = filterChip.dataset.cat
        setFilter(catId !== '' ? { category_id: Number(catId) } : {})
        return
      }
    })
  }
})
