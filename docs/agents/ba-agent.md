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

**Latest Run:** 2026-07-12 07:00 WIB — Created 4 feature issues shifting focus from "tracking infrastructure" to "financial planning & insights." Key findings:

1. **Savings Goals (#857)**: Sribuu tracks past spending but cannot help users plan future savings. Every major competitor (Money Lover, Spendee, YNAB, Firefly III) offers goal-based saving with progress visualization. 2-3 days implementation with new `savings_goals` table + CRUD + frontend goal cards + tab navigation. Option A (manual tracking, no transaction migration) recommended for v1.

2. **Recurring Income (#858)**: Income-side automation is the mirror of recurring bills (#514). Users with salary, freelance retainers, or rental income manually re-enter the same recurring transaction. Without this, Sribuu only tracks half the financial picture. Implementation reuses patterns from the bills feature: `recurring_income` table + CRUD + auto-generation. No local competitor handles this well — whitespace opportunity.

3. **Debt Tracker & Payoff Planner (#859)**: Expands on backlog #64 with a concrete spec. Many Indonesian users juggle multiple debt sources (credit cards, GoPay Later, SPayLater, KTA, family loans). No Indonesian expense tracker handles debt with payoff visualization and strategy recommendations (snowball vs avalanche). New `debts` table + payment recording + progress bars + payoff calculator. 2-3 days.

4. **Financial Insights Engine (#860)**: Rule-based weekly/monthly insights from existing transaction data — no external API needed. Compares spending across periods, surfaces anomalies ("You spent 3x more on Belanja this week"), calculates savings rate, tracks goal progress. Catat.ai differentiates on "AI insight mingguan" — Sribuu can match with pure SQL (free tier) and add AI-powered narrative (premium upsell) via Workers AI later. Phase 1 is 1-2 days.

**Overall backlog health:** 33 open feature issues as of this run. The backlog now covers all major feature categories:
- **Tracking infrastructure** (categories CRUD, multi-currency, tagging) — 3 issues
- **Data portability** (CSV export, CSV import) — 2 issues
- **Visualization & discovery** (calendar view, search, analytics dashboard, heatmap, trend charts) — 5 issues
- **Planning & goals** (budget UI, savings goals, debt tracker, subscription bills, recurring income) — 5 issues
- **Insights & behavior change** (financial health score, streak, smart alerts, weekly digest, net worth tracker, insights engine) — 6 issues
- **UX & platform** (PWA/offline, quick-add, navigation/settings, privacy lock, bottom nav, merchant analysis) — 6 issues
- **Social** (split bill, shared budget) — 2 issues
- **Premium/monetization** (receipt scan, natural language input, budget recommendations) — 4 issues

**Next priority recommendation:** With 8 "tracking & visualization" issues and 6 "insights & behavior change" issues, the next logical focus is implementing the simplest wins (Calendar View #790, Insights Engine Phase 1 #860) to give users immediate value before tackling the larger planning features.
