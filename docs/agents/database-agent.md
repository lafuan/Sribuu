# Database Agent — D1 Query, Index & Performance Audit

**Schedule:** Daily 05:00, 13:00, 21:00 WIB
**Model:** `ocg`
**Skills:** Clean Architecture, DDIA Systems

## Activity Log

| Date | Issues Created | Queries Audited | Recommendations |
|------|----------------|-----------------|----------------|
| 2026-07-08 | #562, #563, #564 | All 20 SQL queries in _worker.js | Stats endpoint dead code; 3 dead columns; category_id silent default |

**Latest Run:** 2026-07-08 13:58 WIB

## Findings Summary

### New Issues (2026-07-08 13:00 WIB)

| # | Severity | Title | Impact |
|---|----------|-------|--------|
| 562 | 🟡 MEDIUM | `/api/stats/summary` endpoint is dead code — frontend calculates stats client-side | D1 read quota waste: downloads ALL monthly transactions instead of using aggregate query |
| 563 | 🟢 LOW | Three dead columns with zero API coverage — `attachment_path`, `notification_enabled`, `reminder_time` | Schema weight, developer confusion, ~130KB+ wasted storage per 10K rows |
| 564 | 🟡 MEDIUM | `category_id` silently defaults to 1 for missing/invalid values | Silent data mis-categorization under "Food & Dining" |

### Queries Audited

All SQL queries from `_worker.ts` / `_worker.js` (20 total):

| Endpoint | Query | Issues Found |
|----------|-------|-------------|
| `POST /api/auth/register` | `SELECT id FROM users WHERE email = ?` | TOCTOU race (issue #472) |
| `POST /api/auth/register` | `INSERT INTO users (name, email, password_hash)` | OK |
| `POST /api/auth/login` | `SELECT id, name, email, password_hash FROM users WHERE email = ?` | OK |
| `GET /api/categories` | `SELECT ... FROM categories WHERE is_active = 1 AND (user_id IS NULL OR user_id = ?)` | OR defeats index (issue #419) |
| `GET /api/payment-methods` | `SELECT ... FROM payment_methods WHERE is_active = 1` | No user_id filter (issue #424) |
| `GET /api/transactions` | Main: `SELECT t.id, t.amount, t.description as notes, ... FROM transactions t LEFT JOIN categories c ... WHERE t.user_id = ?` | strftime() prevents index (issue #349/380); OFFSET pagination (issue #376); COUNT copies unnecessary JOIN (issue #421) |
| `GET /api/transactions` | Count: `SELECT COUNT(*) as total FROM transactions t LEFT JOIN categories c ...` | Regex hack fragile; unnecessary LEFT JOIN (issue #421) |
| `POST /api/transactions` | `INSERT INTO transactions (user_id, amount, type, description, transaction_date, category_id) VALUES (?, ?, ?, ?, ?, ?)` | type hardcoded to 'expense' (issue #277); no RETURNING (issue #469); **category_id || 1 silent default (NEW - #564)** |
| `POST /api/transactions` | Post-INSERT: `SELECT t.id, t.amount, t.description as notes, ... WHERE t.id = ?` | INSERT+SELECT pattern (issue #469) |
| `GET /api/transactions/:id` | `SELECT ... FROM transactions t LEFT JOIN categories c ... WHERE t.id = ? AND t.user_id = ?` | OK |
| `PUT /api/transactions/:id` | Existence check: `SELECT id FROM transactions WHERE id = ? AND user_id = ?` | Redundant (see issue #471) |
| `PUT /api/transactions/:id` | Dynamic UPDATE: `UPDATE transactions SET ...` | Dynamic SQL (issue #377); no updated_at (issue #420) |
| `PUT /api/transactions/:id` | Re-fetch: `SELECT ... FROM transactions t LEFT JOIN categories c ... WHERE t.id = ?` | OK |
| `DELETE /api/transactions/:id` | Existence check: `SELECT id FROM transactions WHERE id = ? AND user_id = ?` | Wasted (issue #471) |
| `DELETE /api/transactions/:id` | `DELETE FROM transactions WHERE id = ? AND user_id = ?` | OK |
| `GET /api/stats/summary` | `SELECT COALESCE(SUM(amount), 0) as total FROM transactions WHERE user_id = ? AND type = 'income'` | **Dead code - frontend never calls it (NEW - #562)**; type always 'expense' (issue #277) |
| `GET /api/stats/summary` | `SELECT COALESCE(SUM(amount), 0) as total FROM transactions WHERE user_id = ? AND type = 'expense'` | Same as above |
| `GET /api/rules` | `SELECT * FROM rules WHERE user_id = ? OR user_id IS NULL` | SELECT * (issue #303); OR pattern may defeat index |
| `POST /api/rules` | `INSERT INTO rules (user_id, name, description, condition, action, priority) VALUES (?, ?, ?, ?, ?, ?)` | Schema drift: columns don't match migration (issue #480) |
| `PUT /api/rules/:id` | Dynamic UPDATE: `UPDATE rules SET ...` | Dynamic SQL (issue #377) |

### Schema Design Review

| Table | Columns | Indexes | Issues |
|-------|---------|---------|--------|
| `users` | 7 | 1 (email) | notification_enabled/reminder_time dead (NEW - #563) |
| `transactions` | 11 | 5 | attachment_path dead (NEW - #563); payment_method_id always NULL (issue #417); parent_transaction_id dead (issue #422) |
| `categories` | 7 | 2 | OK (with OR-index issue #419) |
| `payment_methods` | 5 | 1 | OK |
| `rules` | 9 | 2 | Schema drift (issue #480) |
| `budgets` | 6 | 2 | No API (issue #482) |
| `subscriptions` | 9 | 2 | No API (issue #482) |
| `bills` | 9 | 2 | No API (issue #482) |
| `transaction_templates` | 7 | 1 | No API (issue #482) |

### Open Database Issues: 51+ active (excluding deploy/CI issues)
