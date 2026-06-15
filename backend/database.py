"""
Database connection dan session management.
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
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


async def get_db() -> AsyncSession:
    """Dependency untuk mendapatkan database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Inisialisasi database: buat tabel + seed data."""
    from .models import (  # noqa: F401
        User,
        Category,
        PaymentMethod,
        Transaction,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Seed data
    from .services.seed import seed_all

    async with AsyncSessionLocal() as session:
        result = await seed_all(session)
        if result["categories_added"] > 0 or result["payment_methods_added"] > 0:
            await session.commit()
            print(f"Seed data: {result['categories_added']} kategori, {result['payment_methods_added']} metode pembayaran")
