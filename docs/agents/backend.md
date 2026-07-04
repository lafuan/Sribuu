# Backend Agent

**Schedule**: 10:00, 16:00, 22:00 WIB (3x daily)
**Skills**: `clean-code`, `clean-architecture`, `refactoring-patterns`
**Output**: GitHub Issues with label `backend`, `agent-recommendation`

## Role

The Backend Agent audits the FastAPI backend codebase for code smells, architectural violations, and test quality gaps.

## Audit Dimensions

### 1. Clean Code Audit
- **Large files** (>500 lines): Flag for potential split
- **N+1 queries**: Missing `selectinload`/`joinedload` on SQLAlchemy relationships
- **Deprecated patterns**: `datetime.utcnow()`, old-style type hints
- **Code duplication**: Repeated query patterns across services

### 2. Architecture Check
- **Layer violations**: Routers directly importing models (should go through services)
- **Router methods**: Files with >10 route handlers (should split)
- **Service cohesion**: Too many responsibilities in one service

### 3. Test Quality
- Recent test failures (from CI logs)
- Missing test files for modules
- Coverage gaps (uncovered routes and services)

## Tech Stack Context

- **Framework**: FastAPI + SQLAlchemy (async)
- **Database**: PostgreSQL (production), SQLite (testing)
- **Testing**: pytest + pytest-asyncio
- **Architecture**: Service layer pattern (routers → services → models)

## Common Issues Flagged

| Issue | Pattern | Severity |
|-------|---------|----------|
| `datetime.utcnow()` | Deprecated in Python 3.12, use `datetime.now(datetime.UTC)` | Medium |
| Direct model import in router | Bypasses service layer, violates architecture | High |
| Missing `selectinload` | N+1 query on every request | High |
| Large file (>1000 lines) | Hard to maintain, should split by domain | Medium |

## Recent Activity

### 2026-07-04
- Issue [#239](https://github.com/lafuan/Sribuu/issues/239): Deploy smoke test fails 3x consecutively — /api/categories returns 401, no rollback image, container left stopped — ⏳ OPEN
- Issue [#238](https://github.com/lafuan/Sribuu/issues/238): payment_methods.py + pages.py: zero PaymentMethod service layer — 7x duplicate queries, Dependency Rule violation — ⏳ OPEN
- Issue [#237](https://github.com/lafuan/Sribuu/issues/237): expense_templates.py: mixed DB session lifecycle — manual get_db_session() alongside Depends(get_db) — ⏳ OPEN
- Issue [#236](https://github.com/lafuan/Sribuu/issues/236): notification_service check_budget_alerts fetches ALL active categories (not just user's) — ⏳ OPEN
- Issue [#235](https://github.com/lafuan/Sribuu/issues/235): Missing Connection Pool Configuration in database.py — ✅ CLOSED
- Issue [#234](https://github.com/lafuan/Sribuu/issues/234): Missing Index: parent_transaction_id on transactions table — ✅ CLOSED
- Issue [#233](https://github.com/lafuan/Sribuu/issues/233): 🚨 CRITICAL: N+1 Query Patterns in Stats & Transaction Services — ✅ CLOSED
- Issue [#223](https://github.com/lafuan/Sribuu/issues/223): 🔴 Duplicate date helpers / queries across 3 services — DRY violation + bug risk — ✅ CLOSED
- Issue [#222](https://github.com/lafuan/Sribuu/issues/222): 🔴 Duplicate TemplateResponse block in dashboard_page — duplicated template context dict (30+ lines) — ✅ CLOSED
- Issue [#221](https://github.com/lafuan/Sribuu/issues/221): 🔴 N+1 Cascade: get_cash_flow_forecast fires 3 + N_category queries in nested loops — ✅ CLOSED
- Issue [#220](https://github.com/lafuan/Sribuu/issues/220): 🔴 N+1 Query: annual_summary_stats executes 12 queries in loop — marked # pragma: no cover (zero tests) — ✅ CLOSED

### 2026-07-03
- Issue [#214](https://github.com/lafuan/Sribuu/issues/214): 🐌 N+1 Query: Nested loop sparkline query in stats_service (6 months × N categories) — ⏳ OPEN
- Issue [#207](https://github.com/lafuan/Sribuu/issues/207): Critical: stats_service.py is a 1623-line god object — violates SRP, multiple functions >200 lines, untested code — ⏳ OPEN
- Issue [#206](https://github.com/lafuan/Sribuu/issues/206): Critical: pages.py violates Dependency Rule — direct model/database imports (24 occurrences) — ⏳ OPEN
- Issue [#203](https://github.com/lafuan/Sribuu/issues/203): 🔴 Notification router has no service layer — business logic and DB operations in route handlers — ✅ CLOSED
- Issue [#202](https://github.com/lafuan/Sribuu/issues/202): 🔴 Mixed DB session lifecycle: pages.py uses 17 manual get_db_session() calls instead of Depends(get_db) — leak risk — ⏳ OPEN

### 2026-07-02
- Issue [#188](https://github.com/lafuan/Sribuu/issues/188): Systemic Clean Architecture violation: business logic leaked into routers — ⏳ OPEN
- Issue [#187](https://github.com/lafuan/Sribuu/issues/187): stats_service.py is 1602 lines with 11 functions exceeding 50 lines — extreme SRP violation — ⏳ OPEN
- Issue [#182](https://github.com/lafuan/Sribuu/issues/182): Zero service-layer unit tests — 12 service files with no isolated test coverage — ⏳ OPEN
- Issue [#181](https://github.com/lafuan/Sribuu/issues/181): pdf_service.py has 2 functions over 190 lines — violates Single Responsibility Principle — ⏳ OPEN

### 2026-07-01
- Issue [#167](https://github.com/lafuan/Sribuu/issues/167): pages.py is 1052 lines with 19 routes — violates Single Responsibility Principle — ⏳ OPEN
- Issue [#166](https://github.com/lafuan/Sribuu/issues/166): 18 deprecated datetime.utcnow() calls in models and services — ✅ CLOSED
- Issue [#165](https://github.com/lafuan/Sribuu/issues/165): Duplicate datetime helper functions across services (DRY violation) — ✅ CLOSED
