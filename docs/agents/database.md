# Database Performance Agent

**Schedule**: 05:00, 13:00, 21:00 WIB (3x daily)
**Skills**: `ddia-systems`, `clean-architecture`
**Output**: GitHub Issues with label `database`, `agent-recommendation`

## Role

The Database Agent audits PostgreSQL query patterns, index usage, and connection management for the Sribuu FastAPI backend.

## Audit Dimensions

### 1. N+1 Query Detection
- Scan SQLAlchemy relationship definitions in `backend/models/`
- Check for missing `selectinload`/`joinedload` eager loading
- Calculate relationship-to-eager-loading ratio

### 2. Query Pattern Analysis
- Identify repeated query patterns in `backend/services/`
- Flag queries without pagination/limit
- Check for unnecessary `unique().scalars().all()` chains

### 3. Index Optimization
- Review existing indexes defined in SQLAlchemy models
- Check for missing indexes on filter/sort columns
- Identify potential composite indexes for multi-column queries

### 4. Connection Pool Health
- Check SQLAlchemy pool configuration (`pool_size`, `max_overflow`)
- Verify pool isn't overwhelmed under expected load
- Recommend async connection patterns

### 5. Migration Safety
- Check Alembic migration history for consistency
- Flag migrations without downgrade paths
- Test migration files for syntax errors

## Database Stack

| Component | Technology |
|-----------|-----------|
| Database | PostgreSQL |
| ORM | SQLAlchemy (async) |
| Migrations | Alembic |
| Async driver | asyncpg |
| Connection pooling | SQLAlchemy QueuePool |

## Common Issues Flagged

| Issue | Pattern | Severity |
|-------|---------|----------|
| Missing `selectinload` | Every relationship access = 1 extra query | High |
| No pagination | Unbounded result sets on lists | Medium |
| Missing index on FK | Slows JOIN operations | Medium |
| `pool_size` too small | Connection starvation under load | High |
| Migration without downgrade | Cannot rollback | Medium |

## Recent Activity

### 2026-07-02
- Issue [#186](https://github.com/lafuan/Sribuu/issues/186): 🟢 DEBUG=True still enabled in production config — ⏳ OPEN
- Issue [#185](https://github.com/lafuan/Sribuu/issues/185): 🟡 Missing Index on paid_transaction_id (bills table) — ⏳ OPEN
- Issue [#184](https://github.com/lafuan/Sribuu/issues/184): 🔴 CRITICAL: Sankey endpoint crashes — nonexistent columns Transaction.type, Transaction.date, Category.parent_id — ⏳ OPEN

### 2026-06-30
- Issue [#142](https://github.com/lafuan/Sribuu/issues/142): [DB Agent] 🔴 N+1 Queries: Sparkline (60+ queries), Monthly Comparison, Rule Application — ⏳ OPEN
- Issue [#143](https://github.com/lafuan/Sribuu/issues/143): [DB Agent] 🟡 Missing Connection Pool Config + Inconsistent Session Management — ⏳ OPEN
- Issue [#144](https://github.com/lafuan/Sribuu/issues/144): [DB Agent] 🟡 Missing Index on parent_transaction_id + Text Search Optimization — ⏳ OPEN
- Issue [#145](https://github.com/lafuan/Sribuu/issues/145): [DB Agent] 🟢 Minor: Unbounded .all() Queries + Positive Findings — ⏳ OPEN
