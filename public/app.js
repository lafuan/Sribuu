// ===== API Client =====
const API = {
  async request(method, path, body) {
    const opts = { method, headers: {} }
    const token = localStorage.getItem('token')
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
}

// ===== HTML sanitization helper =====
function escapeHtml(str) {
  if (str == null) return ''
  const div = document.createElement('div')
  div.textContent = str
  return div.innerHTML
}

// ===== Auth =====
function isLoggedIn() { return !!localStorage.getItem('token') }

function logout() {
  localStorage.removeItem('token')
  localStorage.removeItem('user')
  window.location.href = '/'
}

// ===== Toast =====
function showToast(msg, type = 'info') {
  const el = document.getElementById('toast')
  el.textContent = msg
  el.className = `toast show ${type}`
  clearTimeout(el._timer)
  el._timer = setTimeout(() => el.classList.remove('show'), 2500)
}

// ===== Formatting =====
function formatMoney(n) {
  return n.toLocaleString('id-ID', { minimumFractionDigits: 0, maximumFractionDigits: 0 })
}

function formatDate(dateStr) {
  const d = new Date(dateStr + 'T00:00:00')
  const months = ['Jan','Feb','Mar','Apr','Mei','Jun','Jul','Agu','Sep','Okt','Nov','Des']
  return `${d.getDate()} ${months[d.getMonth()]} ${d.getFullYear()}`
}

// ===== Color helpers =====
function hexToRgba(hex, alpha) {
  const r = parseInt(hex.slice(1,2), 16) * 17
  const g = parseInt(hex.slice(2,3), 16) * 17
  const b = parseInt(hex.slice(3,4), 16) * 17
  return `rgba(${r},${g},${b},${alpha})`
}

// ===== Transaction Icon =====
function getCatIcon(cat) { return cat?.icon || '📦' }
function getCatColor(cat) { return cat?.color || '#6366f1' }
function getCatName(cat) { return cat?.category_name || cat?.name || 'Uncategorized' }

// ===== Render transaction item =====
function renderTx(tx) {
  const isExpense = tx.amount < 0
  const absAmt = Math.abs(tx.amount)
  const color = tx.category_color || '#6366f1'
  return `
    <div class="tx-item ${isExpense ? 'expense' : 'income'}" data-id="${tx.id}" onclick="openEditTx(${tx.id})">
      <div class="tx-icon" style="background:${hexToRgba(color, 0.15)}">${escapeHtml(tx.category_icon) || '📦'}</div>
      <div class="tx-info">
        <div class="tx-category">${escapeHtml(tx.category_name) || 'Uncategorized'}</div>
        ${tx.notes ? `<div class="tx-notes">${escapeHtml(tx.notes)}</div>` : ''}
      </div>
      <div class="tx-right">
        <div class="tx-amount">${isExpense ? '-' : '+'}Rp${formatMoney(absAmt)}</div>
        <div class="tx-date">${formatDate(tx.transaction_date)}</div>
      </div>
    </div>`
}

// ===== Load transactions =====
let currentFilter = {}

async function loadTransactions() {
  try {
    const data = await API.getTransactions(currentFilter)
    const list = document.getElementById('tx-list')
    const totalEl = document.getElementById('tx-count')
    if (data.transactions.length === 0) {
      list.innerHTML = '<div class="tx-empty">Belum ada transaksi.<br>Klik "Tambah" untuk mulai mencatat</div>'
    } else {
      list.innerHTML = data.transactions.map(renderTx).join('')
    }
    if (totalEl) totalEl.textContent = data.total
  } catch (e) {
    document.getElementById('tx-list').innerHTML = `<div class="tx-empty">Gagal memuat transaksi</div>`
  }
}

// ===== Load categories & payment methods =====
let categories = []
let paymentMethods = []

async function loadMeta() {
  try {
    categories = await API.getCategories()
    paymentMethods = await API.getPaymentMethods()
    
    // Populate filters
    const filterBar = document.getElementById('filter-bar')
    if (filterBar) {
      let html = '<button class="filter-chip active" onclick="setFilter({})">Semua</button>'
      categories.forEach(c => {
        html += `<button class="filter-chip" data-cat="${c.id}" onclick="setFilter({category_id:${c.id}})">${escapeHtml(c.icon)} ${escapeHtml(c.name)}</button>`
      })
      filterBar.innerHTML = html
    }
  } catch (e) { /* pass */ }
}

function setFilter(f) {
  currentFilter = f
  // Update chip active state
  document.querySelectorAll('#filter-bar .filter-chip').forEach(chip => {
    const catId = chip.dataset.cat
    chip.classList.toggle('active', (!f.category_id && !catId) || (catId && Number(catId) === f.category_id))
  })
  loadTransactions()
}

// ===== Modal: Add Transaction =====
async function openAddTx() {
  const modal = document.getElementById('tx-modal')
  document.getElementById('modal-title').textContent = 'Transaksi Baru'
  document.getElementById('tx-form').reset()
  document.getElementById('tx-id').value = ''
  document.getElementById('tx-submit').textContent = 'Simpan'
  document.getElementById('tx-delete').style.display = 'none'
  
  await populateSelects()
  // Default: today, expense
  document.getElementById('tx-date').value = new Date().toISOString().split('T')[0]
  document.getElementById('tx-amount').value = ''
  modal.classList.add('open')
}

async function openEditTx(id) {
 try {
   const tx = await API.getTransaction(id)
   const modal = document.getElementById('tx-modal')
   document.getElementById('modal-title').textContent = 'Edit Transaksi'
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
      categories.map(c => `<option value="${c.id}">${escapeHtml(c.icon)} ${escapeHtml(c.name)}</option>`).join('')
    
    const payEl = document.getElementById('tx-payment')
    payEl.innerHTML = '<option value="">Pilih metode</option>' +
      paymentMethods.map(p => `<option value="${p.id}">${escapeHtml(p.icon)} ${escapeHtml(p.name)}</option>`).join('')
  } catch (e) { /* pass */ }
}

async function submitTx() {
 const id = document.getElementById('tx-id').value
 const btn = document.getElementById('tx-submit')
 btn.disabled = true
 
 try {
   const type = document.querySelector('input[name="transaction_type"]:checked').value
   let amount = Number(document.getElementById('tx-amount').value)
   if (type === 'expense') {
     amount = -Math.abs(amount)
   }

   const data = {
     amount: amount,
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
  } catch (e) {
    showToast('Gagal menghapus', 'error')
  }
}

function closeModal() {
  document.getElementById('tx-modal').classList.remove('open')
}
