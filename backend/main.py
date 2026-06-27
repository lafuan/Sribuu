"""
Entry point aplikasi Sribuu.
"""

import os
import subprocess
import sys
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .config import settings
from .database import init_db
from .utils.logging import configure_logging, get_logger
from .utils.middleware import LoggingMiddleware

# Configure structured logging
configure_logging(debug=settings.DEBUG)
logger = get_logger(__name__)

# Path ke frontend templates
BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = BASE_DIR / "frontend" / "templates"
STATIC_DIR = BASE_DIR / "frontend" / "static"


def _run_alembic_upgrade() -> None:
    """Run alembic upgrade to head before app startup."""
    # Skip if SKIP_ALEMBIC env var is set (used by E2E tests)
    if os.environ.get("SKIP_ALEMBIC") == "true":
        return
    backend_dir = Path(__file__).resolve().parent
    alembic_ini = backend_dir / "alembic.ini"
    if alembic_ini.exists():
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "-c", str(alembic_ini), "upgrade", "head"],
            cwd=str(backend_dir),
            capture_output=True,
            check=False,
            text=True,
        )
        if result.returncode != 0:
            print(f"[WARN] Alembic upgrade failed: {result.stderr}")
        else:
            print(f"[Alembic] {result.stdout.strip()}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup dan shutdown lifecycle."""
    # Startup: run database migrations + seed data
    _run_alembic_upgrade()
    await init_db()
    yield
    # Shutdown: cleanup (jika diperlukan)


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# Add structured logging middleware
app.add_middleware(LoggingMiddleware)

# Templates
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
# Add flash messages support (dummy — implement session-based later)
templates.env.globals["get_flashed_messages"] = lambda with_categories=False: []
# Add `now` function for templates
templates.env.globals["now"] = lambda: datetime.now(timezone(timedelta(hours=7)))

# Custom Jinja2 filters (Indonesian locale)
def _format_date_id(value, fmt="%d %B %Y"):
    """Format datetime ke bahasa Indonesia. e.g. '15 Juni 2026'"""
    if value is None:
        return ""
    if isinstance(value, str):
        value = datetime.fromisoformat(value)
    months = [
        "Januari", "Februari", "Maret", "April", "Mei", "Juni",
        "Juli", "Agustus", "September", "Oktober", "November", "Desember"
    ]
    result = fmt
    result = result.replace("%B", months[value.month - 1])
    result = result.replace("%d", str(value.day))
    result = result.replace("%Y", str(value.year))
    result = result.replace("%m", f"{value.month:02d}")
    return value.strftime(result) if "%" in result else result

def _format_time(value, fmt="%H:%M"):
    """Format datetime ke jam. e.g. '14:30'"""
    if value is None:
        return ""
    if isinstance(value, str):
        value = datetime.fromisoformat(value)
    return value.strftime(fmt)

templates.env.filters["format_date_id"] = _format_date_id
templates.env.filters["format_time"] = _format_time

# Static files (CSS, JS, images)
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# --- Routes ---


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.APP_VERSION}


# --- PWA Routes ---


@app.get("/sw.js", include_in_schema=False)
async def service_worker():
    sw_path = STATIC_DIR / "sw.js"
    if sw_path.exists():
        return FileResponse(str(sw_path), media_type="application/javascript",
                            headers={"Service-Worker-Allowed": "/",
                                     "Cache-Control": "no-cache"})
    return {"status": "not found"}, 404


@app.get("/manifest.json", include_in_schema=False)
async def manifest():
    m_path = STATIC_DIR / "manifest.json"
    if m_path.exists():
        return FileResponse(str(m_path), media_type="application/manifest+json",
                            headers={"Cache-Control": "no-cache"})
    return {"status": "not found"}, 404


# --- API Routers ---
from .routers import (  # noqa: E402
    auth,
    bills,
    budgets,
    categories,
    expense_templates,
    export,
    notifications,
    payment_methods,
    stats,
    subscriptions,
    transactions,
)

app.include_router(auth.router)
app.include_router(transactions.router)
app.include_router(categories.router)
app.include_router(stats.router)
app.include_router(export.router)
app.include_router(notifications.router)
app.include_router(payment_methods.router)
app.include_router(budgets.router)
app.include_router(expense_templates.router)  # type: ignore[has-type]
app.include_router(bills.router)
app.include_router(subscriptions.router)

# --- Page Router (HTML) — harus didaftarkan setelah API routers ---
from .routers import pages  # noqa: E402

app.include_router(pages.router)
