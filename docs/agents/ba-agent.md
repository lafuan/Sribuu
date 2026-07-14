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

**Latest Run:** 2026-07-14 07:00 WIB — Created 3 feature issues (#923 Spending Heatmap, #924 Quick-Add FAB, #925 Trend Charts). Key findings:

1. **🔥 Spending Heatmap (#923)**: GitHub-style contribution grid showing daily spending intensity across the year. Color-coded cells (green = irit, red = boros) enable instant pattern recognition — weekends, spending bursts, and saving streaks. Pure frontend (Canvas/DOM), no backend changes needed. Inspired by Money Lover Premium's heatmap. **Medium** (2-3 days). **P3 priority** — fun, engaging visualization zero-risk feature.

2. **⏱️ Quick-Add Floating Action Button (#924)**: Persistent FAB on every page that opens a minimal quick-add modal (amount + submit in 3 seconds). Smart defaults (last-used category, today's date, remembered payment method). Solves the #1 reason users quit expense tracking: logging friction. Phase 2: long-press speed dial (add expense, add income, transfer). Phase 3: natural language input ("kopi 25rb"). **Easy-Medium** (1-2 days for FAB + quick modal). **P1 priority** — highest-impact, lowest-effort feature. Ships in a day, benefits every user.

3. **📊 Trend Charts (#925)**: Canvas-based line and bar chart engine with zero external dependencies. Five views: Monthly Spending Trend (income/expense lines), Category Breakdown (bar chart), Category Trend (multi-line per category), Cumulative Spending (area chart), Income vs Expense Waterfall. New backend endpoint (`GET /api/stats/trends`) with monthly SQL aggregation. **Medium** (3-4 days). **P2 priority** — visual insight is irreplaceable; matches Spendee/Money Lover/Firefly III analytics.

**Overall backlog health:** 39 open feature issues (+3 from this run). Backlog now covers:
- **Data foundation** (multi-wallet, multi-currency, custom categories, tagging) — 5 issues
- **Data portability** (CSV export, CSV import) — 2 issues
- **Visualization & discovery** (calendar view, search, analytics dashboard, heatmap, trend charts) — 7 issues (+2: #923 heatmap, #925 trend charts)
- **Planning & goals** (budget UI, savings goals, debt tracker, subscription bills, recurring income) — 5 issues
- **Insights & behavior change** (financial health score, streak, smart alerts, weekly digest, net worth tracker, insights engine, round-up savings) — 7 issues
- **UX & platform** (PWA/offline, quick-add, navigation/settings, privacy lock, bottom nav, merchant analysis) — 7 issues (+1: #924 quick-add FAB)
- **Social** (split bill, shared budget) — 2 issues
- **Premium/monetization** (receipt scan, natural language input, budget recommendations) — 4 issues

**Priority sequencing recommendation:** Quick-Add FAB (#924) is the new highest-impact, lowest-effort item — ships in a day, benefits every user immediately, and solves the #1 churn reason (logging friction). Multi-Wallet (#863) remains the most important foundational data model change, but Quick-Add can be built independently in parallel. Trend Charts (#925) should ship after core data features are stable, as visualization is most valuable when the underlying data model is complete. Spending Heatmap (#923) is a zero-risk, fun visualization that can be deployed anytime since it needs no backend changes.
