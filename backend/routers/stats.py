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
    annual_summary_stats,
    generate_weekly_summary,
    get_cash_flow_forecast,
    get_daily_trend,
    get_dashboard,
    get_monthly_comparison,
    get_monthly_stats,
    get_period_comparison,
    get_sankey_data,
    get_spending_pace,
    get_stats_by_category,
)

router = APIRouter(prefix="/api/stats", tags=["Stats"])


@router.get("/summary", name="api_dashboard")
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


@router.get("/spending-pace")
async def spending_pace(
    request: Request,
    month: int | None = Query(None, ge=1, le=12, description="Bulan (default: sekarang)"),
    year: int | None = Query(None, description="Tahun (default: sekarang)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Spending pace: rata-rata harian, proyeksi, perbandingan budget."""
    result = await get_spending_pace(db, current_user.id, month, year)

    # HTMX: return HTML fragment
    if request.headers.get("HX-Request") == "true":
        from ..main import templates
        return templates.TemplateResponse(
            request,
            "stats/partials/spending_pace.html",
            {"pace": result},
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


@router.get("/weekly-summary")
async def weekly_summary(
    request: Request,
    force: bool = Query(False, description="Force regenerate summary"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Ringkasan mingguan: total, breakdown kategori, perbandingan minggu lalu."""
    result = await generate_weekly_summary(db, current_user.id, force=force)

    # HTMX: return HTML fragment
    if request.headers.get("HX-Request") == "true":
        from ..main import templates
        return templates.TemplateResponse(
            request,
            "stats/partials/weekly_summary.html",
            {"summary": result},
        )

    return StandardResponse(
        status="success",
        data=result,
    ).model_dump()


@router.get("/period-comparison")
async def period_comparison(
    request: Request,
    period: str = Query("month", description="'month' atau 'week'"),
    compare: str = Query("previous", description="'previous' atau 'average'"),
    anomaly_threshold: float = Query(20.0, ge=0, description="Threshold % untuk anomaly detection"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Period-over-Period comparison: analisis tren vs periode sebelumnya."""
    result = await get_period_comparison(
        db, current_user.id, period=period, compare=compare, anomaly_threshold=anomaly_threshold
    )

    # HTMX: return HTML fragment
    if request.headers.get("HX-Request") == "true":
        from ..main import templates
        return templates.TemplateResponse(
            request,
            "stats/partials/period_comparison.html",
            {"comparison": result},
        )

    return StandardResponse(
        status="success",
        data=result,
    ).model_dump()


@router.get("/annual-summary")
async def annual_summary(
    request: Request,
    year: int | None = Query(None, description="Tahun (YYYY), default: tahun sekarang"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Year-End Financial Summary — laporan keuangan tahunan otomatis."""
    result = await annual_summary_stats(db, current_user.id, year=year)

    # HTMX: return HTML fragment
    if request.headers.get("HX-Request") == "true":
        from ..main import templates
        return templates.TemplateResponse(
            request,
            "stats/partials/annual_summary.html",
            {"summary": result},
        )

    return StandardResponse(
        status="success",
        data=result,
    ).model_dump()


@router.get("/cash-flow-forecast")
async def cash_flow_forecast(
    request: Request,
    safe_balance: int | None = Query(None, description="Safe balance threshold (Rupiah) untuk warning"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Cash Flow Forecast — Prediksi saldo & pengeluaran mendatang.

    Proyeksi harian sisa saldo sampai akhir bulan berdasarkan:
    - Weighted average last 3 months daily spending
    - Recurring transactions yang terdeteksi
    - Warning jika forecast menunjukkan saldo akan minus
    """
    result = await get_cash_flow_forecast(db, current_user.id, safe_balance=safe_balance)

    # HTMX: return HTML fragment
    if request.headers.get("HX-Request") == "true":
        from ..main import templates
        return templates.TemplateResponse(
            request,
            "stats/partials/cash_flow_forecast.html",
            {"forecast": result},
        )

    return StandardResponse(
        status="success",
        data=result,
    ).model_dump()


@router.get("/sankey")
async def sankey(
    request: Request,
    year: int | None = Query(None, description="Tahun (YYYY), default: tahun sekarang"),
    month: int | None = Query(None, ge=1, le=12, description="Bulan (1-12), default: bulan sekarang"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Sankey diagram: aliran Pemasukan → Kategori → Subkategori."""
    result = await get_sankey_data(db, current_user.id, year=year, month=month)

    # HTMX: return HTML fragment
    if request.headers.get("HX-Request") == "true":
        from ..main import templates
        return templates.TemplateResponse(
            request,
            "stats/partials/sankey.html",
            {"sankey": result},
        )

    return StandardResponse(
        status="success",
        data=result,
    ).model_dump()
