"""
E2E test fixtures — start FastAPI app with test DB, Playwright browser page.
"""

import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

# ── Test Config ─────────────────────────────────────────────────────
TEST_PORT = 8765
BASE_URL = f"http://localhost:{TEST_PORT}"

TEST_USER_EMAIL = "e2e@test.com"
TEST_USER_PASSWORD = "TestPass123"
TEST_USER_NAME = "E2E Tester"

# Use a temp directory for test DB
TEST_DB_DIR = Path(tempfile.mkdtemp(prefix="sribuu_e2e_"))
TEST_DB_PATH = TEST_DB_DIR / "sribuu.db"


def _init_test_db():
    """Initialize the test database and create test user."""
    env = os.environ.copy()
    env["DATABASE_URL"] = f"sqlite+aiosqlite:///{TEST_DB_PATH}"
    env["SECRET_KEY"] = "e2e-test-secret-key"

    script = f"""
import asyncio
import sys
sys.path.insert(0, '{Path(__file__).resolve().parent.parent}')

# Override DB before any imports
import os
os.environ['DATABASE_URL'] = 'sqlite+aiosqlite:///{TEST_DB_PATH}'

from backend.database import get_db_session, init_db
from backend.models import User
from sqlalchemy import select

async def setup():
    db = get_db_session()
    try:
        await init_db()

        # Check if user exists
        result = await db.execute(select(User).where(User.email == '{TEST_USER_EMAIL}'))
        user = result.scalar_one_or_none()
        if not user:
            from backend.services.auth_service import hash_password
            user = User(
                email='{TEST_USER_EMAIL}',
                name='{TEST_USER_NAME}',
                password_hash=hash_password('{TEST_USER_PASSWORD}'),
            )
            db.add(user)
            await db.commit()
            print(f"Created test user: {TEST_USER_EMAIL}")
        else:
            print(f"Test user already exists: {TEST_USER_EMAIL}")
    finally:
        await db.close()

asyncio.run(setup())
print("DB setup complete")
"""
    subprocess.run(
        [sys.executable, "-c", script],
        check=True,
        cwd=str(Path(__file__).resolve().parent.parent),
        capture_output=True,
        text=True,
    )
    print(f"Test DB initialized at {TEST_DB_PATH}")


def _start_app():
    """Start the FastAPI app with test DB."""
    env = os.environ.copy()
    env["DATABASE_URL"] = f"sqlite+aiosqlite:///{TEST_DB_PATH}"
    env["SECRET_KEY"] = "e2e-test-secret-key"
    env["DEBUG"] = "true"

    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.main:app",
         "--host", "127.0.0.1", "--port", str(TEST_PORT), "--log-level", "warning"],
        cwd=str(Path(__file__).resolve().parent.parent),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # Wait for ready
    import urllib.error
    import urllib.request

    for attempt in range(30):
        try:
            urllib.request.urlopen(f"{BASE_URL}/login", timeout=2)
            print(f"App started at {BASE_URL}")
            return proc
        except Exception:
            if attempt == 29:
                proc.kill()
                raise RuntimeError("App failed to start within 30s") from None
            time.sleep(1)

    return proc


# ── Session Fixtures ────────────────────────────────────────────────

@pytest.fixture(scope="session")
def app_process():
    """Start app + init test DB once per test session."""
    _init_test_db()
    proc = _start_app()
    yield proc
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
    # Cleanup
    shutil.rmtree(TEST_DB_DIR, ignore_errors=True)


# ── Per-Test Fixtures ───────────────────────────────────────────────

@pytest.fixture(scope="function")
def browser_context(app_process):
    """Create a fresh browser context for each test."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            locale="id-ID",
        )
        yield context
        context.close()
        browser.close()


@pytest.fixture(scope="function")
def page(browser_context):
    """Provide a Playwright page."""
    return browser_context.new_page()


@pytest.fixture(scope="function")
def login_page(page):
    """Navigate to login page and authenticate."""
    page.goto(f"{BASE_URL}/login")
    page.wait_for_load_state("networkidle")
    page.fill("input[name=email]", TEST_USER_EMAIL)
    page.fill("input[name=password]", TEST_USER_PASSWORD)
    page.click("button[type=submit]")
    page.wait_for_load_state("networkidle")
    # Should redirect to dashboard
    page.wait_for_url(f"{BASE_URL}/", timeout=5000)
    return page
