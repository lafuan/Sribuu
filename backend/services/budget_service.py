"""
Service layer untuk CRUD budget bulanan.
"""

import calendar
from datetime import date

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy.orm import joinedload

from ..models import Budget, Category, Transaction
from ..schemas.budget import BudgetCreate, BudgetUpdate


async def _get_budget_or_404(
    db: AsyncSession, budget_id: int, user_id: int
) -> Budget:
    """Dapatkan budget by ID, validasi kepemilikan."""
    result = await db.execute(
        select(Budget).where(Budget.id == budget_id)
    )
    budget = result.scalar_one_or_none()
    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "status": "error",
                "data": None,
                "message": "Budget tidak ditemukan",
                "errors": None,
            },
        )

    if budget.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "status": "error",
                "data": None,
                "message": "Anda tidak memiliki akses ke budget ini",
                "errors": None,
            },
        )

    return budget


async def _budget_to_response(budget: Budget, spent: int = 0) -> dict:
    """Konversi Budget model + spent ke dict response."""
    percentage = (spent / budget.amount * 100) if budget.amount > 0 else 0.0
    return {
        "id": budget.id,
        "category_id": budget.category_id,
        "category_name": budget.category.name if budget.category else "",
        "category_icon": budget.category.icon if budget.category else "",
        "category_color": budget.category.color if budget.category else "",
        "month": budget.month,
        "year": budget.year,
        "amount": budget.amount,
        "spent": spent,
        "percentage": round(percentage, 2),
    }


async def _get_spent_for_category(
    db: AsyncSession, user_id: int, category_id: int, month: int, year: int
) -> int:
    """Hitung total pengeluaran untuk kategori tertentu di bulan/tahun tertentu."""
    _, last_day = calendar.monthrange(year, month)
    start_date = date(year, month, 1)
    end_date = date(year, month, last_day)

    result = await db.execute(
        select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.user_id == user_id,
            Transaction.category_id == category_id,
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date <= end_date,
        )
    )
    return result.scalar() or 0


async def _get_spending_map(
    db: AsyncSession, user_id: int, month: int, year: int
) -> dict[int, int]:
    """Dapatkan mapping category_id -> total spent untuk bulan/tahun tertentu."""
    _, last_day = calendar.monthrange(year, month)
    start_date = date(year, month, 1)
    end_date = date(year, month, last_day)

    result = await db.execute(
        select(
            Transaction.category_id,
            func.coalesce(func.sum(Transaction.amount), 0).label("total_spent"),
        )
        .where(
            Transaction.user_id == user_id,
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date <= end_date,
        )
        .group_by(Transaction.category_id)
    )
    return {row.category_id: int(row.total_spent) for row in result.all()}


async def list_budgets(
    db: AsyncSession, user_id: int, month: int, year: int
) -> list[dict]:
    """List semua budget user untuk bulan/tahun tertentu, lengkap dengan spending."""
    result = await db.execute(
        select(Budget)
        .options(joinedload(Budget.category))
        .where(
            Budget.user_id == user_id,
            Budget.month == month,
            Budget.year == year,
        )
        .order_by(Budget.category_id)
    )
    budgets = list(result.unique().scalars().all())

    if not budgets:
        return []

    spending_map = await _get_spending_map(db, user_id, month, year)

    result_list = []
    for budget in budgets:
        spent = spending_map.get(budget.category_id, 0)
        result_list.append(await _budget_to_response(budget, spent))

    return result_list


async def create_budget(
    db: AsyncSession, user_id: int, data: BudgetCreate
) -> dict:
    """Buat budget baru untuk satu kategori di bulan/tahun tertentu."""
    # Validasi kategori milik user (default boleh)
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

    # Validasi akses kategori
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

    # Cek duplikasi: budget per kategori per bulan cuma 1
    result = await db.execute(
        select(Budget).where(
            Budget.user_id == user_id,
            Budget.category_id == data.category_id,
            Budget.month == data.month,
            Budget.year == data.year,
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "status": "error",
                "data": None,
                "message": "Budget untuk kategori ini di bulan tersebut sudah ada",
                "errors": {"category_id": ["Budget sudah ada untuk kategori dan bulan ini"]},
            },
        )

    budget = Budget(
        user_id=user_id,
        category_id=data.category_id,
        month=data.month,
        year=data.year,
        amount=data.amount,
    )
    db.add(budget)
    await db.flush()
    await db.refresh(budget, ["category"])

    # Hitung spent untuk response
    spent = await _get_spent_for_category(db, user_id, data.category_id, data.month, data.year)

    return await _budget_to_response(budget, spent)


async def update_budget_amount(
    db: AsyncSession, budget_id: int, user_id: int, data: BudgetUpdate
) -> dict:
    """Update amount budget."""
    budget = await _get_budget_or_404(db, budget_id, user_id)

    budget.amount = data.amount
    await db.flush()
    await db.refresh(budget, ["category"])

    # Hitung spent untuk response
    spent = await _get_spent_for_category(db, user_id, budget.category_id, budget.month, budget.year)

    return await _budget_to_response(budget, spent)


async def delete_budget(
    db: AsyncSession, budget_id: int, user_id: int
) -> None:
    """Hapus budget (hard delete)."""
    budget = await _get_budget_or_404(db, budget_id, user_id)
    await db.delete(budget)
    await db.flush()


async def get_budgets_summary(
    db: AsyncSession, user_id: int, month: int, year: int
) -> list[dict]:
    """Ambil semua budget user untuk bulan itu, beserta total pengeluaran per kategori.

    Format response: id, category_id, category_name, category_icon, category_color,
    month, year, amount (budget limit), spent (total transaksi), percentage.
    """
    return await list_budgets(db, user_id, month, year)
