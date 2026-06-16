"""
Seed data: kategori default dan metode pembayaran.
"""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Category, PaymentMethod

# 10 Kategori Default
DEFAULT_CATEGORIES = [
    {"name": "Makanan & Minuman",  "icon": "🍔", "color": "#10b981"},
    {"name": "Transportasi",       "icon": "🚗", "color": "#3b82f6"},
    {"name": "Belanja",            "icon": "🛒", "color": "#ec4899"},
    {"name": "Tagihan & Utilitas", "icon": "💡", "color": "#f59e0b"},
    {"name": "Hiburan",            "icon": "🎮", "color": "#8b5cf6"},
    {"name": "Kesehatan",          "icon": "💊", "color": "#ef4444"},
    {"name": "Pendidikan",         "icon": "📚", "color": "#06b6d4"},
    {"name": "Pakaian",            "icon": "👕", "color": "#f97316"},
    {"name": "Rumah Tangga",       "icon": "🏠", "color": "#84cc16"},
    {"name": "Lain-lain",          "icon": "📦", "color": "#6b7280"},
]

# 5 Metode Pembayaran Default
DEFAULT_PAYMENT_METHODS = [
    {"name": "Tunai",         "icon": "💵"},
    {"name": "Debit",         "icon": "💳"},
    {"name": "Kredit",        "icon": "🏦"},
    {"name": "E-Wallet",      "icon": "📱"},
    {"name": "Transfer Bank", "icon": "🏧"},
]


async def seed_categories(db: AsyncSession) -> int:
    """Seed kategori default jika belum ada. Return jumlah yang ditambahkan."""
    result = await db.execute(
        select(func.count()).select_from(Category).where(Category.is_default == 1)
    )
    count = result.scalar()
    if count > 0:
        return 0

    added = 0
    for cat in DEFAULT_CATEGORIES:
        category = Category(
            user_id=None,
            name=cat["name"],
            icon=cat["icon"],
            color=cat["color"],
            is_default=1,
            is_active=1,
        )
        db.add(category)
        added += 1

    await db.flush()
    return added


async def seed_payment_methods(db: AsyncSession) -> int:
    """Seed metode pembayaran default jika belum ada. Return jumlah yang ditambahkan."""
    result = await db.execute(
        select(func.count()).select_from(PaymentMethod)
    )
    count = result.scalar()
    if count > 0:
        return 0

    added = 0
    for pm in DEFAULT_PAYMENT_METHODS:
        method = PaymentMethod(
            name=pm["name"],
            icon=pm["icon"],
            is_default=1,
            is_active=1,
        )
        db.add(method)
        added += 1

    await db.flush()
    return added


async def seed_all(db: AsyncSession) -> dict:
    """Seed semua data default. Return info jumlah yang ditambahkan."""
    cats = await seed_categories(db)
    pms = await seed_payment_methods(db)
    return {"categories_added": cats, "payment_methods_added": pms}
