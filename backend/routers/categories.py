"""
Router untuk modul kategori: CRUD, toggle.
"""

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import User
from ..schemas.auth import StandardResponse
from ..schemas.category import CategoryCreate, CategoryUpdate
from ..services.auth_service import get_current_user
from ..services.category_service import (
    create_category,
    delete_category,
    list_categories,
    toggle_category,
    update_category,
)

router = APIRouter(prefix="/api/categories", tags=["Categories"])


@router.get("")
async def list_cat(
    request: Request,
    include_inactive: bool = Query(False, description="Sertakan kategori non-aktif"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List kategori (default + kustom user)."""
    categories = await list_categories(db, current_user.id, include_inactive)
    return StandardResponse(
        status="success",
        data={"categories": categories},
    ).model_dump()


@router.post("", status_code=201)
async def create_cat(
    data: CategoryCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Buat kategori kustom."""
    result = await create_category(db, current_user.id, data)
    await db.commit()

    return StandardResponse(
        status="success",
        data=result,
        message="Kategori berhasil ditambahkan",
    ).model_dump()


@router.put("/{cat_id}")
async def update_cat(
    cat_id: int,
    data: CategoryUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Edit kategori (hanya kustom)."""
    result = await update_category(db, cat_id, current_user.id, data)
    await db.commit()

    return StandardResponse(
        status="success",
        data=result,
        message="Kategori berhasil diperbarui",
    ).model_dump()


@router.delete("/{cat_id}")
async def delete_cat(
    cat_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Hapus kategori kustom."""
    await delete_category(db, cat_id, current_user.id)
    await db.commit()

    return StandardResponse(
        status="success",
        message="Kategori berhasil dihapus",
    ).model_dump()


@router.patch("/{cat_id}/toggle")
async def toggle_cat(
    cat_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Toggle aktif/nonaktif kategori."""
    result = await toggle_category(db, cat_id, current_user.id)
    await db.commit()

    status_text = "ditampilkan" if result["is_active"] else "disembunyikan"
    return StandardResponse(
        status="success",
        data=result,
        message=f"Kategori {status_text}",
    ).model_dump()
