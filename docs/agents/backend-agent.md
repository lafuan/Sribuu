# Backend Agent — Hono/D1/TS Code & Architecture Audit

**Schedule:** Daily 10:00, 16:00, 22:00 WIB
**Model:** `ocg`
**Skills:** Clean Code, Clean Architecture, Refactoring Patterns

## Activity Log

| Date | Issues Created | PRs Merged | Key Findings |
|------|----------------|------------|--------------|
| 2026-07-08 (10:00) | [#528](https://github.com/lafuan/Sribuu/issues/528) [#529](https://github.com/lafuan/Sribuu/issues/529) [#530](https://github.com/lafuan/Sribuu/issues/530) [#531](https://github.com/lafuan/Sribuu/issues/531) [#532](https://github.com/lafuan/Sribuu/issues/532) [#533](https://github.com/lafuan/Sribuu/issues/533) [#534](https://github.com/lafuan/Sribuu/issues/534) [#535](https://github.com/lafuan/Sribuu/issues/535) [#536](https://github.com/lafuan/Sribuu/issues/536) [#537](https://github.com/lafuan/Sribuu/issues/537) [#538](https://github.com/lafuan/Sribuu/issues/538) [#539](https://github.com/lafuan/Sribuu/issues/539) [#540](https://github.com/lafuan/Sribuu/issues/540) [#541](https://github.com/lafuan/Sribuu/issues/541) | — | Amount sign convention broken; Dynamic SQL UPDATE column injection; No amount validation; Rules schema mismatch; Transaction columns mismatch; strftime() prevents index use; Monolithic routing; any types on middleware; D1 race conditions |
| 2026-07-08 (16:00) | [#579](https://github.com/lafuan/Sribuu/issues/579) [#580](https://github.com/lafuan/Sribuu/issues/580) [#581](https://github.com/lafuan/Sribuu/issues/581) [#582](https://github.com/lafuan/Sribuu/issues/582) [#583](https://github.com/lafuan/Sribuu/issues/583) [#584](https://github.com/lafuan/Sribuu/issues/584) [#585](https://github.com/lafuan/Sribuu/issues/585) | — | Email normalization missing (case-sensitive login causes lockout); No input size limits (Workers memory risk); updated_at never updated in UPDATEs; Health endpoint lacks DB check; TypeScript types subverted by 15+ `as any` casts; No CI pipeline; No request correlation ID |
| 2026-07-08 (22:00) | [#611](https://github.com/lafuan/Sribuu/issues/611) [#612](https://github.com/lafuan/Sribuu/issues/612) [#613](https://github.com/lafuan/Sribuu/issues/613) [#614](https://github.com/lafuan/Sribuu/issues/614) [#615](https://github.com/lafuan/Sribuu/issues/615) [#616](https://github.com/lafuan/Sribuu/issues/616) [#617](https://github.com/lafuan/Sribuu/issues/617) | — | parseInt NaN injection (5 ID params unvalidated); Unused dead imports (base64urlEncode/Decode); Dead userName context var; Silent category_id defaulting to magic number 1; Transaction INSERT uses nonexistent columns (type/description); Malformed JSON returns 500 instead of 400; SELECT * FROM rules fetches unnecessary JSON blobs |

**Latest Run:** 2026-07-08 22:00 WIB

## Backend Audit Report — 2026-07-08 (22:00 WIB)

### Code Quality Score: 4/10

The backend is a functional prototype showing signs of rapid iteration. It works end-to-end for basic flows but has critical issues in three areas:

1. **Schema mismatch** — The migration defines columns (`notes`, no `type` column) but the API code references `description` and `type` columns. The rules table has a complete mismatch (`match_keywords`/`category_id` vs `condition`/`action`).

2. **Production integrity** — No amount validation (NaN/Infinity accepted), sign convention between backend and frontend is inverted, dynamic SQL column injection possible via UPDATE endpoints, email case-sensitivity causes login failures.

3. **Architecture** — Single monolithic `_worker.ts` (410 lines), no D1 transactions for atomicity, 15+ `as any` casts bypassing strict TypeScript, strftime() killing index usage, no CI pipeline.

### Issues Created This Run (2026-07-08 16:00 WIB)

| # | Priority | Title | File:Line |
|---|----------|-------|-----------|
| [#579](https://github.com/lafuan/Sribuu/issues/579) | 🟡 MEDIUM | Email normalization missing — case-sensitive login causes account lockout | `_worker.ts:66-68, 95-100` |
| [#580](https://github.com/lafuan/Sribuu/issues/580) | 🟡 MEDIUM | No input size limits on request body — Workers memory exhaustion risk | `_worker.ts:204, 249, 350, 369` |
| [#581](https://github.com/lafuan/Sribuu/issues/581) | 🟡 MEDIUM | updated_at column never updated — schema promises audit trail but all UPDATEs skip it | `_worker.ts:267, 382` |
| [#582](https://github.com/lafuan/Sribuu/issues/582) | 🟢 LOW | Health endpoint does not verify D1 connectivity — false positives during DB outages | `_worker.ts:61` |
| [#583](https://github.com/lafuan/Sribuu/issues/583) | 🟡 MEDIUM | TypeScript types not enforced — `as any`/`as number` casts subvert strict mode | `_worker.ts:100, 177, 255, 371` etc. |
| [#584](https://github.com/lafuan/Sribuu/issues/584) | 🟢 LOW | No CI pipeline or pre-commit hooks — TypeScript errors reach production | `package.json:7-14`, `build.py:54` |
| [#585](https://github.com/lafuan/Sribuu/issues/585) | 🟢 LOW | No request correlation ID or structured logging | `_worker.ts:87-401` (all catch blocks) |

### Issues Created This Run (2026-07-08 22:00 WIB)

| # | Priority | Title | File:Line |
|---|----------|-------|-----------|
| [#611](https://github.com/lafuan/Sribuu/issues/611) | 🟡 MEDIUM | No input validation on URL path parameter IDs — parseInt silently returns NaN for non-numeric values | `_worker.ts:229, 248, 282, 366, 395` |
| [#612](https://github.com/lafuan/Sribuu/issues/612) | 🟡 MEDIUM | Unused imports in _worker.ts — base64urlEncode and base64urlDecode imported but never called | `_worker.ts:4` |
| [#613](https://github.com/lafuan/Sribuu/issues/613) | 🟡 MEDIUM | userName variable set on context but never read — dead state in every authenticated request | `_worker.ts:24, 32` |
| [#614](https://github.com/lafuan/Sribuu/issues/614) | 🟡 MEDIUM | category_id default value of 1 silently ignores validation — missing categories produce misleading transaction data | `_worker.ts:209` |
| [#615](https://github.com/lafuan/Sribuu/issues/615) | 🔴 HIGH | Transaction INSERT uses non-existent columns (type, description) — production crash risk due to schema mismatch with migration | `_worker.ts:213`, `migrations/0001_initial.sql:44-56` |
| [#616](https://github.com/lafuan/Sribuu/issues/616) | 🟡 MEDIUM | Malformed JSON in request body returns HTTP 500 instead of 400 — unhelpful error response from JSON parse failures | `_worker.ts:66, 95, 204, 249, 350, 369` |
| [#617](https://github.com/lafuan/Sribuu/issues/617) | 🟢 LOW | SELECT * FROM rules fetches large JSON blobs (condition, action) that may not be needed for list view | `_worker.ts:337-340` |
