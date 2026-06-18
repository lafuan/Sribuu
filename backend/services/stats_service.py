"""
Service layer untuk statistik: dashboard, by-category, daily-trend, monthly.
"""

from datetime import date, datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from ..models import Category, Transaction
from ..utils.formatting import (
    format_rupiah,
    get_day_name_id,
    get_month_label,
)

WIB = timezone(timedelta(hours=7))


def _today_wib() -> date:
    return datetime.now(WIB).date()


def _start_of_month(year: int, month: int) -> date:
    return date(year, month, 1)


def _end_of_month(year: int, month: int) -> date:
    if month == 12:
        return date(year, month, 31)
    return date(year, month + 1, 1) - timedelta(days=1)


async def get_dashboard(
    db: AsyncSession, user_id: int
) -> dict:
    """Data dashboard: ringkasan hari ini, bulan ini, top kategori, transaksi terbaru."""
    today = _today_wib()
    month_start = today.replace(day=1)

    # --- Hari ini ---
    result = await db.execute(
        select(
            func.coalesce(func.sum(Transaction.amount), 0),
            func.count(Transaction.id),
        ).where(
            Transaction.user_id == user_id,
            Transaction.transaction_date == today,
        )
    )
    today_amount, today_count = result.one()

    # --- Bulan ini ---
    result = await db.execute(
        select(
            func.coalesce(func.sum(Transaction.amount), 0),
            func.count(Transaction.id),
        ).where(
            Transaction.user_id == user_id,
            Transaction.transaction_date >= month_start,
            Transaction.transaction_date <= today,
        )
    )
    month_amount, month_count = result.one()

    # --- Top kategori bulan ini ---
    result = await db.execute(
        select(
            Category.id,
            Category.name,
            Category.icon,
            Category.color,
            func.sum(Transaction.amount).label("total"),
            func.count(Transaction.id).label("count"),
        )
        .join(Transaction, Transaction.category_id == Category.id)
        .where(
            Transaction.user_id == user_id,
            Transaction.transaction_date >= month_start,
            Transaction.transaction_date <= today,
        )
        .group_by(Category.id)
        .order_by(func.sum(Transaction.amount).desc())
        .limit(3)
    )
    top_categories = []
    for row in result.all():
        percentage = (row.total / month_amount * 100) if month_amount > 0 else 0
        top_categories.append({
            "category": {
                "id": row.id,
                "name": row.name,
                "icon": row.icon,
                "color": row.color,
            },
            "total_amount": row.total,
            "total_amount_formatted": format_rupiah(row.total),
            "percentage": round(percentage, 1),
        })

    # --- 5 transaksi terbaru ---
    from .transaction_service import _build_transaction_response

    result = await db.execute(
        select(Transaction)
        .options(joinedload(Transaction.category), joinedload(Transaction.payment_method))
        .where(Transaction.user_id == user_id)
        .order_by(Transaction.transaction_date.desc(), Transaction.id.desc())
        .limit(5)
    )
    recent_tx = result.unique().scalars().all()
    recent = [
        _build_transaction_response(tx, tx.category, tx.payment_method).model_dump()
        for tx in recent_tx
    ]

    return {
        "today": {
            "total_amount": today_amount,
            "total_amount_formatted": format_rupiah(today_amount),
            "transaction_count": today_count,
        },
        "this_month": {
            "total_amount": month_amount,
            "total_amount_formatted": format_rupiah(month_amount),
            "transaction_count": month_count,
            "month_label": get_month_label(today.year, today.month),
        },
        "top_categories": top_categories,
        "recent_transactions": recent,
    }


async def get_stats_by_category(
    db: AsyncSession,
    user_id: int,
    date_from: date | None = None,
    date_to: date | None = None,
) -> dict:
    """Distribusi pengeluaran per kategori."""
    today = _today_wib()
    if not date_from:
        date_from = today.replace(day=1)
    if not date_to:
        date_to = today

    result = await db.execute(
        select(
            Category.id,
            Category.name,
            Category.icon,
            Category.color,
            func.sum(Transaction.amount).label("total"),
            func.count(Transaction.id).label("count"),
        )
        .join(Transaction, Transaction.category_id == Category.id)
        .where(
            Transaction.user_id == user_id,
            Transaction.transaction_date >= date_from,
            Transaction.transaction_date <= date_to,
        )
        .group_by(Category.id)
        .order_by(func.sum(Transaction.amount).desc())
    )

    rows = result.all()
    total_all = sum(row.total for row in rows)

    categories = []
    for row in rows:
        percentage = (row.total / total_all * 100) if total_all > 0 else 0
        categories.append({
            "category": {
                "id": row.id,
                "name": row.name,
                "icon": row.icon,
                "color": row.color,
            },
            "total_amount": row.total,
            "total_amount_formatted": format_rupiah(row.total),
            "percentage": round(percentage, 1),
            "transaction_count": row.count,
        })

    return {
        "date_from": date_from.isoformat(),
        "date_to": date_to.isoformat(),
        "total_amount": total_all,
        "total_amount_formatted": format_rupiah(total_all),
        "categories": categories,
    }


async def get_daily_trend(
    db: AsyncSession,
    user_id: int,
    date_from: date | None = None,
    date_to: date | None = None,
) -> dict:
    """Tren pengeluaran harian."""
    today = _today_wib()
    if not date_from:
        date_from = today - timedelta(days=6)  # 7 hari terakhir
    if not date_to:
        date_to = today

    # Query aggregate
    result = await db.execute(
        select(
            Transaction.transaction_date,
            func.sum(Transaction.amount).label("total"),
            func.count(Transaction.id).label("count"),
        )
        .where(
            Transaction.user_id == user_id,
            Transaction.transaction_date >= date_from,
            Transaction.transaction_date <= date_to,
        )
        .group_by(Transaction.transaction_date)
        .order_by(Transaction.transaction_date)
    )
    db_data = {row.transaction_date: (row.total, row.count) for row in result.all()}

    # Isi semua tanggal dalam rentang (termasuk tanpa transaksi)
    daily = []
    max_amount = 0
    current = date_from
    while current <= date_to:
        total, count = db_data.get(current, (0, 0))
        max_amount = max(max_amount, total)
        daily.append({
            "date": current.isoformat(),
            "date_formatted": f"{current.day:02d}/{current.month:02d}",
            "day_name": get_day_name_id(current),
            "total_amount": total,
            "total_amount_formatted": format_rupiah(total),
            "transaction_count": count,
        })
        current += timedelta(days=1)

    return {
        "date_from": date_from.isoformat(),
        "date_to": date_to.isoformat(),
        "daily": daily,
        "max_amount": max_amount,
    }


async def get_monthly_stats(
    db: AsyncSession,
    user_id: int,
    year: int | None = None,
    month: int | None = None,
) -> dict:
    """Statistik bulanan detail dengan perbandingan bulan sebelumnya."""
    today = _today_wib()
    if not year:
        year = today.year
    if not month:
        month = today.month

    month_start = _start_of_month(year, month)
    month_end = _end_of_month(year, month)

    # Total bulan ini
    result = await db.execute(
        select(
            func.coalesce(func.sum(Transaction.amount), 0),
            func.count(Transaction.id),
        )
        .where(
            Transaction.user_id == user_id,
            Transaction.transaction_date >= month_start,
            Transaction.transaction_date <= month_end,
        )
    )
    total_amount, tx_count = result.one()

    # Transaksi tertinggi
    result = await db.execute(
        select(Transaction)
        .options(joinedload(Transaction.category))
        .where(
            Transaction.user_id == user_id,
            Transaction.transaction_date >= month_start,
            Transaction.transaction_date <= month_end,
        )
        .order_by(Transaction.amount.desc())
        .limit(1)
    )
    highest_tx = result.scalar_one_or_none()

    highest = None
    if highest_tx:
        highest = {
            "id": highest_tx.id,
            "amount": highest_tx.amount,
            "amount_formatted": format_rupiah(highest_tx.amount),
            "category": {
                "id": highest_tx.category.id,
                "name": highest_tx.category.name,
                "icon": highest_tx.category.icon,
            } if highest_tx.category else {},
            "transaction_date": highest_tx.transaction_date.isoformat(),
        }

    # Daily average
    days_in_month = (month_end - month_start).days + 1
    daily_avg = total_amount // days_in_month if days_in_month > 0 else 0

    # Perbandingan bulan sebelumnya
    prev_month = month - 1
    prev_year = year
    if prev_month == 0:
        prev_month = 12
        prev_year -= 1

    prev_start = _start_of_month(prev_year, prev_month)
    prev_end = _end_of_month(prev_year, prev_month)

    result = await db.execute(
        select(func.coalesce(func.sum(Transaction.amount), 0))
        .where(
            Transaction.user_id == user_id,
            Transaction.transaction_date >= prev_start,
            Transaction.transaction_date <= prev_end,
        )
    )
    prev_total = result.scalar() or 0

    diff = total_amount - prev_total
    pct_change = round((diff / prev_total * 100), 2) if prev_total > 0 else 0

    comparison = {
        "previous_total": prev_total,
        "previous_total_formatted": format_rupiah(prev_total),
        "difference": diff,
        "difference_formatted": format_rupiah(diff),
        "percentage_change": pct_change,
    }

    return {
        "year": year,
        "month": month,
        "month_label": get_month_label(year, month),
        "total_amount": total_amount,
        "total_amount_formatted": format_rupiah(total_amount),
        "transaction_count": tx_count,
        "daily_average": daily_avg,
        "daily_average_formatted": format_rupiah(daily_avg),
        "highest_transaction": highest,
        "comparison_previous_month": comparison,
    }


async def get_spending_pace(
    db: AsyncSession,
    user_id: int,
    month: int | None = None,
    year: int | None = None,
) -> dict:
    """Hitung spending pace bulan ini: rata-rata harian, proyeksi akhir bulan, perbandingan budget."""
    today = _today_wib()
    if not year:
        year = today.year
    if not month:
        month = today.month

    month_start = _start_of_month(year, month)
    month_end = _end_of_month(year, month)

    # Hari yang sudah berlalu (paling tidak 1)
    days_elapsed = (today - month_start).days + 1
    if days_elapsed < 1:
        days_elapsed = 1
    days_in_month = (month_end - month_start).days + 1

    # Total pengeluaran bulan ini
    result = await db.execute(
        select(func.coalesce(func.sum(Transaction.amount), 0))
        .where(
            Transaction.user_id == user_id,
            Transaction.transaction_date >= month_start,
            Transaction.transaction_date <= today,
        )
    )
    total_spent = result.scalar() or 0

    # Rata-rata per hari
    daily_avg = total_spent // days_elapsed if days_elapsed > 0 else 0

    # Proyeksi akhir bulan
    projected_total = daily_avg * days_in_month

    # Total budget bulan ini (dari semua kategori)
    from ..models import Budget
    result = await db.execute(
        select(func.coalesce(func.sum(Budget.amount), 0))
        .where(
            Budget.user_id == user_id,
            Budget.month == month,
            Budget.year == year,
        )
    )
    total_budget = int(result.scalar() or 0)

    # Pace: berapa % budget yang sudah terpakai vs waktu yang berlalu
    budget_used_pct = round((total_spent / total_budget * 100), 1) if total_budget > 0 else None
    time_elapsed_pct = round((days_elapsed / days_in_month * 100), 1)

    # Apakah pengeluaran sesuai pace? (budget_used_pct <= time_elapsed_pct = on track)
    is_on_track: bool | None = None
    if total_budget > 0 and budget_used_pct is not None:
        is_on_track = budget_used_pct <= time_elapsed_pct

    # Sisa budget per hari ke depan
    remaining_days = days_in_month - days_elapsed
    remaining_budget = max(0, total_budget - total_spent)
    daily_remaining_budget = remaining_budget // remaining_days if remaining_days > 0 else remaining_budget

    return {
        "month": month,
        "year": year,
        "month_label": get_month_label(year, month),
        "days_elapsed": days_elapsed,
        "days_in_month": days_in_month,
        "total_spent": total_spent,
        "total_spent_formatted": format_rupiah(total_spent),
        "daily_avg": daily_avg,
        "daily_avg_formatted": format_rupiah(daily_avg),
        "projected_total": projected_total,
        "projected_total_formatted": format_rupiah(projected_total),
        "total_budget": total_budget,
        "total_budget_formatted": format_rupiah(total_budget) if total_budget > 0 else None,
        "budget_used_pct": budget_used_pct,
        "time_elapsed_pct": time_elapsed_pct,
        "is_on_track": is_on_track,
        "remaining_days": remaining_days,
        "remaining_budget": remaining_budget,
        "remaining_budget_formatted": format_rupiah(remaining_budget),
        "daily_remaining_budget": daily_remaining_budget,
        "daily_remaining_budget_formatted": format_rupiah(daily_remaining_budget),
    }


async def get_monthly_comparison(
    db: AsyncSession,
    user_id: int,
    months: int = 3,
) -> dict:
    """Perbandingan multi-bulan."""
    months = min(months, 12)
    if months < 1:
        months = 3

    today = _today_wib()
    months_data = []
    max_amount = 0

    for i in range(months - 1, -1, -1):
        # Hitung tahun dan bulan
        m = today.month - i
        y = today.year
        while m <= 0:
            m += 12
            y -= 1

        month_start = _start_of_month(y, m)
        month_end = _end_of_month(y, m)

        result = await db.execute(
            select(
                func.coalesce(func.sum(Transaction.amount), 0),
                func.count(Transaction.id),
            )
            .where(
                Transaction.user_id == user_id,
                Transaction.transaction_date >= month_start,
                Transaction.transaction_date <= month_end,
            )
        )
        total, count = result.one()

        max_amount = max(max_amount, total)

        months_data.append({
            "year": y,
            "month": m,
            "label": get_month_label(y, m),
            "total_amount": total,
            "total_amount_formatted": format_rupiah(total),
            "transaction_count": count,
        })

    return {
        "months": months_data,
        "max_amount": max_amount,
    }
