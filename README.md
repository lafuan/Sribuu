# Sribuu — Aplikasi Pencatatan Pengeluaran Harian

[![CI](https://github.com/lafuan/Sribuu/actions/workflows/ci.yml/badge.svg)](https://github.com/lafuan/Sribuu/actions/workflows/ci.yml)
[![Coverage](https://codecov.io/gh/lafuan/Sribuu/branch/main/graph/badge.svg)](https://codecov.io/gh/lafuan/Sribuu)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Aplikasi web ringan untuk mencatat pengeluaran harian. Dibangun dengan Python FastAPI + SQLite + Jinja2 + HTMX.

## Tech Stack

| Komponen | Teknologi |
|----------|-----------|
| Backend | Python 3.11+ / FastAPI |
| Database | SQLite + SQLAlchemy 2.0 (async) |
| Frontend | Jinja2 + HTMX + Alpine.js + Tailwind CSS CDN |
| Chart | Chart.js CDN |
| Server | Uvicorn + Nginx |
| CI/CD | GitHub Actions |
| SAST | Bandit, CodeQL |
| Linting | Ruff, Mypy |
| Migrations | Alembic (async) |
| Logging | Structlog (JSON structured) |

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
# atau: cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Buka http://localhost:8000

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

## Struktur Proyek

```
Sribuu/
├── backend/
│   ├── main.py              # Entry point FastAPI
│   ├── config.py            # Konfigurasi aplikasi
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
│   └── tests/               # Frontend tests
├── scripts/                 # VPS deployment scripts
├── docs/                    # Dokumentasi
├── .github/
│   ├── workflows/
│   │   ├── ci.yml           # CI pipeline
│   │   └── deploy.yml       # CD pipeline
│   └── dependabot.yml       # Auto dependency updates
├── pyproject.toml            # Centralized tool config
├── .pre-commit-config.yaml  # Pre-commit hooks
├── Makefile                  # Development shortcuts
└── requirements.txt
```

## CI/CD Pipeline

### CI (Continuous Integration)
Trigger on push & PR ke `main`:
- **pip-audit** — Dependency vulnerability scanning
- **Bandit** — Python SAST security scan
- **Ruff** — Fast Python linter
- **Mypy** — Static type checking
- **Pytest** — All tests (backend 56 + frontend 19)
- **pytest-cov** — Coverage report (fail < 70%)
- **CodeQL** — GitHub security analysis (Python + JavaScript)

### CD (Continuous Deployment)
Trigger on push ke `main` (setelah merge):
- SSH ke VPS → git pull → restart service → health check
- Auto-rollback jika health check gagal
- Gunakan GitHub Secrets: `SSH_HOST`, `SSH_USER`, `SSH_KEY`

## Deploy ke VPS

### Prasyarat
- Ubuntu 22.04+ VPS
- Domain yang mengarah ke VPS
- GitHub Secrets terisi (`SSH_HOST`, `SSH_USER`, `SSH_KEY`)

### Setup Manual

```bash
# SSH ke VPS
ssh user@your-vps-ip

# Clone dan jalankan setup script
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/lafuan/Sribuu/main/scripts/setup-vps.sh)"
```

Atau step-by-step:

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
# Generate migration (setelah perubahan model)
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

## Lisensi

MIT
