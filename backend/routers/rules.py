"""
Router untuk Rule Engine — CRUD rules + apply.
"""
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import User
from ..schemas.auth import StandardResponse
from ..schemas.rule import RuleCreate, RuleUpdate
from ..services.auth_service import get_current_user
from ..services.rule_service import (
    apply_rules_to_existing,
    create_rule,
    delete_rule,
    list_rules,
    update_rule,
)

router = APIRouter(prefix="/api/rules", tags=["Rules"])


@router.get("")
async def list_r(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List semua rule user."""
    rules = await list_rules(db, current_user.id)
    return StandardResponse(status="success", data={"rules": rules}).model_dump()


@router.post("", status_code=201)
async def create_r(
    data: RuleCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Buat rule baru."""
    result = await create_rule(db, current_user.id, data)
    await db.commit()
    return StandardResponse(
        status="success", data=result, message="Rule berhasil dibuat"
    ).model_dump()


@router.put("/{rule_id}")
async def update_r(
    rule_id: int,
    data: RuleUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update rule."""
    result = await update_rule(db, rule_id, current_user.id, data)
    await db.commit()
    return StandardResponse(
        status="success", data=result, message="Rule berhasil diperbarui"
    ).model_dump()


@router.delete("/{rule_id}")
async def delete_r(
    rule_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Hapus rule."""
    await delete_rule(db, rule_id, current_user.id)
    await db.commit()
    return StandardResponse(
        status="success", message="Rule berhasil dihapus"
    ).model_dump()


@router.post("/apply")
async def apply_r(
    request: Request,
    days: int = Query(30, ge=1, le=365, description="Hari ke belakang untuk cek ulang"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Jalankan rules ke transaksi yang belum terkategori."""
    result = await apply_rules_to_existing(db, current_user.id, days=days)
    await db.commit()
    return StandardResponse(
        status="success",
        data=result,
        message=f"{result['updated']} dari {result['total_checked']} transaksi ter-update",
    ).model_dump()
