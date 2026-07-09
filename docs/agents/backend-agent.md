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

**Latest Run:** 2026-07-09 16:00 WIB

## Code Quality Score: 4/10

The backend is a functional prototype showing signs of rapid iteration. It works end-to-end for basic flows but has critical issues:

### Issues Created This Run (2026-07-09 16:00 WIB)

| # | Priority | Title | File:Line |
|---|----------|-------|-----------|
| [#666](https://github.com/lafuan/Sribuu/issues/666) | 🔴 HIGH | D1 foreign key constraints not enabled — invalid category/payment_method IDs silently accepted | `_worker.ts:211-213` |
| [#667](https://github.com/lafuan/Sribuu/issues/667) | 🟡 MEDIUM | Rules PUT handler not refactored in schema fix — inconsistent field whitelisting | `_worker.ts:370-377` |
| [#668](https://github.com/lafuan/Sribuu/issues/668) | 🟡 MEDIUM | body.hasOwnProperty(key) vulnerable to prototype overrides — malicious JSON key causes 500 | `_worker.ts:258` |
| [#669](https://github.com/lafuan/Sribuu/issues/669) | 🟡 MEDIUM | JWT expiry check uses loose `&&` — tokens with `exp: 0` or missing `exp` never expire | `_worker.ts:91` |
| [#670](https://github.com/lafuan/Sribuu/issues/670) | 🔴 HIGH | Frontend transaction form has no income/expense toggle — all UI transactions recorded as income | `public/app.js submitTx()` |
| [#671](https://github.com/lafuan/Sribuu/issues/671) | 🟢 LOW | 15+ duplicate try/catch blocks — Hono app.onError() can eliminate all boilerplate | `_worker.ts` (entire file) |
| [#672](https://github.com/lafuan/Sribuu/issues/672) | 🟡 MEDIUM | Rules list endpoint missing `is_active` filter — inactive rules returned, index unused | `_worker.ts:336-337` |
| [#673](https://github.com/lafuan/Sribuu/issues/673) | 🟢 LOW | 4 of 8 D1 tables have zero API routes — budgets, subscriptions, bills, templates are dead schema | `migrations/0001_initial.sql` |
