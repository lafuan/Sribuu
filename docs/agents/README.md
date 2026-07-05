# Agent Documentation

Sribuu uses a fleet of autonomous AI agents for continuous quality monitoring and backlog generation. Each agent runs as a scheduled cron job and produces reports as GitHub Issues.

## Today's Activity (2026-07-05)

| Agent | Issues Created | Status |
|-------|---------------|--------|
| Security Agent | 1 | 1 open, 0 closed |
| DevOps Agent | 1 | 1 open, 0 closed |
| Frontend Agent | 1 | 1 open, 0 closed |
| BA Agent | 1 | 1 open, 0 closed |
| Backend Agent | 0 | — |
| Database Agent | 0 | — |
| QA Agent | 0 | — |
| Mobile Agent | 0 | — |
| Scrum Master Agent | 0 | — |

**Total**: 4 agent issues today (4 open, 0 closed)

### CI Status
- ✅ **4 CI runs** succeeded
- ✅ **1 PR merged**:
  - #254 fix: use actions/checkout@v4 instead of nonexistent @v7

## Agent Fleet Overview

| Agent | Schedule | Focus Area | Issues Label |
|-------|----------|------------|--------------|
| [Scrum Master](scrum-master.md) | 08:00, 19:00 WIB | Backlog prioritization, sprint planning, execution delegation | `scrum` |
| [Business Analyst](business-analyst.md) | 07:00 WIB | Market research, competitor analysis, feature discovery | `feature` |
| [Backend](backend.md) | 10:00, 16:00, 22:00 WIB | Code quality, architecture, N+1 queries, test coverage | `backend` |
| [Frontend](frontend.md) | 12:00, 18:00, 00:00 WIB | UI/UX, accessibility, CSS cleanup, responsive design | `frontend` |
| [QA](qa.md) | Every 2 hours | CI health, flaky tests, coverage gaps | `bug`, `testing` |
| [DevOps](devops.md) | 02:00, 14:00, 20:00 WIB | Infrastructure health, deploy safety, server monitoring | `infrastructure` |
| [Security](security.md) | 03:00, 09:00, 15:00, 21:00 WIB | Code SAST, infra hardening, dependency CVE, secrets scanning | `security` |
| [Database](database.md) | 05:00, 13:00, 21:00 WIB | Query performance, index optimization, connection pool | `database` |
| [Mobile](mobile.md) | 06:00, 18:00 WIB | Flutter iOS code quality, build health, dependency audit | `mobile` |
| [Daily Progress](daily-progress.md) | 23:00 WIB | Compiles all daily agent activity into one report | `documentation` |

## How Agents Work

1. **Schedule**: Each agent runs on a fixed cron schedule
2. **Audit**: Agent scans its domain (code, infra, CI, deps, UI, etc.)
3. **Report**: Findings are posted to this Telegram chat
4. **Backlog**: Critical findings become GitHub Issues with `agent-recommendation` label
5. **Scrum**: Scrum Master reviews all agent recommendations twice daily and prioritizes

## Issue Labels

All agent-created issues use these labels:

| Label | Purpose |
|-------|---------|
| `agent-recommendation` | All agent-generated issues |
| `bug` | QA findings |
| `feature` | BA feature research |
| `security` | Security audit findings |
| `infrastructure` | DevOps infrastructure issues |
| `backend` / `frontend` / `mobile` | Domain-specific issues |
| `database` | Database performance issues |
| `documentation` | Progress logs, docs |
| `priority-high` / `priority-medium` / `priority-low` | Severity |

## Agent Policy

- **REPORT-ONLY**: Agents do NOT create PRs, commit code, or modify anything
- **ISSUES ONLY**: Agents create GitHub Issues for the Scrum Master to review
- **ENGLISH ONLY**: All issue titles and bodies must be in English
- **AUTONOMOUS**: No human intervention needed — agents run on schedule
