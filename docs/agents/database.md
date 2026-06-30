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

_(Updated daily at 23:00 WIB by Daily Progress Recorder)_
