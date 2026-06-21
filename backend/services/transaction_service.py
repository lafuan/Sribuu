"""
Service layer untuk CRUD transaksi dengan filter, search, dan pagination.
"""

import math
from datetime import date, datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from ..models import Category, PaymentMethod, Transaction
from ..schemas.transaction import (
    CategoryBrief,
    PaginationInfo,
    PaymentMethodBrief,
    TransactionCreate,
    TransactionListResponse,
    TransactionResponse,
    TransactionSummary,
    TransactionUpdate,
)
from ..utils.formatting import (
    format_date_id_short,
    format_datetime_id,
    format_rupiah,
    parse_tags,
)

WIB = timezone(timedelta(hours=7))


def _today_wib() -> date:
    """Tanggal hari ini di WIB."""
    return datetime.now(WIB).date()


def _build_transaction_response(tx, cat, pm) -> TransactionResponse:
    """Bangun TransactionResponse dari model + relasi."""
    # Build attachment URL if exists
    attachment_url = None
    if tx.attachment_path:
        # attachment_path format: uploads/{user_id}/{tx_id}.{ext}
        attachment_url = f"/api/transactions/{tx.id}/attachment"
    return TransactionResponse(
        id=tx.id,
        amount=tx.amount,
        amount_formatted=format_rupiah(tx.amount),
        notes=tx.notes,
        tags=parse_tags(tx.notes),
        transaction_date=tx.transaction_date.isoformat() if tx.transaction_date else None,
        transaction_date_formatted=format_date_id_short(tx.transaction_date) if tx.transaction_date else None,
        category=CategoryBrief(
            id=cat.id, name=cat.name, icon=cat.icon
        ) if cat else None,
        payment_method=PaymentMethodBrief(
            id=pm.id, name=pm.name, icon=pm.icon
        ) if pm else None,
        attachment_url=attachment_url,
        created_at=format_datetime_id(tx.created_at),
        updated_at=format_datetime_id(tx.updated_at),
    )


async def create_transaction(
    db: AsyncSession, user_id: int, data: TransactionCreate
) -> dict:
    """Buat transaksi baru."""
    # Validasi kategori
    result = await db.execute(
        select(Category).where(
            Category.id == data.category_id,
            Category.is_active == 1,
            or_(Category.user_id == user_id, Category.user_id.is_(None)),
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

    tx_date = data.transaction_date or _today_wib()

    tx = Transaction(
        user_id=user_id,
        category_id=data.category_id,
        payment_method_id=data.payment_method_id,
        amount=data.amount,
        notes=data.notes,
        transaction_date=tx_date,
    )
    db.add(tx)
    await db.flush()
    await db.refresh(tx)

    return _build_transaction_response(tx, category, payment_method).model_dump()


async def get_transaction_by_id(
    db: AsyncSession, tx_id: int, user_id: int
) -> Transaction:
    """Dapatkan transaksi by ID, validasi kepemilikan."""
    result = await db.execute(
        select(Transaction)
        .options(joinedload(Transaction.category), joinedload(Transaction.payment_method))
        .where(Transaction.id == tx_id)
    )
    tx = result.scalar_one_or_none()
    if not tx:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "status": "error",
                "data": None,
                "message": "Transaksi tidak ditemukan",
                "errors": None,
            },
        )
    if tx.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "status": "error",
                "data": None,
                "message": "Anda tidak memiliki akses ke transaksi ini",
                "errors": None,
            },
        )
    return tx


async def get_transaction_detail(
    db: AsyncSession, tx_id: int, user_id: int
) -> dict:
    """Dapatkan detail transaksi."""
    tx = await get_transaction_by_id(db, tx_id, user_id)
    return _build_transaction_response(tx, tx.category, tx.payment_method).model_dump()


async def update_transaction(
    db: AsyncSession, tx_id: int, user_id: int, data: TransactionUpdate
) -> dict:
    """Update transaksi."""
    tx = await get_transaction_by_id(db, tx_id, user_id)

    # Validasi kategori baru
    result = await db.execute(
        select(Category).where(
            Category.id == data.category_id,
            Category.is_active == 1,
            or_(Category.user_id == user_id, Category.user_id.is_(None)),
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

    # Validasi payment method
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

    tx.amount = data.amount
    tx.category_id = data.category_id
    tx.transaction_date = data.transaction_date
    tx.payment_method_id = data.payment_method_id
    tx.notes = data.notes
    await db.flush()
    await db.refresh(tx)

    return _build_transaction_response(tx, category, payment_method).model_dump()


async def delete_transaction(
    db: AsyncSession, tx_id: int, user_id: int
) -> None:
    """Hapus transaksi (hard delete)."""
    tx = await get_transaction_by_id(db, tx_id, user_id)
    await db.delete(tx)
    await db.flush()


async def list_transactions(
    db: AsyncSession,
    user_id: int,
    date_from: date | None = None,
    date_to: date | None = None,
    category_id: int | None = None,
    payment_method_id: int | None = None,
    search: str | None = None,
    tag: str | None = None,
    page: int = 1,
    per_page: int = 25,
) -> dict:
    """List transaksi dengan filter, search, dan pagination."""

    # Batasi per_page
    per_page = min(per_page, 100)
    if per_page < 1:
        per_page = 25

    # Bangun base query
    conditions = [Transaction.user_id == user_id]

    if date_from:
        conditions.append(Transaction.transaction_date >= date_from)
    if date_to:
        conditions.append(Transaction.transaction_date <= date_to)
    if category_id:
        conditions.append(Transaction.category_id == category_id)
    if payment_method_id:
        conditions.append(Transaction.payment_method_id == payment_method_id)
    if search:
        conditions.append(Transaction.notes.ilike(f"%{search}%"))
    if tag:
        conditions.append(Transaction.notes.ilike(f"%#{tag}%"))
    where_clause = and_(*conditions)

    # Hitung total (untuk pagination dan summary)
    count_query = select(func.count()).select_from(Transaction).where(where_clause)
    total_result = await db.execute(count_query)
    total_items = total_result.scalar()

    # Hitung total amount
    sum_query = select(func.coalesce(func.sum(Transaction.amount), 0)).where(where_clause)
    sum_result = await db.execute(sum_query)
    total_amount = sum_result.scalar() or 0

    # Pagination
    total_pages = math.ceil(total_items / per_page) if total_items > 0 else 0
    offset = (page - 1) * per_page

    # Query data dengan join
    query = (
        select(Transaction)
        .options(joinedload(Transaction.category), joinedload(Transaction.payment_method))
        .where(where_clause)
        .order_by(Transaction.transaction_date.desc(), Transaction.id.desc())
        .offset(offset)
        .limit(per_page)
    )
    result = await db.execute(query)
    transactions = result.unique().scalars().all()

    tx_list = [
        _build_transaction_response(tx, tx.category, tx.payment_method).model_dump()
        for tx in transactions
    ]

    pagination = PaginationInfo(
        page=page,
        per_page=per_page,
        total_items=total_items,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1,
    )

    summary = TransactionSummary(
        total_amount=total_amount,
        total_amount_formatted=format_rupiah(total_amount),
        total_filtered=total_items,
    )

    return TransactionListResponse(
        transactions=tx_list,
        pagination=pagination,
        summary=summary,
    ).model_dump()


async def get_transactions_for_export(
    db: AsyncSession,
    user_id: int,
    date_from: date | None = None,
    date_to: date | None = None,
    category_id: int | None = None,
    payment_method_id: int | None = None,
    search: str | None = None,
    tag: str | None = None,
) -> list[Transaction]:
    """Dapatkan semua transaksi (tanpa pagination) untuk export."""
    conditions = [Transaction.user_id == user_id]

    if date_from:
        conditions.append(Transaction.transaction_date >= date_from)
    if date_to:
        conditions.append(Transaction.transaction_date <= date_to)
    if category_id:
        conditions.append(Transaction.category_id == category_id)
    if payment_method_id:
        conditions.append(Transaction.payment_method_id == payment_method_id)
    if search:
        conditions.append(Transaction.notes.ilike(f"%{search}%"))
    if tag:
        conditions.append(Transaction.notes.ilike(f"%#{tag}%"))

    where_clause = and_(*conditions)

    query = (
        select(Transaction)
        .options(joinedload(Transaction.category), joinedload(Transaction.payment_method))
        .where(where_clause)
        .order_by(Transaction.transaction_date.desc(), Transaction.id.desc())
    )
    result = await db.execute(query)
    return list(result.unique().scalars().all())
