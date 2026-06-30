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
