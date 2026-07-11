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

**Latest Run:** 2026-07-11 07:00 WIB — Created 4 feature issues analyzing foundational gaps vs competitors and whitespace differentiation opportunities. Key findings:
1. **Custom Categories CRUD (#788)**: Sribuu's `/api/categories` is read-only — users cannot add/edit/delete categories despite the schema fully supporting it. Every competitor offers this. Backend takes ~1 day since no migration is needed (columns already exist). Blocks meaningful budget management and analytics.
2. **Multi-Currency Support (#789)**: No Indonesian expense tracker handles foreign currencies well. Freelancers, remote workers, travelers, and cross-border shoppers are underserved. Manual rate entry (free) + optional auto-fetch (premium potential). 3-4 days, requires migration.
3. **Financial Calendar View (#790)**: Flat list is inadequate for monthly pattern discovery. Pure frontend implementation (no backend changes), 2-3 days. Replaces the current `prompt()`-based month picker with proper calendar navigation.
4. **Net Worth Tracker (#791)**: Sribuu tracks transactions but cannot answer "am I getting wealthier?" Monthly balance history from existing data + Canvas line chart. Differentiator vs Catat.ai, DompetKu, BukuKas. No migration needed.
