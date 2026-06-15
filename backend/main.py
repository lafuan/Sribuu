"""
Entry point aplikasi Sribuu.
"""

import subprocess
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
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

# Static files (CSS, JS, images)
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# --- Routes ---

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.APP_VERSION}


# Import dan daftarkan routers (akan ditambahkan di fase development)
# from .routers import auth, transactions, categories, stats, export
# app.include_router(auth.router)
