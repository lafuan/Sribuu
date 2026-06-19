"""Service layer untuk CRUD TransactionTemplate (Favorit Transaksi)."""

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from ..models import Category, PaymentMethod, TransactionTemplate
from ..schemas.template import (
    TransactionTemplateCreate,
    TransactionTemplateResponse,
    TransactionTemplateUpdate,
)
from ..utils.formatting import format_rupiah


def _build_template_response(template, cat, pm) -> TransactionTemplateResponse:
    """Bangun TransactionTemplateResponse dari model + relasi."""
    from ..schemas.transaction import CategoryBrief, PaymentMethodBrief

    return TransactionTemplateResponse(
        id=template.id,
        label=template.label,
        amount=template.amount,
        amount_formatted=format_rupiah(template.amount),
        notes=template.notes,
        sort_order=template.sort_order,
        category=CategoryBrief(
            id=cat.id, name=cat.name, icon=cat.icon
        ) if cat else None,
        payment_method=PaymentMethodBrief(
            id=pm.id, name=pm.name, icon=pm.icon
        ) if pm else None,
        created_at=template.created_at.isoformat() if template.created_at else None,
    )


async def list_templates(
    db: AsyncSession, user_id: int
) -> list[dict]:
    """List semua template milik user, diurutkan berdasarkan sort_order."""
    query = (
        select(TransactionTemplate)
        .options(
            joinedload(TransactionTemplate.category),
            joinedload(TransactionTemplate.payment_method),
        )
        .where(TransactionTemplate.user_id == user_id)
        .order_by(TransactionTemplate.sort_order, TransactionTemplate.id)
    )
    result = await db.execute(query)
    templates = result.unique().scalars().all()

    return [
        _build_template_response(t, t.category, t.payment_method).model_dump()
        for t in templates
    ]


async def create_template(
    db: AsyncSession, user_id: int, data: TransactionTemplateCreate
) -> dict:
    """Buat template transaksi baru."""
    # Validasi kategori
    result = await db.execute(
        select(Category).where(
            Category.id == data.category_id,
            Category.is_active == 1,
        )
    )
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "status": "error",
                "data": None,
                "message": "Kategori tidak ditemukan atau tidak aktif",
                "errors": {"category_id": ["Kategori tidak ditemukan"]},
            },
        )

    # Validasi payment method jika diisi
    payment_method = None
    if data.payment_method_id:
        result = await db.execute(
            select(PaymentMethod).where(
                PaymentMethod.id == data.payment_method_id,
                PaymentMethod.is_active == 1,
            )
        )
        payment_method = result.scalar_one_or_none()
        if not payment_method:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "status": "error",
                    "data": None,
                    "message": "Metode pembayaran tidak ditemukan",
                    "errors": {"payment_method_id": ["Metode pembayaran tidak valid"]},
                },
            )

    template = TransactionTemplate(
        user_id=user_id,
        category_id=data.category_id,
        payment_method_id=data.payment_method_id,
        amount=data.amount,
        notes=data.notes,
        label=data.label,
        sort_order=data.sort_order,
    )
    db.add(template)
    await db.flush()
    await db.refresh(template)

    return _build_template_response(template, category, payment_method).model_dump()


async def update_template(
    db: AsyncSession, template_id: int, user_id: int, data: TransactionTemplateUpdate
) -> dict:
    """Update template transaksi."""
    template = await _get_template(db, template_id, user_id)

    # Validasi kategori baru
    result = await db.execute(
        select(Category).where(
            Category.id == data.category_id,
            Category.is_active == 1,
        )
    )
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "status": "error",
                "data": None,
                "message": "Kategori tidak ditemukan atau tidak aktif",
            },
        )

    payment_method = None
    if data.payment_method_id:
        result = await db.execute(
            select(PaymentMethod).where(
                PaymentMethod.id == data.payment_method_id,
                PaymentMethod.is_active == 1,
            )
        )
        payment_method = result.scalar_one_or_none()
        if not payment_method:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "status": "error",
                    "data": None,
                    "message": "Metode pembayaran tidak ditemukan",
                },
            )

    template.label = data.label
    template.amount = data.amount
    template.category_id = data.category_id
    template.payment_method_id = data.payment_method_id
    template.notes = data.notes
    template.sort_order = data.sort_order
    await db.flush()
    await db.refresh(template)

    return _build_template_response(template, category, payment_method).model_dump()


async def delete_template(
    db: AsyncSession, template_id: int, user_id: int
) -> None:
    """Hapus template transaksi."""
    template = await _get_template(db, template_id, user_id)
    await db.delete(template)
    await db.flush()


async def _get_template(
    db: AsyncSession, template_id: int, user_id: int
) -> TransactionTemplate:
    """Dapatkan template by ID, validasi kepemilikan."""
    result = await db.execute(
        select(TransactionTemplate)
        .options(
            joinedload(TransactionTemplate.category),
            joinedload(TransactionTemplate.payment_method),
        )
        .where(TransactionTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "status": "error",
                "data": None,
                "message": "Template tidak ditemukan",
            },
        )
    if template.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "status": "error",
                "data": None,
                "message": "Anda tidak memiliki akses ke template ini",
            },
        )
    return template
