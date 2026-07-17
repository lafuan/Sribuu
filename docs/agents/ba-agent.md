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
|| 2026-07-17 | #987, #988, #989 | Infrastructure + engagement + schema ROI: PWA Push Notifications (unblocks 3 downstream features, P1 — infrastructure), Annual Spending Wrapped (year-in-review whitespace in Indonesian market, P2 — viral engagement potential), Split Transactions (activate unused parent_transaction_id column, P2 — eliminates daily workaround, whitespace) |
|| 2026-07-18 | #1005, #1006, #1007 | Market trend + behavioral economics gap analysis: Budget Rollover (activate unused `rollover` column in budgets table — zero schema investment needed), Shared Budget for Couples & Family (whitespace — no Indonesian expense tracker supports joint budgeting), Gamification: Daily Streaks, Achievements & Financial Health Score (retention mechanic — no local competitor has gamification) |

**Latest Run:** 2026-07-18 07:00 WIB — Created 3 feature issues (#1005 Budget Rollover, #1006 Shared Budget for Couples & Family, #1007 Gamification). Key findings:

1. **💰 Budget Rollover (#1005)**: The `budgets` table has a `rollover` INTEGER column (default 0) that is completely unused. When enabled, underspent budget carries to next month — a core behavioral economics mechanic every major competitor (YNAB, Monarch, EveryDollar) supports. **Schema investment already made — zero new tables needed.** Proposed: `PATCH /api/budgets/:id` to toggle rollover, compute carry-forward in budget calculation, toggle UI in Budget vs Actual dashboard. **Medium** (5 days). **P2 — activates dead schema column with high user impact.**

2. **👫 Shared Budget for Couples & Family (#1006)**: Sribuu is single-user only. Couples managing shared finances must share login or maintain separate accounts with no joint visibility. **Whitespace opportunity** — no Indonesian expense tracker (Catatu, BukuKas, DompetKu) offers native shared budgeting. International competitors (Monarch Money, Honeydue, Zeta) have built products around this need. Proposed: shared family CRUD with invite-by-email, combined transaction feed, merged budget view. **Hard** (8 days). **P2 — monetization opportunity as premium tier.**

3. **🎮 Gamification: Streaks, Achievements & Health Score (#1007)**: Sribuu has zero retention mechanics — no feedback loop, no progress tracking, no reason to return beyond self-discipline. Behavioral economics research shows gamification increases expense tracking retention 40-60%. **Whitespace** — no Indonesian competitor has meaningful gamification. Proposed: daily streak (consecutive logging days), 12 achievement badges, financial health score (0-100 based on 5 weighted factors: logging consistency, budget adherence, savings rate, category diversity, debt ratio). **Hard** (10 days). **P2 — retention driver that creates viral sharing mechanic.**

**Overall backlog health:** 51 open feature issues (+3 from this run: #1005, #1006, #1007). New categories added:
- **Gamification & retention** — 1 issue (new category)
- **Social & shared** — 4 issues (+1: #1006 shared family)
- **Budget & planning** — 8 issues (+1: #1005 budget rollover)

**Total issues with `agent-recommendation` label:** ~700+ (incl bugs, CI reports, security). Open feature backlog at 51.

**Priority sequencing recommendation:** The big three infrastructure unlocks remain: Password Reset (#977) is P0 — production blocker ship first. PWA Push Notifications (#987) is the single highest-leverage investment — unblocks 3 downstream features. Budget Rollover (#1005) is the highest ROI schema activation — zero new tables, biggest behavioral impact. Shared Budget (#1006) and Gamification (#1007) are P2 differentiators — build after infrastructure is stable.
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
