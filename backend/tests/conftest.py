"""
Test fixtures untuk seluruh backend test suite.
Digunakan file-based SQLite agar semua koneksi share database yang sama.
"""
import os
import tempfile

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Gunakan file-based SQLite agar semua koneksi share database yang sama
TEST_DB_FILE = os.path.join(tempfile.gettempdir(), "sribuu_test.db")
TEST_DB_URL = f"sqlite+aiosqlite:///{TEST_DB_FILE}"

# Override DATABASE_URL sebelum import backend modules
os.environ["DATABASE_URL"] = TEST_DB_URL
os.environ["SECRET_KEY"] = "test-secret-key-for-ci"


from backend.database import Base, get_db  # noqa: E402
from backend.services.seed import seed_all  # noqa: E402

# Test engine (file-based — semua koneksi otomatis share DB yang sama)
TEST_ENGINE = create_async_engine(
    TEST_DB_URL,
    echo=False,
    connect_args={"check_same_thread": False},
)
TEST_SESSION_FACTORY = async_sessionmaker(
    TEST_ENGINE, class_=AsyncSession, expire_on_commit=False
)


@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_test_db():
    """Buat tabel + seed data setiap test function (isolasi penuh)."""
    async with TEST_ENGINE.begin() as conn:
        # Drop all tables first untuk isolasi bersih
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    # Seed default categories & payment methods
    async with TEST_SESSION_FACTORY() as session:
        await seed_all(session)
        await session.commit()

    yield

    # Cleanup: rollback any pending txns
    async with TEST_ENGINE.connect() as conn:
        await conn.rollback()


async def _override_get_db():
    """Override get_db — setiap request dapat session test baru."""
    async with TEST_SESSION_FACTORY() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@pytest_asyncio.fixture
async def client():
    """Test client dengan dependency override ke test DB."""
    from backend.main import app  # noqa: E402

    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def db_session():
    """DB session langsung untuk operasi manual (bypass API)."""
    async with TEST_SESSION_FACTORY() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def test_user(db_session):
    """Buat test user via API (register) dan return credentials."""
    # Always use fresh user by registering via API
    # We need a client for this, use a fresh one
    from httpx import ASGITransport, AsyncClient

    from backend.main import app

    # Set up override for this client
    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Gunakan timestamp unik untuk email
        import time
        email = f"test_{int(time.time() * 1000)}@example.com"
        response = await ac.post(
            "/api/auth/register",
            json={
                "name": "Test User",
                "email": email,
                "password": "password123",
                "password_confirm": "password123",
            },
        )
        assert response.status_code == 201, f"Register failed: {response.text}"
        data = response.json()
        user = data["data"]["user"]
        result = {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "password": "password123",
        }
    app.dependency_overrides.clear()
    return result


@pytest_asyncio.fixture
async def auth_client(client, test_user):
    """Test client yang sudah ter-autentikasi (cookie diset)."""
    response = await client.post(
        "/api/auth/login",
        json={
            "email": test_user["email"],
            "password": test_user["password"],
        },
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    client.cookies = response.cookies
    return client
