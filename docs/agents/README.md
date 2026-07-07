# Sribuu Agent Fleet — Tracking Pages

> Auto-updated by each agent on every run.
> Last compiled by Daily Progress Log agent.

## Agents

| Agent | Role | Page |
|-------|------|------|
| BA Agent | Feature Research & Market Analysis | [BA Agent](ba-agent.md) |
| Scrum Master | Prioritize, Assign & Execute Backlog | [Scrum Master](scrum-master.md) |
| QA Agent | CI Health, Build & Deploy Monitor | [QA Agent](qa-agent.md) |
| Backend Agent | Hono/D1/TS Code & Architecture Audit | [Backend Agent](backend-agent.md) |
| Frontend Agent | SPA UI/UX & Performance Audit | [Frontend Agent](frontend-agent.md) |
| DevOps Agent | Cloudflare Pages CI/CD & Deploy Safety | [DevOps Agent](devops-agent.md) |
| Security Agent | CF Pages, D1, JWT, CSP Audit | [Security Agent](security-agent.md) |
| Database Agent | D1 Query, Index & Performance Audit | [Database Agent](database-agent.md) |
| Mobile Agent | Flutter iOS App Audit & Update | [Mobile Agent](mobile-agent.md) |
| Daily Progress | Update Docs + Create Summary | [Daily Progress](daily-progress.md) |

## Workflow

1. Each agent creates **GitHub Issues** for every finding (`agent-recommendation` label)
2. Each agent updates its **tracking page** in this directory on every run
3. Issues are triaged by Scrum Master
4. All code changes go through PR → CI → merge workflow
