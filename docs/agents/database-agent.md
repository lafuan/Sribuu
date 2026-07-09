# Database Agent — D1 Query, Index & Performance Audit

**Schedule:** Daily 05:00, 13:00, 21:00 WIB
**Model:** `ocg`
**Skills:** Clean Architecture, DDIA Systems

## Activity Log

| Date | Issues Created | Queries Audited | Recommendations |
|------|----------------|-----------------|----------------|
| 2026-07-08 | #562, #563, #564 | All 20 SQL queries in _worker.js | Stats endpoint dead code; 3 dead columns; category_id silent default |
| 2026-07-08 (21:00) | #608, #609 | All 20 SQL queries re-audited | Frontend stats only receives 50 tx; payment method broken at POST + PUT |
| 2026-07-09 (13:00) | #660, #662, #663, #664 | Full re-audit post-PR#637 (all queries in _worker.ts) | Income/expense regression (classification flipped); amount validation allows negatives; Promise.all() lacks snapshot isolation; Rules API schema drift remains |

**Latest Run:** 2026-07-09 13:00 WIB

## Findings Summary

### New Issues (2026-07-09 13:00 WIB)

| # | Severity | Title | Impact |
|---|----------|-------|--------|
| 660 | 🔴 CRITICAL | Income/expense classification regression after PR#637 — frontend sends positive amounts, backend treats all as income | Every transaction shows as income instead of expense; monthly balance inflated 100% |
| 662 | 🟡 MEDIUM | POST /api/transactions amount validation uses falsy check — rejects zero, allows negative values silently | Negative amounts bypass validation; zero amounts rejected despite schema allowing it |
| 663 | 🟡 MEDIUM | Promise.all() for parallel D1 queries risks inconsistent snapshot — concurrent writes cause mismatched SELECT vs COUNT | Pagination metadata inconsistent under concurrent writes; .batch() would fix |
| 664 | 🔴 HIGH | Rules API still broken after PR#637 — last remaining schema drift, INSERT references non-existent columns | Rules feature has never worked; any create/update call throws 500 error |

### New Queries Audited

All queries from current `_worker.ts` (post-PR#637, 22 total SQL statements):

| Endpoint | Query | Status | Notes |
|----------|-------|--------|-------|
| `POST /api/auth/register` | `SELECT id FROM users WHERE email = ?` | Existing | TOCTOU race (issue #472) |
| `POST /api/auth/register` | `INSERT INTO users (name, email, password_hash)` | Existing | OK |
| `POST /api/auth/login` | `SELECT id, name, email, password_hash FROM users WHERE email = ?` | Existing | OK |
| `GET /api/categories` | `SELECT ... FROM categories WHERE is_active = 1 AND (user_id IS NULL OR user_id = ?)` | Existing | OR defeats index (issue #419) |
| `GET /api/payment-methods` | `SELECT ... FROM payment_methods WHERE is_active = 1` | Existing | No user_id filter (issue #424) |
| `GET /api/transactions` (list) | `SELECT t.id, t.amount, t.notes, t.payment_method_id, ...` | ✅ **FIXED in PR#637** | Now uses real `notes` and `payment_method_id` columns; no more `description as notes` or `NULL as payment_method_id` |
| `GET /api/transactions` (count) | `SELECT COUNT(*) ...` | Existing | Still uses regex hack + unnecessary LEFT JOIN (issue #421) |
| `POST /api/transactions` (INSERT) | `INSERT INTO transactions (user_id, amount, transaction_date, category_id, notes, payment_method_id)` | ✅ **FIXED in PR#637** | No more `type` hardcode; no more `description`/`type` columns |
| `POST /api/transactions` (re-fetch) | `SELECT t.id, t.amount, t.notes, t.payment_method_id, ... WHERE t.id = ?` | ✅ **FIXED** | Returns real `payment_method_id` (no longer NULL) |
| `GET /api/transactions/:id` | `SELECT ... WHERE t.id = ? AND t.user_id = ?` | ✅ **FIXED** | Returns real `notes` and `payment_method_id` |
| `PUT /api/transactions/:id` (check) | `SELECT id FROM transactions WHERE id = ? AND user_id = ?` | Existing | Wasted query (issue #471) |
| `PUT /api/transactions/:id` (UPDATE) | `UPDATE transactions SET ... WHERE id = ? AND user_id = ?` | Existing | Dynamic SQL (issue #377); no updated_at (issue #420) |
| `PUT /api/transactions/:id` (re-fetch) | `SELECT ... FROM transactions t LEFT JOIN categories c ... WHERE t.id = ?` | ✅ **FIXED** | Returns real `notes` and `payment_method_id` |
| `DELETE /api/transactions/:id` (check) | `SELECT id FROM transactions WHERE id = ? AND user_id = ?` | Existing | Wasted query (issue #471) |
| `DELETE /api/transactions/:id` (delete) | `DELETE FROM transactions WHERE id = ? AND user_id = ?` | Existing | OK |
| `GET /api/stats/summary` (income) | `SELECT COALESCE(SUM(amount), 0) as total FROM transactions WHERE user_id = ? AND amount > 0` | ✅ **FIXED** | No more `type = 'income'` dead code; uses amount sign now |
| `GET /api/stats/summary` (expense) | `SELECT COALESCE(SUM(amount), 0) as total FROM transactions WHERE user_id = ? AND amount < 0` | ✅ **FIXED** | No more `type = 'expense'` dead code; uses amount sign now |
| `GET /api/rules` (list) | `SELECT * FROM rules WHERE user_id = ? OR user_id IS NULL` | Existing | SELECT * (issue #303); OR pattern may defeat index |
| `POST /api/rules` (INSERT) | `INSERT INTO rules (user_id, name, description, condition, action, priority)` | ❌ **STILL BROKEN** | References non-existent columns; schema drift unfixed (issue #664 / #480) |
| `PUT /api/rules/:id` (UPDATE) | `UPDATE rules SET ...` | ❌ **STILL BROKEN** | Same schema drift |
| `DELETE /api/rules/:id` (check) | `SELECT id FROM rules WHERE id = ? AND user_id = ?` | Existing | Wasted query |

### Schema Design Review

| Table | Columns | Indexes | Issues |
|-------|---------|---------|--------|
| `users` | 7 | 1 (email) | notification_enabled/reminder_time dead (issue #563) |
| `transactions` | 11 | 5 | attachment_path dead (issue #563); parent_transaction_id dead (issue #422) |
| `categories` | 7 | 2 | OR-index issue (issue #419) |
| `payment_methods` | 5 | 1 | OK |
| `rules` | 9 | 2 | Schema drift UNFIXED (issue #664) |
| `budgets` | 6 | 2 | No API (issue #482) |
| `subscriptions` | 9 | 2 | No API (issue #482) |
| `bills` | 9 | 2 | No API (issue #482) |
| `transaction_templates` | 7 | 1 | No API (issue #482) |

### Open Database Issues: 54+ active (excluding deploy/CI issues)
