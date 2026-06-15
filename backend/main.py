"""
Entry point aplikasi Sribuu.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path

from .config import settings
from .database import init_db

# Path ke frontend templates
BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = BASE_DIR / "frontend" / "templates"
STATIC_DIR = BASE_DIR / "frontend" / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup dan shutdown lifecycle."""
    # Startup: inisialisasi database + seed data
    await init_db()
    yield
    # Shutdown: cleanup (jika diperlukan)


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

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


# --- API Routers ---
from .routers import auth, transactions, categories, stats, export, payment_methods

app.include_router(auth.router)
app.include_router(transactions.router)
app.include_router(categories.router)
app.include_router(stats.router)
app.include_router(export.router)
app.include_router(payment_methods.router)

# --- Page Router (HTML) — harus didaftarkan setelah API routers ---
from .routers import pages

app.include_router(pages.router)
