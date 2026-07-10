# Database Agent — D1 Query, Index & Performance Audit

**Schedule:** Daily 05:00, 13:00, 21:00 WIB
**Model:** `ocg`
**Skills:** Clean Architecture, DDIA Systems

## Activity Log

| Date | Issues Created | Queries Audited | Recommendations |
|------|----------------|-----------------|----------------|
|| 2026-07-08 | #562, #563, #564 | All 20 SQL queries in _worker.js | Stats endpoint dead code; 3 dead columns; category_id silent default |
|| 2026-07-08 (21:00) | #608, #609 | All 20 SQL queries re-audited | Frontend stats only receives 50 tx; payment method broken at POST + PUT |
|| 2026-07-09 (13:00) | #660, #662, #663, #664 | Full re-audit post-PR#637 (all queries in _worker.ts) | Income/expense regression (classification flipped); amount validation allows negatives; Promise.all() lacks snapshot isolation; Rules API schema drift remains |
|| 2026-07-10 (05:00) | #719, #720, #721 | Full re-audit post-PR#688 (all queries in _worker.ts + _worker.js stale vs _worker.ts) | Stale build artifact skews local dev; no pagination UI makes COUNT query waste; loadMonthlyStats() bypasses backend stats endpoint |
|| 2026-07-10 (13:00) | — | Re-audit — no code changes since 05:00 run | Closed #609 (payment_method_id confirmed fixed); no new findings |

**Latest Run:** 2026-07-10 13:00 WIB

## Findings Summary

### New Issues (2026-07-10 05:00 WIB)

| # | Severity | Title | Impact |
|---|----------|-------|--------|
| 719 | 🟡 MEDIUM | Stale _worker.js build artifact — local dev serves wrong SQL after PR #688, amount >= 0 fix not reflected | Local dev environment serves SQL different from production; dev/debug confusion |
| 720 | 🟡 MEDIUM | Frontend has no pagination UI — COUNT query runs wastefully when only first 50 transactions are visible | Every transaction list load wastes 80% of D1 rows read on a COUNT query users can't act on |
| 721 | 🟡 MEDIUM | loadMonthlyStats() bypasses /api/stats/summary — dead endpoint, client-side calc wrong for >50 tx/month | Stats endpoint is dead code; dashboard summary under-reported when user has >50 transactions |

### Status Updates

| # | Previous Status | Current Status | Change |
|---|----------------|----------------|--------|
| 660 | 🔴 CRITICAL — Open (2026-07-09 13:00) | ✅ CLOSED by PR #688 | Income/expense regression fixed |
| 609 | 🟡 MEDIUM — Open (2026-07-08) | ✅ CLOSED by Database Agent (2026-07-10 13:00) | payment_method_id confirmed working in _worker.ts (post-PR#637) |
| 662 | 🟡 MEDIUM — Still Open | Still Open | amount validation still uses !amount falsy check |
| 663 | 🟡 MEDIUM — Still Open | Still Open | Promise.all() still used instead of .batch() |
| 664 | 🔴 HIGH — Still Open | Still Open | Rules API schema drift unfixed (last remaining blocker)

### Queries Audited (2026-07-10 13:00 WIB)

All queries from current `_worker.ts` (post-PR#688, 22 total SQL statements):

| Endpoint | Query | Status | Notes |
|----------|-------|--------|-------|
| POST /api/auth/register (SELECT) | SELECT id FROM users WHERE email = ? | Existing | TOCTOU race (issue #472) |
| POST /api/auth/register (INSERT) | INSERT INTO users (name, email, password_hash) | Existing | OK |
| POST /api/auth/login | SELECT id, name, email, password_hash FROM users WHERE email = ? | Existing | OK |
| GET /api/categories | SELECT ... FROM categories WHERE is_active=1 AND (user_id IS NULL OR user_id=?) | Existing | OR defeats index (issue #419) |
| GET /api/payment-methods | SELECT ... FROM payment_methods WHERE is_active = 1 | Existing | No user_id filter (issue #424) |
| GET /api/transactions (list) | SELECT t.id, t.amount, t.notes, t.payment_method_id, ... | FIXED in PR#637 | Real notes, real payment_method_id |
| GET /api/transactions (count) | SELECT COUNT(*) ... | Existing | Regex hack + LEFT JOIN (issue #421, #720) |
| POST /api/transactions (INSERT) | INSERT INTO transactions (...) VALUES (...) | FIXED in PR#637 | Real columns, no type/description |
| POST /api/transactions (re-fetch) | SELECT ... WHERE t.id = ? | FIXED | Returns real payment_method_id |
| GET /api/transactions/:id | SELECT ... WHERE t.id = ? AND t.user_id = ? | FIXED | Returns real notes, payment_method_id |
| PUT /api/transactions/:id (check) | SELECT id FROM transactions WHERE id = ? AND user_id = ? | Existing | Wasted query (issue #471) |
| PUT /api/transactions/:id (UPDATE) | UPDATE transactions SET ... WHERE id = ? AND user_id = ? | Existing | Dynamic SQL (issue #377); no updated_at (issue #420) |
| PUT /api/transactions/:id (re-fetch) | SELECT ... FROM transactions LEFT JOIN categories WHERE t.id = ? | FIXED | Returns real notes and payment_method_id |
| DELETE /api/transactions/:id (check) | SELECT id FROM transactions WHERE id = ? AND user_id = ? | Existing | Wasted query (issue #471) |
| DELETE /api/transactions/:id (delete) | DELETE FROM transactions WHERE id = ? AND user_id = ? | Existing | OK |
| GET /api/stats/summary (income) | SELECT COALESCE(SUM(amount), 0) as total FROM ... WHERE user_id=? AND amount >= 0 | UPDATED in PR#688 | Changed from >0 to >=0; frontend bypasses this endpoint (issue #721) |
| GET /api/stats/summary (expense) | SELECT COALESCE(SUM(amount), 0) as total FROM ... WHERE user_id=? AND amount < 0 | FIXED in PR#637 | No more type = expense dead code |
| GET /api/rules (list) | SELECT * FROM rules WHERE user_id = ? OR user_id IS NULL | Existing | SELECT * (issue #303); OR defeats index |
| POST /api/rules (INSERT) | INSERT INTO rules (user_id, name, description, condition, action, priority) | STILL BROKEN | Non-existent columns (issue #664) |
| PUT /api/rules/:id (UPDATE) | UPDATE rules SET ... | STILL BROKEN | Same schema drift |
| DELETE /api/rules/:id (check) | SELECT id FROM rules WHERE id = ? AND user_id = ? | Existing | Wasted query |

### Schema Design Review

| Table | Columns | Indexes | Issues |
|-------|---------|---------|--------|
| users | 7 | 1 (email) | notification_enabled/reminder_time dead (issue #563) |
| transactions | 11 | 5 | attachment_path dead (issue #563); parent_transaction_id dead (issue #422) |
| categories | 7 | 2 | OR-index issue (issue #419) |
| payment_methods | 5 | 1 | OK |
| rules | 9 | 2 | Schema drift UNFIXED (issue #664) |
| budgets | 6 | 2 | No API (issue #482) |
| subscriptions | 9 | 2 | No API (issue #482) |
| bills | 9 | 2 | No API (issue #482) |
| transaction_templates | 7 | 1 | No API (issue #482) |

### Open Database Issues: 54+ active (excluding deploy/CI issues)
