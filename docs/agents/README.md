# Agent Documentation

Sribuu uses a fleet of autonomous AI agents for continuous quality monitoring and backlog generation. Each agent runs as a scheduled cron job and produces reports as GitHub Issues.

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

## Today's Activity (2026-07-04)

| Agent | Issues Created | Status |
|-------|---------------|--------|
| Backend Agent | 11 | 4 open, 7 closed |
| Frontend Agent | 2 | 2 open, 0 closed |
| BA Agent | 1 | 1 open, 0 closed |
| DevOps Agent | 2 | 0 open, 2 closed |
| Database Agent | 0 | — |
| QA Agent | 0 | — |
| Security Agent | 0 | — |
| Mobile Agent | 0 | — |
| Scrum Master Agent | 0 | — |

**Total**: 16 agent issues today (7 open, 9 closed ✅ significant backlog reduction!)

### CI Status
- ✅ **10 CI runs** succeeded
- ✅ **10 Docker builds** succeeded
- ✅ **7 Deploys** succeeded (1 failure, later fixed)
- ✅ **7 PRs merged**:
  - [#218](https://github.com/lafuan/Sribuu/pull/218) — fix: deploy rollback now actually executes + inline smoke test
  - [#226](https://github.com/lafuan/Sribuu/pull/226) — fix(ci): remove broken inline smoke test, restore post-deploy Playwright test
  - [#227](https://github.com/lafuan/Sribuu/pull/227) — fix: replace N+1 query in annual_summary_stats with single GROUP BY (Closes #220)
  - [#228](https://github.com/lafuan/Sribuu/pull/228) — fix: replace N+1 cascade in get_cash_flow_forecast with single GROUP BY (Closes #221)
  - [#229](https://github.com/lafuan/Sribuu/pull/229) — fix: extract shared template context dict in dashboard_page to eliminate duplication (Closes #222)
  - [#230](https://github.com/lafuan/Sribuu/pull/230) — fix: deduplicate date helper functions into shared utils/time.py (Closes #223)
  - [#232](https://github.com/lafuan/Sribuu/pull/232) — fix: extract notification service layer from router (Closes #203)

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
