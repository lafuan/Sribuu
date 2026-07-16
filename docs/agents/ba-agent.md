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

**Latest Run:** 2026-07-16 07:00 WIB — Created 3 feature issues (#983 Budget vs Actual Dashboard, #984 Recurring Transaction Engine, #985 First-Time User Onboarding Flow). Key findings:

1. **📊 Budget vs Actual Dashboard (#983)**: The `budgets` table exists in the DB schema but has zero API endpoints or UI — users can't see how they're tracking against their budgets. Proposed: `GET /api/budgets/with-spending` aggregation endpoint joining budgets with SUM of transactions per category, per-category progress bars with color coding (green < 60%, yellow 60-85%, red > 85%), and a dashboard budget summary card. No migration needed. **Medium** (3-5 days). **P1 priority** — closes the core loop of personal finance management; every competitor has this.

2. **🔄 Recurring Transaction Engine (#984)**: The `subscriptions`, `bills`, and `transaction_templates` tables (migration 0001) are completely unused — three tables with zero API surface. This is the largest schema ROI opportunity in the codebase. Proposed: Phase 1 — CRUD endpoints for all three tables. Phase 2 — Daily CRON trigger (Cloudflare Cron Triggers) that auto-creates transactions from subscriptions whose `next_payment_date <= today`. Phase 3 — Frontend UI with subscriptions/bills/templates tabs and upcoming-payments dashboard card. **Hard** (5-7 days across all phases). **P1 priority** — unlocks the largest pre-invested schema value; users stop manually re-entering recurring expenses.

3. **🚀 First-Time User Onboarding Flow (#985)**: Sribuu has zero onboarding — new users land on a blank dashboard with no guidance. Competitors (Finku, Money Lover, Spendee) guide the first transaction within 30 seconds. Proposed: Phase 1 — guided first transaction modal (3-step overlay, < 30 seconds). Phase 2 — initial setup wizard (budget, categories, payment methods, reminder time). Phase 3 — progressive tips for first 7 days. Pure frontend, zero backend needed for Phase 1. **Medium** (3-5 days). **P1 priority** — activation directly determines retention; highest-ROI investment for Stickiness stage.

**Overall backlog health:** 45 open feature issues (+3 from this run). Backlog now covers:
- **Auth & security** (password reset) — 1 issue
- **Data foundation** (multi-wallet, multi-currency, custom categories, tagging) — 5 issues
- **Data portability** (CSV export, CSV import, monthly PDF report) — 3 issues
- **Visualization & discovery** (calendar view, search, analytics dashboard, heatmap, trend charts) — 7 issues
- **Planning & goals** (budget UI/actual, savings goals, debt tracker, subscription bills, recurring income, recurring engine) — 7 issues (+2: #983 budget dashboard, #984 recurring engine)
- **Insights & behavior change** (financial health score, streak, smart alerts, weekly digest, net worth tracker, insights engine, round-up savings) — 7 issues
- **UX & platform** (PWA/offline, quick-add, navigation/settings, privacy lock, bottom nav, merchant analysis, onboarding) — 8 issues (+1: #985 onboarding)
- **Attachments & media** (transaction attachments) — 1 issue
- **Social** (split bill, shared budget) — 2 issues
- **Premium/monetization** (receipt scan, natural language input, budget recommendations) — 4 issues

**Priority sequencing recommendation:** Password Reset (#977) remains **P0 — production blocker**; ship before anything else. After that, Budget vs Actual Dashboard (#983) unlocks the most pre-invested schema value. Recurring Transaction Engine (#984) is the largest codebase ROI opportunity but takes longer — start Phase 1 (CRUD endpoints) in parallel. First-Time User Onboarding (#985) is the highest-leverage activation intervention and should ship alongside Quick-Add FAB (#924). The big theme this run: **schema ROI** — Sribuu has $10K+ worth of unserved database schema (budgets, subscriptions, bills, templates) that needs API + UI investment to unlock.
