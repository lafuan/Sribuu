# DevOps Agent

**Schedule**: 02:00, 14:00, 20:00 WIB (3x daily)
**Skills**: `release-it`, `ddia-systems`, `clean-architecture`
**Output**: GitHub Issues with label `infrastructure`, `agent-recommendation`

## Role

The DevOps Agent monitors server health, CI/CD pipeline safety, and deployment readiness for the Sribuu VPS.

## Audit Dimensions

### 1. Server Health
- **CPU & Memory**: Top consumers, memory pressure, swap usage
- **Disk**: Available space, large directories
- **Services**: nginx, sribuu app, PostgreSQL status
- **Uptime**: Server uptime and load averages

### 2. CI/CD Pipeline
- **Workflow runs**: Recent status on main branch
- **Stale PRs**: Open PRs older than 24 hours
- **Build cache**: Disk usage of pip/npm caches
- **Artifact cleanup**: Expiring artifacts in GitHub Actions

### 3. Security Surface
- **SSH config**: Root login disabled, key-only auth
- **Firewall**: UFW active, only necessary ports open
- **Open ports**: Audit listening services

### 4. Deploy Pipeline
- **Last deploy**: Freshness of production deployment
- **Backups**: Database backup schedule and recency
- **SSL**: Certificate expiry date

## Infrastructure Stack

| Component | Technology |
|-----------|-----------|
| Server | Ubuntu VPS |
| Web server | Nginx + Let's Encrypt |
| App server | Uvicorn (systemd) |
| Database | PostgreSQL |
| CI/CD | GitHub Actions |
| Firewall | UFW |

## Common Issues Flagged

| Issue | Severity |
|-------|----------|
| Disk >85% full | Critical |
| Service down | Critical |
| Stale PRs >3 days | Medium |
| SSH password auth enabled | High |
| UFW inactive | High |
| SSL expiring <7 days | Critical |

## Recent Activity

_(Updated daily at 23:00 WIB by Daily Progress Recorder)_
