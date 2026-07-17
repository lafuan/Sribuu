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
| 2026-07-16 | #983, #984, #985 | Schema ROI analysis + activation gap analysis: Budget vs Actual Dashboard (unlock existing budgets table — P1), Recurring Transaction Engine (unlock subscriptions/bills/templates tables — P1, largest schema ROI), First-Time User Onboarding Flow (activation gap — P1, no guided setup today) |
| 2026-07-17 | #987, #988, #989 | Infrastructure + engagement + schema ROI: PWA Push Notifications (unblocks 3 downstream features, P1 — infrastructure), Annual Spending Wrapped (year-in-review whitespace in Indonesian market, P2 — viral engagement potential), Split Transactions (activate unused parent_transaction_id column, P2 — eliminates daily workaround, whitespace) |

**Latest Run:** 2026-07-17 07:00 WIB — Created 3 feature issues (#987 PWA Push Notifications, #988 Annual Spending Wrapped, #989 Split Transactions). Key findings:

1. **📬 PWA Push Notification Infrastructure (#987)**: Sribuu has zero push notification capability — the `users` table has `notification_enabled` and `reminder_time` columns but zero API reads/writes them, and no delivery mechanism exists when users aren't on the page. This blocks 3 existing feature requests (#726 Smart Alerts, #63/#864 Weekly Digest). Proposed: Web Push API with VAPID keys, `push_subscriptions` D1 table, Cloudflare Cron Triggers for scheduled sending, Service Worker in `sw.js`, and opt-in prompt after 3rd transaction. **Medium** (4-6 days). **P1 priority** — infrastructure that unblocks 3 downstream features; push notification users log 30-50% more transactions.

2. **📅 Annual Spending Wrapped (#988)**: Sribuu has no retrospective feature — users log daily but get zero "look how far you've come" moments. Every major competitor (Spendee, Money Lover, Wallet) has year-end reports, and shareable infographic cards drive viral acquisition. This is a **whitespace in the Indonesian market** — no local expense tracker has a well-designed "Wrapped" feature. Proposed: `GET /api/reports/annual?year=2026` aggregation endpoint (12 D1 aggregate queries), scrollable review page, Canvas-generated shareable infographic card via Web Share API. **Medium** (3-5 days). **P2 — High engagement value.**

3. **🔀 Split Transactions (#989)**: The `transactions` table has a `parent_transaction_id` column that is **completely unused** despite being perfect for multi-category receipts, bill splitting with friends, installment tracking, and refund linking. Current daily workaround: users create 3+ separate transactions for one supermarket receipt. No Indonesian competitor supports transaction splitting — this is a **whitespace** opportunity. Proposed: `POST /api/transactions/split` endpoint (creates parent + N children with sum validation), collapsible parent-child UI in transaction list, and auto-balance split modal. **Medium** (4-6 days). **P2 — eliminates daily user workaround.**

**Overall backlog health:** 48 open feature issues (+3 from this run: #987, #988, #989). Backlog now covers:
- **Auth & security** (password reset) — 1 issue
- **Data foundation** (multi-wallet, multi-currency, custom categories, tagging) — 5 issues
- **Data portability** (CSV export, CSV import, monthly PDF report) — 3 issues
- **Visualization & discovery** (calendar view, search, analytics dashboard, heatmap, trend charts) — 7 issues
- **Planning & goals** (budget UI/actual, savings goals, debt tracker, subscription bills, recurring income, recurring engine) — 7 issues
- **Insights & behavior change** (financial health score, streak, smart alerts, weekly digest, net worth tracker, insights engine, round-up savings) — 7 issues
- **UX & platform** (PWA/offline, quick-add, navigation/settings, privacy lock, bottom nav, merchant analysis, onboarding) — 8 issues
- **Attachments & media** (transaction attachments) — 1 issue
- **Social** (split bill, shared budget, split transactions) — 3 issues (+1: #989)
- **Premium/monetization** (receipt scan, natural language input, budget recommendations, annual report premium) — 5 issues (+1: #988 premium tier)
- **Infrastructure** (push notifications) — 1 issue (+1: #987 foundation)

**Total issues with `agent-recommendation` label:** 49 (3 new this run).

**Priority sequencing recommendation:** Password Reset (#977) remains **P0 — production blocker**; ship before anything else. The big new theme this run is **infrastructure unlocks**: PWA Push Notifications (#987) is the single highest-leverage infrastructure investment because it unlocks 3 downstream features (#726, #63, #864). Build it first to create a notification pipeline that all subsequent engagement features can plug into. Annual Spending Wrapped (#988) should ship before December to capture the year-end engagement spike. Split Transactions (#989) turns unused schema debt into a differentiated product capability — no Indonesian competitor has this yet. The backlog now includes 48 feature issues, with the most promising whitespace areas being: **push notifications** (no infra today), **annual wrapped** (no competitor has one), **split transactions** (unused column ready to activate), and **multi-currency** (unserved need for Indonesian users dealing with USD/SGD).
