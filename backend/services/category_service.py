"""
Service layer untuk CRUD kategori.
"""

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Category, Transaction
from ..schemas.category import CategoryCreate, CategoryUpdate


async def _get_category_or_404(
    db: AsyncSession, cat_id: int, user_id: int
) -> Category:
    """Dapatkan kategori by ID, validasi kepemilikan."""
    result = await db.execute(
        select(Category).where(Category.id == cat_id)
    )
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "status": "error",
                "data": None,
                "message": "Kategori tidak ditemukan",
                "errors": None,
            },
        )

    # Kategori default (user_id=NULL) bisa diakses semua user
    if category.user_id is not None and category.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "status": "error",
                "data": None,
                "message": "Anda tidak memiliki akses ke kategori ini",
                "errors": None,
            },
        )

    return category


def _category_to_response(cat: Category, tx_count: int = 0) -> dict:
    """Konversi Category model ke dict response."""
    return {
        "id": cat.id,
        "name": cat.name,
        "icon": cat.icon,
        "color": cat.color,
        "is_default": bool(cat.is_default),
        "is_active": bool(cat.is_active),
        "transaction_count": tx_count,
    }


async def list_categories(
    db: AsyncSession, user_id: int, include_inactive: bool = False
) -> list[dict]:
    """List kategori user (kustom) + default sistem."""
    # Ambil kategori user + default yang aktif
    conditions = [
        or_(Category.user_id == user_id, Category.user_id.is_(None)),
    ]
    if not include_inactive:
        conditions.append(Category.is_active == 1)

    result = await db.execute(
        select(Category).where(*conditions).order_by(Category.is_default.desc(), Category.name)
    )
    categories = result.scalars().all()

    # Hitung transaction count per kategori
    cat_ids = [c.id for c in categories]
    tx_counts = {}
    if cat_ids:
        result = await db.execute(
            select(
                Transaction.category_id,
                func.count(Transaction.id).label("count"),
            )
            .where(
                Transaction.category_id.in_(cat_ids),
                Transaction.user_id == user_id,
            )
            .group_by(Transaction.category_id)
        )
        for row in result.all():
            tx_counts[row.category_id] = row.count

    return [
        _category_to_response(cat, tx_counts.get(cat.id, 0))
        for cat in categories
    ]


async def create_category(
    db: AsyncSession, user_id: int, data: CategoryCreate
) -> dict:
    """Buat kategori kustom untuk user."""
    # Cek duplikasi nama
    result = await db.execute(
        select(Category).where(
            Category.user_id == user_id,
            Category.name == data.name.strip(),
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "status": "error",
                "data": None,
                "message": "Kategori dengan nama ini sudah ada",
                "errors": {"name": ["Nama kategori sudah digunakan"]},
            },
        )

    cat = Category(
        user_id=user_id,
        name=data.name.strip(),
        icon=data.icon,
        color=data.color,
        is_default=0,
        is_active=1,
    )
    db.add(cat)
    await db.flush()
    await db.refresh(cat)

    return _category_to_response(cat, 0)


async def update_category(
    db: AsyncSession, cat_id: int, user_id: int, data: CategoryUpdate
) -> dict:
    """Edit kategori kustom."""
    cat = await _get_category_or_404(db, cat_id, user_id)

    # Hanya kategori kustom yang bisa diedit
    if cat.is_default:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "status": "error",
                "data": None,
                "message": "Kategori default tidak dapat diedit",
                "errors": None,
            },
        )

    # Cek duplikasi nama (kecuali nama sendiri)
    result = await db.execute(
        select(Category).where(
            Category.user_id == user_id,
            Category.name == data.name.strip(),
            Category.id != cat_id,
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "status": "error",
                "data": None,
                "message": "Kategori dengan nama ini sudah ada",
                "errors": {"name": ["Nama kategori sudah digunakan"]},
            },
        )

    cat.name = data.name.strip()
    cat.icon = data.icon
    cat.color = data.color
    await db.flush()
    await db.refresh(cat)

    # Hitung transaction count
    result = await db.execute(
        select(func.count(Transaction.id)).where(
            Transaction.category_id == cat_id,
            Transaction.user_id == user_id,
        )
    )
    tx_count = result.scalar() or 0

    return _category_to_response(cat, tx_count)


async def delete_category(
    db: AsyncSession, cat_id: int, user_id: int
) -> None:
    """Hapus kategori kustom."""
    cat = await _get_category_or_404(db, cat_id, user_id)

    # Kategori default tidak bisa dihapus
    if cat.is_default:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "status": "error",
                "data": None,
                "message": "Kategori default tidak dapat dihapus. Anda dapat menyembunyikannya.",
                "errors": None,
            },
        )

    # Cek apakah kategori masih digunakan transaksi
    result = await db.execute(
        select(func.count(Transaction.id)).where(
            Transaction.category_id == cat_id,
            Transaction.user_id == user_id,
        )
    )
    tx_count = result.scalar() or 0

    if tx_count > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "status": "error",
                "data": {"transaction_count": tx_count},
                "message": f"Kategori sedang digunakan oleh {tx_count} transaksi. Pindahkan atau hapus transaksi terlebih dahulu.",
                "errors": None,
            },
        )

    await db.delete(cat)
    await db.flush()


async def toggle_category(
    db: AsyncSession, cat_id: int, user_id: int
) -> dict:
    """Toggle status aktif/nonaktif kategori."""
    cat = await _get_category_or_404(db, cat_id, user_id)

    cat.is_active = 0 if cat.is_active else 1
    await db.flush()

    return {
        "id": cat.id,
        "name": cat.name,
        "is_active": bool(cat.is_active),
    }
