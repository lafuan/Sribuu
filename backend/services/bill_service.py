"""
Service layer untuk CRUD Bill (tagihan) + mark as paid (auto-create transaction).
"""

from datetime import date

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from ..models import Bill, Category, Transaction
from ..schemas.bill import BillCreate, BillUpdate


async def _get_bill_or_404(db: AsyncSession, bill_id: int, user_id: int) -> Bill:
    result = await db.execute(
        select(Bill)
        .options(joinedload(Bill.category))
        .where(Bill.id == bill_id)
    )
    bill = result.scalar_one_or_none()
    if not bill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"status": "error", "message": "Tagihan tidak ditemukan"},
        )
    if bill.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"status": "error", "message": "Akses ditolak"},
        )
    return bill


async def _bill_to_dict(bill: Bill) -> dict:
    return {
        "id": bill.id,
        "name": bill.name,
        "amount": bill.amount,
        "due_date": bill.due_date.isoformat() if bill.due_date else None,
        "frequency": bill.frequency,
        "is_paid": bool(bill.is_paid),
        "category_id": bill.category_id,
        "category_name": bill.category.name if bill.category else "",
        "category_icon": bill.category.icon if bill.category else "",
        "paid_transaction_id": bill.paid_transaction_id,
        "created_at": bill.created_at.isoformat() if bill.created_at else None,
    }


async def list_bills(
    db: AsyncSession, user_id: int,
    is_paid: bool | None = None,
    limit: int = 50,
) -> list[dict]:
    stmt = (
        select(Bill)
        .options(joinedload(Bill.category))
        .where(Bill.user_id == user_id)
    )
    if is_paid is not None:
        stmt = stmt.where(Bill.is_paid == (1 if is_paid else 0))
    stmt = stmt.order_by(Bill.due_date.asc()).limit(limit)
    result = await db.execute(stmt)
    bills = list(result.unique().scalars().all())
    return [await _bill_to_dict(b) for b in bills]


async def get_upcoming_bills(db: AsyncSession, user_id: int, limit: int = 5) -> list[dict]:
    today = date.today()
    stmt = (
        select(Bill)
        .options(joinedload(Bill.category))
        .where(
            Bill.user_id == user_id,
            Bill.is_paid == 0,
        )
        .order_by(Bill.due_date.asc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    bills = list(result.unique().scalars().all())
    return [
        {
            **await _bill_to_dict(b),
            "is_overdue": b.due_date < today if b.due_date else False,
        }
        for b in bills
    ]


async def create_bill(db: AsyncSession, user_id: int, data: BillCreate) -> dict:
    cat_result = await db.execute(
        select(Category).where(Category.id == data.category_id, Category.is_active == 1)
    )
    category = cat_result.scalar_one_or_none()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"status": "error", "message": "Kategori tidak ditemukan atau tidak aktif"},
        )
    if data.frequency not in ("monthly", "yearly"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"status": "error", "message": "Frekuensi harus 'monthly' atau 'yearly'"},
        )
    bill = Bill(
        user_id=user_id,
        category_id=data.category_id,
        name=data.name,
        amount=data.amount,
        due_date=data.due_date,
        frequency=data.frequency,
    )
    db.add(bill)
    await db.flush()
    await db.refresh(bill, ["category"])
    return await _bill_to_dict(bill)


async def update_bill(db: AsyncSession, bill_id: int, user_id: int, data: BillUpdate) -> dict:
    bill = await _get_bill_or_404(db, bill_id, user_id)
    if data.name is not None:
        bill.name = data.name
    if data.amount is not None:
        bill.amount = data.amount
    if data.due_date is not None:
        bill.due_date = data.due_date
    if data.frequency is not None:
        if data.frequency not in ("monthly", "yearly"):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"status": "error", "message": "Frekuensi harus 'monthly' atau 'yearly'"},
            )
        bill.frequency = data.frequency
    if data.category_id is not None:
        cat_result = await db.execute(
            select(Category).where(Category.id == data.category_id, Category.is_active == 1)
        )
        if not cat_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"status": "error", "message": "Kategori tidak ditemukan"},
            )
        bill.category_id = data.category_id
    await db.flush()
    await db.refresh(bill, ["category"])
    return await _bill_to_dict(bill)


async def delete_bill(db: AsyncSession, bill_id: int, user_id: int) -> None:
    bill = await _get_bill_or_404(db, bill_id, user_id)
    await db.delete(bill)
    await db.flush()


async def mark_as_paid(
    db: AsyncSession, bill_id: int, user_id: int, payment_method_id: int,
) -> dict:
    bill = await _get_bill_or_404(db, bill_id, user_id)
    if bill.is_paid:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"status": "error", "message": "Tagihan sudah lunas"},
        )
    tx = Transaction(
        user_id=user_id,
        category_id=bill.category_id,
        payment_method_id=payment_method_id,
        amount=bill.amount,
        notes=f"Tagihan: {bill.name}",
        transaction_date=bill.due_date,
    )
    db.add(tx)
    await db.flush()
    bill.is_paid = 1
    bill.paid_transaction_id = tx.id
    await db.flush()
    await db.refresh(bill, ["category"])
    return await _bill_to_dict(bill)


async def unmark_paid(db: AsyncSession, bill_id: int, user_id: int) -> dict:
    bill = await _get_bill_or_404(db, bill_id, user_id)
    if not bill.is_paid:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"status": "error", "message": "Tagihan belum lunas"},
        )
    if bill.paid_transaction_id:
        tx_result = await db.execute(
            select(Transaction).where(Transaction.id == bill.paid_transaction_id)
        )
        tx = tx_result.scalar_one_or_none()
        if tx:
            await db.delete(tx)
    bill.is_paid = 0
    bill.paid_transaction_id = None
    await db.flush()
    await db.refresh(bill, ["category"])
    return await _bill_to_dict(bill)
