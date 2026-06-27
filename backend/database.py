"""
Database connection dan session management.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from .config import settings

# Async engine untuk SQLite
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base class untuk semua model."""
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency untuk mendapatkan database session (via FastAPI DI / Depends)."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def get_db_session() -> AsyncSession:
    """Buat session langsung tanpa async generator.
    Gunakan ini untuk direct calls (bukan via Depends).
    Handler wajib close manual: finally: await db.close()
    """
    return AsyncSessionLocal()


async def init_db():
    """Inisialisasi database: buat tabel + seed data."""
    from .models import (  # noqa: F401, PLC0415
        Bill,
        Budget,
        Category,
        PaymentMethod,
        Subscription,
        Transaction,
        TransactionTemplate,
        User,
        WeeklySummary,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    from .services.seed import seed_all  # noqa: PLC0415 (circular import)

    async with AsyncSessionLocal() as session:
        result = await seed_all(session)
        if result["categories_added"] > 0 or result["payment_methods_added"] > 0:
            await session.commit()
            print(f"Seed data: {result['categories_added']} kategori, {result['payment_methods_added']} metode pembayaran")
