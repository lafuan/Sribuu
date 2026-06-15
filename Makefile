.PHONY: dev test lint scan all install clean alembic-init alembic-migrate

# ─── Development ────────────────────────────────────────────────────
dev:
	cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000

# ─── Testing ────────────────────────────────────────────────────────
test:
	pytest backend/tests/ frontend/tests/ -v --tb=short

test-backend:
	pytest backend/tests/ -v --tb=short

test-frontend:
	pytest frontend/tests/ -v --tb=short

test-cov:
	pytest backend/tests/ frontend/tests/ --cov=backend --cov=frontend --cov-report=term-missing --cov-report=html -v

# ─── Linting ────────────────────────────────────────────────────────
lint:
	ruff check backend/
	mypy backend/ --config-file pyproject.toml --explicit-package-bases

lint-fix:
	ruff check backend/ --fix

# ─── Security Scan ──────────────────────────────────────────────────
scan:
	bandit -c pyproject.toml -r backend/

# ─── All checks ─────────────────────────────────────────────────────
all: lint scan test

# ─── Install ────────────────────────────────────────────────────────
install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements.txt
	pip install ruff mypy bandit pytest-cov pre-commit
	pre-commit install

# ─── Alembic ────────────────────────────────────────────────────────
alembic-init:
	cd backend && alembic revision --autogenerate -m "initial"

alembic-migrate:
	cd backend && alembic upgrade head

alembic-downgrade:
	cd backend && alembic downgrade -1

# ─── Cleanup ────────────────────────────────────────────────────────
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	find . -type f -name "coverage.xml" -delete 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
