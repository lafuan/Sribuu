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

### 2026-07-03
- Issue [#214](https://github.com/lafuan/Sribuu/issues/214): 🐌 N+1 Query: Nested loop sparkline query in stats_service (6 months × N categories) — ⏳ OPEN
- Issue [#207](https://github.com/lafuan/Sribuu/issues/207): Critical: stats_service.py is a 1623-line god object — violates SRP, multiple functions >200 lines, untested code — ⏳ OPEN
- Issue [#206](https://github.com/lafuan/Sribuu/issues/206): Critical: pages.py violates Dependency Rule — direct model/database imports (24 occurrences) — ⏳ OPEN
- Issue [#203](https://github.com/lafuan/Sribuu/issues/203): 🔴 Notification router has no service layer — business logic and DB operations in route handlers — ⏳ OPEN
- Issue [#202](https://github.com/lafuan/Sribuu/issues/202): 🔴 Mixed DB session lifecycle: pages.py uses 17 manual get_db_session() calls instead of Depends(get_db) — leak risk — ⏳ OPEN

### 2026-07-02
- Issue [#188](https://github.com/lafuan/Sribuu/issues/188): Systemic Clean Architecture violation: business logic leaked into routers — ⏳ OPEN
- Issue [#187](https://github.com/lafuan/Sribuu/issues/187): stats_service.py is 1602 lines with 11 functions exceeding 50 lines — extreme SRP violation — ⏳ OPEN
- Issue [#182](https://github.com/lafuan/Sribuu/issues/182): Zero service-layer unit tests — 12 service files with no isolated test coverage — ⏳ OPEN
- Issue [#181](https://github.com/lafuan/Sribuu/issues/181): pdf_service.py has 2 functions over 190 lines — violates Single Responsibility Principle — ⏳ OPEN

### 2026-07-01
- Issue [#167](https://github.com/lafuan/Sribuu/issues/167): pages.py is 1052 lines with 19 routes — violates Single Responsibility Principle — ⏳ OPEN
- Issue [#166](https://github.com/lafuan/Sribuu/issues/166): 18 deprecated datetime.utcnow() calls in models and services — ✅ CLOSED
- Issue [#165](https://github.com/lafuan/Sribuu/issues/165): Duplicate datetime helper functions across services (DRY violation) — ⏳ OPEN

### 2026-06-30
- Issue [#117](https://github.com/lafuan/Sribuu/issues/117): [Backend Agent] Refactor pages.py (1048 lines) → Modular Router Split — ⏳ OPEN
- Issue [#118](https://github.com/lafuan/Sribuu/issues/118): [Backend Agent] Replace deprecated datetime.utcnow() (17 occurences) — ⏳ OPEN
- Issue [#119](https://github.com/lafuan/Sribuu/issues/119): [Backend Agent] Split stats_service.py (1604 lines) + Add Caching Layer — ⏳ OPEN
- Issue [#128](https://github.com/lafuan/Sribuu/issues/128): 🔴 CI Broken: Ruff lint errors blocking main pipeline (10 failures across 3 files) — ✅ CLOSED
- Issue [#136](https://github.com/lafuan/Sribuu/issues/136): 🔴 God Class: stats_service.py (1,602 lines) — needs decomposition — ⏳ OPEN
- Issue [#137](https://github.com/lafuan/Sribuu/issues/137): 🟡 datetime.utcnow() deprecated — 18 occurrences across backend — ⏳ OPEN
- Issue [#138](https://github.com/lafuan/Sribuu/issues/138): 🟡 Duplicated Code: PaymentMethod query repeated 5× in pages.py — ⏳ OPEN
- Issue [#146](https://github.com/lafuan/Sribuu/issues/146): CRITICAL: stats_service.py is 1,602 lines with 4 functions over 200 lines — ⏳ OPEN
- Issue [#147](https://github.com/lafuan/Sribuu/issues/147): CRITICAL: E2E login test fails — asserts 'Masuk' but page title is 'Login — Sribuu' (i18n mismatch) — ⏳ OPEN
- Issue [#148](https://github.com/lafuan/Sribuu/issues/148): Clean Code: pages.py (1,052 lines) has duplicated PaymentMethod queries — ⏳ OPEN
- Issue [#149](https://github.com/lafuan/Sribuu/issues/149): Clean Code: 18 deprecated datetime.utcnow() calls in models/__init__.py and stats_service.py — ⏳ OPEN
- Issue [#150](https://github.com/lafuan/Sribuu/issues/150): Clean Code: 10 models crammed into single models/__init__.py (247 lines) — ⏳ OPEN
