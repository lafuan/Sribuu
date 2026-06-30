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
