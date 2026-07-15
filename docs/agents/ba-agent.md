# BA Agent — Feature Research & Market Analysis

**Schedule:** Daily 07:00 WIB
**Model:** `research`
**Skills:** Jobs-to-be-done, Continuous Discovery, Obviously Awesome, Lean Analytics

## Activity Log

| Date | Issues Created | Summary |
|------|----------------|---------|
| 2026-07-08 | #513, #514, #515, #516, #517, #518, #519, #520 | Competitor analysis of Catatu/BukuKas/MoneyLover/Firefly III + 8 feature issues: Budget UI, Subscriptions/Bills, CSV Export, Search, Analytics Dashboard, Quick-Add, PWA/Offline, Navigation/Settings |
| 2026-07-09 | #634, #635, #636 | Market trend analysis: Split Bill (whitespace opportunity — no Indonesian expense tracker has native split feature), CSV Import (data portability to reduce switching cost), Privacy Lock (PIN/biometric — trust gap vs every major competitor) |
| 2026-07-10 | #726, #727, #728 | Competitive gap analysis of spendee/fynance/catatu + 3 feature issues: Smart Spending Alerts (proactive anomaly detection — the missing behavioral feedback loop), PWA Quick-Add Widget (reduce time-to-log from 15s to 3s), Tagging System (flexible organization beyond flat categories) |
| 2026-07-11 | #788, #789, #790, #791 | Deep-dive analysis of 29 open backlog issues + competitor parity audit (Money Lover, Spendee, Firefly III, Catat.ai, BukuKas): Custom Categories CRUD (foundational gap — categories read-only), Multi-Currency Support (whitespace — no Indonesian tracker handles USD/SGD well), Calendar View (feature parity with all major competitors), Net Worth Tracker (differentiator vs Catat.ai/DompetKu/BukuKas) |
| 2026-07-12 | #857, #858, #859, #860 | Financial planning features analysis: Savings Goals (core personal finance feature every competitor has), Recurring Income (income-side automation missing from current stack), Debt Tracker (whitespace in Indonesian market — no app handles paylater/credit card debt well), Financial Insights Engine (rule-based + AI-powered weekly insights to rival Catat.ai) |
| 2026-07-13 | #863, #864, #865 | Behavioral & data foundation analysis: Multi-Wallet/Accounts (data model change — wallet_id on every transaction, transfers, reconciliation), Weekly Spending Digest (push-based re-engagement via in-app + email, inspired by Catatu's Insight Mingguan), Round-Up Savings (proven behavioral economics mechanic — auto-save from every transaction) |
| 2026-07-14 | #923, #924, #925 | Visualization, UX, and data completeness analysis: Spending Heatmap (yearly GitHub-style grid to visualize daily spending intensity — inspired by Money Lover Premium), Quick-Add FAB (reducing time-to-log from 15s to 3s — #1 churn reason for expense trackers), Trend Charts (Canvas-based line/bar chart engine — feature parity with Spendee/Money Lover/Firefly III analytics) |
| 2026-07-15 | #977, #978, #979 | Production-critical gap analysis + whitespace identification: Password Reset (critical auth gap — no recovery path = permanent lockout), Transaction Attachments (wasted schema investment — `attachment_path` column exists but unused; CF Images integration), Monthly PDF Report (human-readable report vs raw CSV — browser print-to-PDF, category bars, last-month comparison) |

**Latest Run:** 2026-07-15 07:00 WIB — Created 3 feature issues (#977 Password Reset, #978 Transaction Attachments, #979 Monthly PDF Report). Key findings:

1. **🔐 Password Reset (#977)**: CRITICAL production blocker. Sribuu has NO password reset mechanism — a user who forgets their password is permanently locked out. Every competitor (Money Lover, Spendee, Catatu, Firefly III, BukuKas) has this. Proposed: `POST /api/auth/forgot-password` + `POST /api/auth/reset-password` with time-limited 32-byte tokens stored in a new `password_reset_tokens` table. Email via Resend API (fetch from Workers). Frontend: new `/forgot-password` and `/reset-password` pages. Security: constant-time token comparison, 15-min expiry, single-use, no user enumeration. **Medium** (2-3 days). **P0 priority** — production blocker, ships before any feature.

2. **📎 Transaction Attachments (#978)**: The `transactions` table already has an `attachment_path` column that was designed for photo receipts — but no upload endpoint or UI was ever built. This is a wasted schema investment. Proposed: upload endpoint (`POST /api/transactions/:id/attachments`) proxying to Cloudflare Images API (free tier: 20 images/month). Frontend: camera/file picker in transaction form, thumbnail preview, paperclip indicator in list, lightbox viewer. Phase 1: single photo per transaction (zero migration). **Easy-Medium** (2-3 days). **P2 priority** — closes a loop the schema was designed for; high delight value.

3. **📄 Monthly PDF Report (#979)**: CSV export exists but is raw data — useless for sharing or printing. Proposed: `GET /api/reports/monthly-data` aggregation endpoint (combines summary, category breakdown, last-month comparison, transaction list). Client-side report generation with print-optimized HTML/CSS → browser "Save as PDF". Pure CSS horizontal category bars. No external libraries. Unlike Money Lover (premium PDF) and Firefly III (built-in reports), Sribuu's approach requires zero server-side PDF engine. **Medium** (3-4 days). **P2 priority** — high shareability value, couples finance use case.

**Overall backlog health:** 42 open feature issues (+3 from this run). Backlog now covers:
- **Auth & security** (password reset) — 1 issue (+1: #977) — **NEW CATEGORY**
- **Data foundation** (multi-wallet, multi-currency, custom categories, tagging) — 5 issues
- **Data portability** (CSV export, CSV import, monthly PDF report) — 3 issues (+1: #979 PDF report)
- **Visualization & discovery** (calendar view, search, analytics dashboard, heatmap, trend charts) — 7 issues
- **Planning & goals** (budget UI, savings goals, debt tracker, subscription bills, recurring income) — 5 issues
- **Insights & behavior change** (financial health score, streak, smart alerts, weekly digest, net worth tracker, insights engine, round-up savings) — 7 issues
- **UX & platform** (PWA/offline, quick-add, navigation/settings, privacy lock, bottom nav, merchant analysis) — 7 issues
- **Attachments & media** (transaction attachments) — 1 issue (+1: #978) — **NEW CATEGORY**
- **Social** (split bill, shared budget) — 2 issues
- **Premium/monetization** (receipt scan, natural language input, budget recommendations) — 4 issues

**Priority sequencing recommendation:** Password Reset (#977) is the new **P0 — production blocker**. It must ship before any feature. No other item matters if users can't access their accounts. Quick-Add FAB (#924) remains the highest-impact feature (P1). Transaction Attachments (#978) is an independent scope that can ship any time — leverages existing schema, requires no data migration. Monthly PDF Report (#979) provides immediate shareability value and should follow core data features. Multi-Wallet (#863) remains the most important foundational data model change (P1-P2). Check CF Images API token availability before scoping #978.
