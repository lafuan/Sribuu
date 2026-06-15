"""
Router untuk modul statistik: dashboard, by-category, daily-trend, monthly.
"""

from datetime import date

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import User
from ..schemas.auth import StandardResponse
from ..services.auth_service import get_current_user
from ..services.stats_service import (
    get_dashboard,
    get_daily_trend,
    get_monthly_comparison,
    get_monthly_stats,
    get_stats_by_category,
)
from ..services.transaction_service import list_transactions

router = APIRouter(prefix="/api/stats", tags=["Stats"])


@router.get("/summary")
async def dashboard(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Dashboard: ringkasan harian, bulanan, top kategori, transaksi terbaru."""
    result = await get_dashboard(db, current_user.id)
    return StandardResponse(
        status="success",
        data=result,
    ).model_dump()


@router.get("/by-category")
async def by_category(
    request: Request,
    date_from: date | None = Query(None, description="Awal rentang"),
    date_to: date | None = Query(None, description="Akhir rentang"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Distribusi pengeluaran per kategori (untuk pie chart)."""
    result = await get_stats_by_category(
        db, current_user.id, date_from, date_to
    )
    return StandardResponse(
        status="success",
        data=result,
    ).model_dump()


@router.get("/daily-trend")
async def daily_trend(
    request: Request,
    date_from: date | None = Query(None, description="Awal rentang"),
    date_to: date | None = Query(None, description="Akhir rentang"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Tren pengeluaran harian (untuk bar chart)."""
    result = await get_daily_trend(
        db, current_user.id, date_from, date_to
    )
    return StandardResponse(
        status="success",
        data=result,
    ).model_dump()


@router.get("/monthly")
async def monthly(
    request: Request,
    year: int | None = Query(None, description="Tahun (YYYY)"),
    month: int | None = Query(None, ge=1, le=12, description="Bulan (1-12)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Statistik bulanan detail dengan perbandingan."""
    result = await get_monthly_stats(
        db, current_user.id, year, month
    )
    return StandardResponse(
        status="success",
        data=result,
    ).model_dump()


@router.get("/monthly-comparison")
async def monthly_comparison(
    request: Request,
    months: int = Query(3, ge=1, le=12, description="Jumlah bulan ke belakang"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Perbandingan multi-bulan."""
    result = await get_monthly_comparison(
        db, current_user.id, months
    )
    return StandardResponse(
        status="success",
        data=result,
    ).model_dump()
