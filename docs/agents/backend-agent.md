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
| 2026-07-09 (16:00) | [#666](https://github.com/lafuan/Sribuu/issues/666) [#667](https://github.com/lafuan/Sribuu/issues/667) [#668](https://github.com/lafuan/Sribuu/issues/668) [#669](https://github.com/lafuan/Sribuu/issues/669) [#670](https://github.com/lafuan/Sribuu/issues/670) [#671](https://github.com/lafuan/Sribuu/issues/671) [#672](https://github.com/lafuan/Sribuu/issues/672) [#673](https://github.com/lafuan/Sribuu/issues/673) | — | D1 foreign keys never enabled (data integrity hole); body.hasOwnProperty() prototype override DoS; JWT `exp: 0` bypasses expiry check; Frontend has no income/expense toggle (all transactions recorded as income after schema fix); Rules PUT not refactored with allowedFields pattern; 15+ duplicate try/catch blocks; Rules list missing is_active filter; 4 dead D1 tables with zero API routes |

|| 2026-07-09 (22:00) | [#696](https://github.com/lafuan/Sribuu/issues/696) [#697](https://github.com/lafuan/Sribuu/issues/697) [#698](https://github.com/lafuan/Sribuu/issues/698) [#699](https://github.com/lafuan/Sribuu/issues/699) [#700](https://github.com/lafuan/Sribuu/issues/700) [#701](https://github.com/lafuan/Sribuu/issues/701) | [#688](https://github.com/lafuan/Sribuu/pull/688) | transaction_date format not validated — malformed dates silently break strftime filters; Missing Content-Type validation (defense-in-depth gap); hexToRgba() uses wrong slice indices — Food icon shows yellow instead of red; Duplicate orphan test at api.test.ts:550; Payment methods GET-only with no user CRUD; JSON.parse() on static files has no try/catch |

| **Latest Run:** 2026-07-09 22:00 WIB

## Code Quality Score: 4/10

The backend is a functional prototype showing signs of rapid iteration. It works end-to-end for basic flows but has critical issues:

### Issues Created This Run (2026-07-09 22:00 WIB)

| # | Priority | Title | File:Line |
|---|----------|-------|-----------|
| [#696](https://github.com/lafuan/Sribuu/issues/696) | 🟡 MEDIUM | transaction_date format not validated — malformed dates break strftime filters and frontend parsing | `_worker.ts:210-211` |
| [#697](https://github.com/lafuan/Sribuu/issues/697) | 🟡 MEDIUM | Missing Content-Type validation — defense-in-depth gap enables attack surface expansion | `_worker.ts:64-68` |
| [#698](https://github.com/lafuan/Sribuu/issues/698) | 🔴 HIGH | hexToRgba() uses wrong slice indices for 6-char hex colors — Food icon shows yellow instead of red | `public/app.js (hexToRgba)` |
| [#699](https://github.com/lafuan/Sribuu/issues/699) | 🟢 LOW | Duplicate orphan test at api.test.ts:550 — tests outside describe block | `tests/api.test.ts:550` |
| [#700](https://github.com/lafuan/Sribuu/issues/700) | 🟡 MEDIUM | Payment methods GET-only with no user CRUD — cannot add custom payment methods | `_worker.ts:146-158` |
| [#701](https://github.com/lafuan/Sribuu/issues/701) | 🟢 LOW | JSON.parse() on static files has no try/catch — uncaught SyntaxError crash risk | `_worker.ts:55-57` |
