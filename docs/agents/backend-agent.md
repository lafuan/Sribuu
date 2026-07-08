# Backend Agent — Hono/D1/TS Code & Architecture Audit

**Schedule:** Daily 10:00, 16:00, 22:00 WIB
**Model:** `ocg`
**Skills:** Clean Code, Clean Architecture, Refactoring Patterns

## Activity Log

| Date | Issues Created | PRs Merged | Key Findings |
|------|----------------|------------|--------------|
| 2026-07-08 | [#528](https://github.com/lafuan/Sribuu/issues/528) [#529](https://github.com/lafuan/Sribuu/issues/529) [#530](https://github.com/lafuan/Sribuu/issues/530) [#531](https://github.com/lafuan/Sribuu/issues/531) [#532](https://github.com/lafuan/Sribuu/issues/532) [#533](https://github.com/lafuan/Sribuu/issues/533) [#534](https://github.com/lafuan/Sribuu/issues/534) [#535](https://github.com/lafuan/Sribuu/issues/535) [#536](https://github.com/lafuan/Sribuu/issues/536) [#537](https://github.com/lafuan/Sribuu/issues/537) [#538](https://github.com/lafuan/Sribuu/issues/538) [#539](https://github.com/lafuan/Sribuu/issues/539) [#540](https://github.com/lafuan/Sribuu/issues/540) [#541](https://github.com/lafuan/Sribuu/issues/541) | — | Amount sign convention broken (all expenses display as income); Dynamic SQL UPDATE column injection; No amount validation (NaN/Infinity); Rules schema mismatch; Transaction description/type columns mismatch; strftime() prevents index use; Monolithic routing; any types on middleware; D1 race conditions |

**Latest Run:** 2026-07-08 10:00 WIB

## Backend Audit Report — 2026-07-08

### Code Quality Score: 4/10

The backend is a functional prototype showing signs of rapid iteration. It works end-to-end for basic flows but has critical issues in three areas:

1. **Schema mismatch** — The migration defines columns (`notes`, no `type` column) but the API code references `description` and `type` columns. The rules table has a complete mismatch (`match_keywords`/`category_id` vs `condition`/`action`).

2. **Production integrity** — No amount validation (NaN/Infinity accepted), sign convention between backend and frontend is inverted, dynamic SQL column injection possible via UPDATE endpoints.

3. **Architecture** — Single monolithic `_worker.ts` (410 lines), no D1 transactions for atomicity, 12+ `as any` casts bypassing strict TypeScript, strftime() killing index usage.

### Priority Issues (should fix before production)

| Priority | Issue | File:Line |
|----------|-------|-----------|
| 🔴 CRITICAL | Sign convention broken — all expenses display as income | `_worker.ts:214`, `src/static.ts:226` |
| 🔴 CRITICAL | Amount accepted without type/range validation | `_worker.ts:205-214` |
| 🔴 HIGH | Dynamic SQL column injection in UPDATE queries | `_worker.ts:254-267`, `_worker.ts:370-382` |
| 🔴 HIGH | Rules schema mismatch — API writes non-existent columns | `_worker.ts:352-354` vs migration |
| 🔴 HIGH | Transactions schema mismatch — `type`/`description` don't exist | `_worker.ts:213` vs migration |
| 🔴 HIGH | strftime() prevents index usage — full table scan | `_worker.ts:180-181`, `_worker.ts:310-311` |
| 🔴 HIGH | Monolithic routing — violates SRP | `_worker.ts:1-410` |
| 🟡 MEDIUM | Race condition: INSERT+SELECT not atomic | `_worker.ts:212-218` |
| 🟡 MEDIUM | Any types on middleware and 12+ casts | `_worker.ts:16` |
| 🟡 MEDIUM | No JWT key rotation support | `src/utils.ts:74-93` |
| 🟡 MEDIUM | Stats summary runs duplicated queries | `_worker.ts:304-320` |
| 🟡 MEDIUM | Payment methods have no user ownership | `_worker.ts:146-158` |
| 🟢 LOW | Env interface incomplete | `_worker.ts:7-10` |
| 🟢 LOW | Unused imports, bare console.error | `_worker.ts:4` |
