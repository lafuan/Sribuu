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
| 2026-07-09 (10:00) | [#644](https://github.com/lafuan/Sribuu/issues/644) [#645](https://github.com/lafuan/Sribuu/issues/645) [#646](https://github.com/lafuan/Sribuu/issues/646) [#647](https://github.com/lafuan/Sribuu/issues/647) [#648](https://github.com/lafuan/Sribuu/issues/648) [#649](https://github.com/lafuan/Sribuu/issues/649) [#650](https://github.com/lafuan/Sribuu/issues/650) [#651](https://github.com/lafuan/Sribuu/issues/651) [#652](https://github.com/lafuan/Sribuu/issues/652) [#653](https://github.com/lafuan/Sribuu/issues/653) | — | Wildcard CORS allows cross-origin exfiltration; No rate limiting on auth endpoints (brute force + enumeration); Missing security headers (clickjacking/MIME/CSP/HSTS); JWT tokens cached without Cache-Control: no-store; Unbounded offset param wastes D1 quota; Test coverage gaps (no UPDATE/DELETE/Rules tests); Build script skips type-checking; Static files lack cache headers; Float truncation in amount field; Dashboard computes stats client-side wasting D1 reads |

**Latest Run:** 2026-07-09 10:00 WIB

## Backend Audit Report — 2026-07-09 (10:00 WIB)

### Code Quality Score: 4/10

The backend is a functional prototype showing signs of rapid iteration. It works end-to-end for basic flows but has critical issues in three areas:

1. **Security gaps** — Wildcard CORS on finance API allows cross-origin data exfiltration; no rate limiting on auth endpoints enables brute force and account enumeration; missing security headers (CSP, HSTS, X-Frame-Options) expose users to clickjacking and XSS; JWT tokens from login/register responses have no cache-control headers.

2. **Production integrity** — No amount validation (NaN/Infinity accepted, float truncation silent), dynamic SQL column injection possible via UPDATE endpoints, email case-sensitivity causes login failures, unbounded offset param wastes D1 read quota.

3. **Architecture & testing** — Single monolithic `_worker.ts` (410 lines), no D1 transactions for atomicity, 15+ `as any` casts bypassing strict TypeScript, strftime() killing index usage, no CI pipeline, significant test coverage gaps (no tests for UPDATE/DELETE/Rules CRUD), build script skips type-checking.

### Issues Created This Run (2026-07-09 10:00 WIB)

| # | Priority | Title | File:Line |
|---|----------|-------|-----------|
| [#644](https://github.com/lafuan/Sribuu/issues/644) | 🔴 HIGH | Wildcard CORS allows cross-origin data exfiltration on finance API | `_worker.ts:34` |
| [#645](https://github.com/lafuan/Sribuu/issues/645) | 🔴 HIGH | No rate limiting on auth endpoints — brute force and account enumeration | `_worker.ts:64-117` |
| [#646](https://github.com/lafuan/Sribuu/issues/646) | 🟡 MEDIUM | Missing security headers (clickjacking, MIME sniffing, CSP, HSTS) | `_worker.ts:34` |
| [#647](https://github.com/lafuan/Sribuu/issues/647) | 🟡 MEDIUM | JWT tokens returned without Cache-Control: no-store — token caching risk | `_worker.ts:85, 113` |
| [#648](https://github.com/lafuan/Sribuu/issues/648) | 🟡 MEDIUM | Unbounded offset query param on transactions — D1 read quota exhaustion | `_worker.ts:173-174` |
| [#649](https://github.com/lafuan/Sribuu/issues/649) | 🟡 MEDIUM | Test coverage gaps — no tests for UPDATE, DELETE, Rules CRUD, or error edges | `tests/api.test.ts` |
| [#650](https://github.com/lafuan/Sribuu/issues/650) | 🟢 LOW | Build script skips TypeScript type-checking — type errors reach production | `build.py:54` |
| [#651](https://github.com/lafuan/Sribuu/issues/651) | 🟢 LOW | Static file responses missing cache headers (ETag, Cache-Control) | `_worker.ts:50-58` |
| [#652](https://github.com/lafuan/Sribuu/issues/652) | 🟢 LOW | No validation that amount is an integer — float truncation causes data loss | `_worker.ts:204-206` |
| [#653](https://github.com/lafuan/Sribuu/issues/653) | 🟢 LOW | Frontend computes monthly stats client-side instead of using stats endpoint — 2x D1 reads | `app.html loadMonthlyStats()` |
