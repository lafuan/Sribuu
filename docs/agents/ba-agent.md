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

**Latest Run:** 2026-07-13 07:00 WIB — Created 3 feature issues (#863 Multi-Wallet, #864 Weekly Digest, #865 Round-Up Savings). Key findings:

1. **Multi-Wallet / Multiple Accounts (#863)**: Sribuu lacks the most fundamental data model feature — assigning transactions to wallets/accounts. Indonesian users have 5+ money containers (cash, GoPay, OVO, BCA, Mandiri). Money Lover, Spendee, Firefly III, and even the original Sribuu all support this. Implementation requires: new `wallets` table, ALTER transactions to add `wallet_id` + `transfer_to_wallet_id`, computed balance SQL, transfer endpoint, and frontend wallet selector/cards. **Medium-Hard** (4-6 days). **P1 priority** — foundational data model change that affects every future feature.

2. **Weekly Spending Digest (#864)**: Inspired by Catatu's most-praised feature "Insight Mingguan." Phase 1: in-app digest card displayed on Monday with category breakdown, week-over-week comparison, budget alerts, financial tips — all computed from existing SQL. Phase 2: email digest via Cloudflare MailChannels integration, scheduled via Workers Cron. No external APIs needed. **Medium** (4-6 days full). **P2 priority** — builds on Budget UI (#513).

3. **Round-Up Savings (#865)**: Behavioral economics mechanic used by Acorns ($37B AUM) and Qapital. Auto-saves small amounts by rounding each transaction to nearest Rp1,000 and logging the difference. Two new tables (`round_up_rules`, `round_up_log`) + auto-trigger on transaction create + interface to contribute to Savings Goals. **Easy-Medium** (2-3 days). **P3 priority** — depends on Savings Goals (#857).

**Overall backlog health:** 36 open feature issues (+3 from this run). Backlog now covers:
- **Data foundation** (multi-wallet, multi-currency, custom categories, tagging) — 5 issues
- **Data portability** (CSV export, CSV import) — 2 issues
- **Visualization & discovery** (calendar view, search, analytics dashboard, heatmap, trend charts) — 5 issues
- **Planning & goals** (budget UI, savings goals, debt tracker, subscription bills, recurring income) — 5 issues
- **Insights & behavior change** (financial health score, streak, smart alerts, weekly digest, net worth tracker, insights engine, round-up savings) — 7 issues
- **UX & platform** (PWA/offline, quick-add, navigation/settings, privacy lock, bottom nav, merchant analysis) — 6 issues
- **Social** (split bill, shared budget) — 2 issues
- **Premium/monetization** (receipt scan, natural language input, budget recommendations) — 4 issues

**Priority sequencing recommendation:** Multi-Wallet (#863) is the single highest-impact foundational change. Build it as P1 before anything else — it changes the transaction data model and every feature built after it should be wallet-aware. Weekly Digest (#864) should ship after Budget UI (#513) since digest shows budget progress. Round-Up Savings (#865) is a delight feature that requires Savings Goals (#857) first.
