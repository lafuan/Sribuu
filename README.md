# Sribuu — Daily Expense Tracker

[![CI](https://github.com/lafuan/Sribuu/actions/workflows/ci.yml/badge.svg)](https://github.com/lafuan/Sribuu/actions/workflows/ci.yml)
[![Coverage](https://codecov.io/gh/lafuan/Sribuu/branch/main/graph/badge.svg)](https://codecov.io/gh/lafuan/Sribuu)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A lightweight web application for tracking daily expenses. Built with Python FastAPI + SQLite + Jinja2 + HTMX.

**Live**: [sribuu.duckdns.org](https://sribuu.duckdns.org) | **Docs**: [Agent Documentation](docs/agents/)

---

## 🚀 Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | Python 3.11+ / FastAPI |
| Database | PostgreSQL (production) / SQLite (dev) + SQLAlchemy 2.0 (async) |
| Frontend | Jinja2 + HTMX + Alpine.js + Tailwind CSS |
| Charts | Chart.js CDN |
| Server | Uvicorn + Nginx + systemd |
| CI/CD | GitHub Actions |
| SAST | Bandit, CodeQL |
| Linting | Ruff, Mypy |
| Migrations | Alembic (async) |
| Logging | Structlog (JSON structured) |
| iOS App | Flutter (unsigned IPA for sideloading) |

## 🤖 Autonomous AI Agents

Sribuu uses a fleet of autonomous AI agents for continuous quality monitoring. Each agent runs on a cron schedule and creates GitHub Issues with findings.

| Agent | Schedule | Focus Area |
|-------|----------|------------|
| [Scrum Master](docs/agents/scrum-master.md) | 08:00, 19:00 WIB | Backlog prioritization, sprint planning |
| [Business Analyst](docs/agents/business-analyst.md) | 07:00 WIB | Market research, feature discovery |
| [Backend](docs/agents/backend.md) | 10:00, 16:00, 22:00 WIB | Code quality, architecture, N+1 queries |
| [Frontend](docs/agents/frontend.md) | 12:00, 18:00, 00:00 WIB | UI/UX, accessibility, CSS cleanup |
| [QA](docs/agents/qa.md) | Every 2 hours | CI health, flaky tests, coverage gaps |
| [DevOps](docs/agents/devops.md) | 02:00, 14:00, 20:00 WIB | Infrastructure health, deploy safety |
| [Security](docs/agents/security.md) | 03:00, 09:00, 15:00, 21:00 WIB | SAST, infra hardening, CVE audit |
| [Database](docs/agents/database.md) | 05:00, 13:00, 21:00 WIB | Query performance, index optimization |
| [Mobile](docs/agents/mobile.md) | 06:00, 18:00 WIB | Flutter iOS code quality, build health |

See [Agent Documentation](docs/agents/README.md) for full details.

## Quick Start (Development)

```bash
# Clone repo
git clone https://github.com/lafuan/Sribuu.git
cd Sribuu

# Setup virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run with hot reload
make dev
# or: cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Open http://localhost:8000

## Makefile Commands

| Command | Description |
|---------|-------------|
| `make dev` | Run server with hot reload |
| `make test` | Run all tests (backend + frontend) |
| `make test-backend` | Run backend tests only |
| `make test-frontend` | Run frontend tests only |
| `make test-cov` | Run tests with HTML coverage report |
| `make lint` | Run Ruff + Mypy checks |
| `make lint-fix` | Auto-fix linting issues |
| `make scan` | Run Bandit security scan |
| `make all` | Run lint + scan + test |
| `make install` | Install production dependencies |
| `make install-dev` | Install all dev dependencies + pre-commit |
| `make alembic-init` | Generate new migration |
| `make alembic-migrate` | Apply all pending migrations |
| `make alembic-downgrade` | Rollback last migration |
| `make clean` | Remove cache and build artifacts |

## Project Structure

```
Sribuu/
├── backend/
│   ├── main.py              # FastAPI entry point
│   ├── config.py            # Application configuration
│   ├── database.py          # Database connection + session
│   ├── alembic.ini          # Alembic configuration
│   ├── migrations/          # Database migrations
│   ├── models/              # SQLAlchemy models
│   ├── schemas/             # Pydantic schemas
│   ├── routers/             # API routes
│   ├── services/            # Business logic
│   ├── utils/               # Helpers (security, logging, formatting)
│   └── tests/               # Backend tests
├── frontend/
│   ├── templates/           # Jinja2 templates
│   ├── static/              # Static assets (CSS, JS)
│   └── tests/               # Frontend tests
├── flutter_app/             # Flutter iOS app
├── docs/
│   └── agents/              # AI agent documentation
├── scripts/                 # VPS deployment scripts
├── .github/
│   ├── workflows/
│   │   ├── ci.yml           # CI pipeline
│   │   ├── ios-build.yml    # iOS IPA build
│   │   └── deploy.yml       # CD pipeline
│   └── dependabot.yml       # Auto dependency updates
├── pyproject.toml           # Centralized tool config
├── .pre-commit-config.yaml  # Pre-commit hooks
├── Makefile                 # Development shortcuts
└── requirements.txt
```

## CI/CD Pipeline

### CI (Continuous Integration)
Trigger on push & PR to `main`:
- **pip-audit** — Dependency vulnerability scanning
- **Bandit** — Python SAST security scan
- **Ruff** — Fast Python linter
- **Mypy** — Static type checking
- **Pytest** — All tests (backend + frontend)
- **pytest-cov** — Coverage report (fail < 70%)
- **CodeQL** — GitHub security analysis (Python + JavaScript)

### CD (Continuous Deployment)
Trigger on push to `main` (after merge):
- SSH to VPS → git pull → restart service → health check
- Auto-rollback if health check fails
- Uses GitHub Secrets: `SSH_HOST`, `SSH_USER`, `SSH_KEY`

## Deploy to VPS

### Prerequisites
- Ubuntu 22.04+ VPS
- Domain pointing to VPS
- GitHub Secrets configured (`SSH_HOST`, `SSH_USER`, `SSH_KEY`)

### Automated Setup

```bash
# SSH to VPS
ssh user@your-vps-ip

# Clone and run setup script
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/lafuan/Sribuu/main/scripts/setup-vps.sh)"
```

### Manual Setup (Step by Step)

```bash
# 1. Install dependencies
sudo apt-get update
sudo apt-get install -y nginx python3-venv ufw fail2ban git certbot python3-certbot-nginx

# 2. Clone repo
sudo git clone https://github.com/lafuan/Sribuu.git /opt/sribuu

# 3. Setup venv
cd /opt/sribuu
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. Copy systemd service
sudo cp scripts/sribuu.service /etc/systemd/system/
sudo systemctl daemon-reload

# 5. Copy nginx config
sudo cp scripts/sribuu.nginx.conf /etc/nginx/sites-available/sribuu
sudo ln -s /etc/nginx/sites-available/sribuu /etc/nginx/sites-enabled/
sudo nginx -t

# 6. Start services
sudo systemctl enable --now sribuu nginx

# 7. Setup SSL
sudo certbot --nginx -d your-domain.com
```

### Database Migrations

```bash
# Generate migration (after model changes)
cd backend
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Monitoring

```bash
# Health check
curl http://localhost:8000/health

# Service status
sudo systemctl status sribuu

# Logs
sudo journalctl -u sribuu -f
sudo tail -f /var/log/nginx/sribuu-access.log
```

## License

MIT
