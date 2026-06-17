"""
Router untuk modul budget: CRUD + summary.
"""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import User
from ..schemas.auth import StandardResponse
from ..schemas.budget import BudgetCreate, BudgetUpdate
from ..services.auth_service import get_current_user
from ..services.budget_service import (
    create_budget,
    delete_budget,
    get_budgets_summary,
    list_budgets,
    update_budget_amount,
)

WIB = timezone(timedelta(hours=7))

router = APIRouter(prefix="/api/budgets", tags=["Budgets"])


def _now_wib() -> datetime:
    """Waktu sekarang di WIB."""
    return datetime.now(WIB)


@router.get("")
async def list_bgt(
    request: Request,
    month: int | None = Query(None, ge=1, le=12, description="Bulan (default: bulan sekarang)"),
    year: int | None = Query(None, description="Tahun (default: tahun sekarang)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List budget untuk bulan/tahun tertentu."""
    now = _now_wib()
    month = month or now.month
    year = year or now.year

    budgets = await list_budgets(db, current_user.id, month, year)
    return StandardResponse(
        status="success",
        data={"budgets": budgets},
    ).model_dump()


@router.post("", status_code=201)
async def create_bgt(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Buat budget baru."""

    # Detect HTMX form-data vs JSON
    if request.headers.get("Content-Type", "").startswith("application/x-www-form-urlencoded") or request.headers.get("HX-Request") == "true":
        form = await request.form()
        data = BudgetCreate(
            category_id=int(str(form.get("category_id", "0"))),
            amount=int(str(form.get("amount", "0"))),
            month=int(str(form.get("month", "0"))),
            year=int(str(form.get("year", "0"))),
        )
    else:
        body = await request.json()
        data = BudgetCreate(**body)

    result = await create_budget(db, current_user.id, data)
    await db.commit()

    # HTMX: return updated budget list for the current month
    if request.headers.get("HX-Request") == "true":
        now = _now_wib()
        budgets = await list_budgets(db, current_user.id, now.month, now.year)
        from ..main import templates as tpl

        # juga butuh categories, current_month, current_year buat modal
        from ..services.category_service import list_categories as list_cats
        categories = await list_cats(db, current_user.id)
        return tpl.TemplateResponse(
            request, "budgets/list.html",
            {
                "budgets": budgets,
                "categories": categories,
                "current_month": now.month,
                "current_year": now.year,
            },
        )

    return StandardResponse(
        status="success",
        data=result,
        message="Budget berhasil ditambahkan",
    ).model_dump()


@router.put("/{budget_id}")
async def update_bgt(
    budget_id: int,
    data: BudgetUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update amount budget."""
    result = await update_budget_amount(db, budget_id, current_user.id, data)
    await db.commit()

    return StandardResponse(
        status="success",
        data=result,
        message="Budget berhasil diperbarui",
    ).model_dump()


@router.delete("/{budget_id}")
async def delete_bgt(
    budget_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Hapus budget."""
    await delete_budget(db, budget_id, current_user.id)
    await db.commit()

    return StandardResponse(
        status="success",
        message="Budget berhasil dihapus",
    ).model_dump()


@router.get("/summary")
async def summary_bgt(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return budgets + spending per category for current month (for dashboard)."""
    now = _now_wib()
    budgets = await get_budgets_summary(db, current_user.id, now.month, now.year)

    # HTMX request: return HTML fragment
    if request.headers.get("HX-Request") == "true":
        from ..main import templates
        return templates.TemplateResponse(
            request,
            "budgets/partials/summary.html",
            {"budgets": budgets, "current_user": current_user},
        )

    return StandardResponse(
        status="success",
        data={"budgets": budgets},
    ).model_dump()
