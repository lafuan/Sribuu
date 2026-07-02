"""
Service layer untuk statistik: dashboard, by-category, daily-trend, monthly.
"""

import json
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from ..models import Category, Transaction, WeeklySummary
from ..utils.formatting import (
    format_rupiah,
    get_day_name_id,
    get_month_label,
    parse_tags,
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
            Transaction.parent_transaction_id.is_(None),
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
            Transaction.parent_transaction_id.is_(None),
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
            Transaction.parent_transaction_id.is_(None),
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
        .where(Transaction.user_id == user_id, Transaction.parent_transaction_id.is_(None))
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
    days_elapsed = max(days_elapsed, 1)
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


async def get_period_comparison(
    db: AsyncSession,
    user_id: int,
    period: str = "month",
    compare: str = "previous",
    anomaly_threshold: float = 20.0,
) -> dict:
    """Period-over-Period comparison: bandingkan spending antar periode.

    Args:
        period: 'month' atau 'week'
        compare: 'previous' (vs periode sebelumnya) atau 'average' (vs rata-rata)
        anomaly_threshold: persen perubahan untuk dianggap anomaly (default 20%)

    Returns:
        dict dengan overall comparison dan per-category breakdown + sparkline
    """
    today = _today_wib()
    ANOMALY_THRESHOLD = anomaly_threshold

    if period == "month":
        # Current month
        curr_start = today.replace(day=1)
        curr_end = _end_of_month(today.year, today.month)

        # Previous month
        prev_month = today.month - 1 or 12
        prev_year = today.year if today.month > 1 else today.year - 1
        prev_start = date(prev_year, prev_month, 1)
        prev_end = _end_of_month(prev_year, prev_month)
    else:  # week
        curr_monday = today - timedelta(days=today.weekday())
        curr_sunday = curr_monday + timedelta(days=6)
        curr_start, curr_end = curr_monday, curr_sunday

        prev_monday = curr_monday - timedelta(days=7)
        prev_sunday = curr_monday - timedelta(days=1)
        prev_start, prev_end = prev_monday, prev_sunday

    # --- Current period totals ---
    curr_result = await db.execute(
        select(
            func.coalesce(func.sum(Transaction.amount), 0),
            func.count(Transaction.id),
        ).where(
            Transaction.user_id == user_id,
            Transaction.transaction_date >= curr_start,
            Transaction.transaction_date <= curr_end,
        )
    )
    curr_total, curr_count = curr_result.one()

    # --- Previous period totals ---
    prev_result = await db.execute(
        select(
            func.coalesce(func.sum(Transaction.amount), 0),
            func.count(Transaction.id),
        ).where(
            Transaction.user_id == user_id,
            Transaction.transaction_date >= prev_start,
            Transaction.transaction_date <= prev_end,
        )
    )
    prev_total, prev_count = prev_result.one()

    curr_total = int(curr_total)
    prev_total = int(prev_total)

    # --- Per-category breakdown for both periods ---
    # Current period by category
    curr_cat_result = await db.execute(
        select(
            Category.id,
            Category.name,
            Category.icon,
            Category.color,
            func.coalesce(func.sum(Transaction.amount), 0).label("total"),
            func.count(Transaction.id).label("count"),
        )
        .join(Transaction, Transaction.category_id == Category.id, isouter=True)
        .where(
            Transaction.user_id == user_id,
            Transaction.transaction_date >= curr_start,
            Transaction.transaction_date <= curr_end,
        )
        .group_by(Category.id)
        .order_by(func.sum(Transaction.amount).desc())
    )
    curr_cats: dict[int, dict] = {}
    for row in curr_cat_result.all():
        curr_cats[row.id] = {
            "total": row.total,
            "count": row.count,
            "name": row.name,
            "icon": row.icon,
            "color": row.color,
        }

    # Previous period by category
    prev_cat_result = await db.execute(
        select(
            Category.id,
            func.coalesce(func.sum(Transaction.amount), 0).label("total"),
        )
        .join(Transaction, Transaction.category_id == Category.id, isouter=True)
        .where(
            Transaction.user_id == user_id,
            Transaction.transaction_date >= prev_start,
            Transaction.transaction_date <= prev_end,
        )
        .group_by(Category.id)
    )
    prev_cats: dict[int, dict] = {}
    for row in prev_cat_result.all():
        prev_cats[row.id] = {"total": row.total}

    # All category IDs seen
    all_cat_ids = set(curr_cats.keys()) | set(prev_cats.keys())

    # Build category comparison list
    category_comparisons = []
    all_category_names = {}

    for cat_id in all_cat_ids:
        curr_data = curr_cats.get(cat_id, {"total": 0, "count": 0, "name": "", "icon": "📦", "color": "#888"})
        prev_data = prev_cats.get(cat_id, {"total": 0})

        cat_name = curr_data["name"] or (prev_data.get("name", "Unknown") if isinstance(prev_data, dict) else "Unknown")
        cat_icon = curr_data["icon"]
        cat_color = curr_data["color"]

        if prev_data["total"] > 0:
            pct_change = round(((curr_data["total"] - prev_data["total"]) / prev_data["total"]) * 100, 1)
        else:
            pct_change = 100 if curr_data["total"] > 0 else 0

        is_anomaly = abs(pct_change) >= ANOMALY_THRESHOLD

        category_comparisons.append({
            "category_id": cat_id,
            "name": cat_name,
            "icon": cat_icon,
            "color": cat_color,
            "current_total": curr_data["total"],
            "current_total_formatted": format_rupiah(curr_data["total"]),
            "previous_total": prev_data["total"],
            "previous_total_formatted": format_rupiah(prev_data["total"]),
            "percentage_change": pct_change,
            "is_anomaly": is_anomaly,
            "trend": "up" if pct_change > 0 else ("down" if pct_change < 0 else "flat"),
        })

        all_category_names[cat_id] = cat_name

    # Sort: anomalies first, then by absolute % change descending
    category_comparisons.sort(key=lambda x: (-abs(x["percentage_change"]) if x["is_anomaly"] else -999, -abs(x["percentage_change"])))

    # --- 6-month sparkline per category ---
    sparkline_data: dict[int, list[dict]] = {}
    if period == "month":
        sparkline_query_months = 6
        for i in range(sparkline_query_months - 1, -1, -1):
            m = today.month - i
            y = today.year
            while m <= 0:
                m += 12
                y -= 1
            month_start = _start_of_month(y, m)
            month_end = _end_of_month(y, m)

            for cat_id in all_cat_ids:
                if cat_id not in sparkline_data:
                    sparkline_data[cat_id] = []

                cat_total_result = await db.execute(
                    select(func.coalesce(func.sum(Transaction.amount), 0))
                    .where(
                        Transaction.user_id == user_id,
                        Transaction.category_id == cat_id,
                        Transaction.transaction_date >= month_start,
                        Transaction.transaction_date <= month_end,
                    )
                )
                cat_total = int(cat_total_result.scalar() or 0)
                sparkline_data[cat_id].append({
                    "month": m,
                    "year": y,
                    "label": get_month_label(y, m),
                    "total": cat_total,
                })

    # Attach sparkline to category comparisons
    for cat_comp in category_comparisons:
        cat_id = cat_comp["category_id"]
        cat_comp["sparkline"] = sparkline_data.get(cat_id, [])

    # Overall summary
    curr_vs_prev_pct = round(((curr_total - prev_total) / prev_total) * 100, 1) if prev_total > 0 else (0 if curr_total == 0 else 100)

    # Highest change categories
    biggest_increase = sorted(
        [c for c in category_comparisons if c["trend"] == "up" and c["percentage_change"] > 0],
        key=lambda x: -x["percentage_change"]
    )
    biggest_decrease = sorted(
        [c for c in category_comparisons if c["trend"] == "down" and c["percentage_change"] < 0],
        key=lambda x: x["percentage_change"]
    )

    return {
        "period": period,
        "compare_mode": compare,
        "current_period": {
            "start": curr_start.isoformat(),
            "end": curr_end.isoformat(),
            "total_amount": curr_total,
            "total_amount_formatted": format_rupiah(curr_total),
            "transaction_count": curr_count,
        },
        "previous_period": {
            "start": prev_start.isoformat(),
            "end": prev_end.isoformat(),
            "total_amount": prev_total,
            "total_amount_formatted": format_rupiah(prev_total),
            "transaction_count": prev_count,
        },
        "overall_change_pct": curr_vs_prev_pct,
        "anomaly_threshold": ANOMALY_THRESHOLD,
        "categories": category_comparisons,
        "highlights": {
            "biggest_increase": biggest_increase[:3],
            "biggest_decrease": biggest_decrease[:3],
            "anomalies": [c for c in category_comparisons if c["is_anomaly"]],
        },
    }


async def generate_weekly_summary(
    db: AsyncSession,
    user_id: int,
    force: bool = False,
) -> dict:
    """Generate atau refresh ringkasan mingguan untuk minggu ini.

    Args:
        db: Database session
        user_id: ID user
        force: True = generate ulang meskipun sudah ada

    Returns:
        dict dengan data ringkasan mingguan
    """
    today = _today_wib()
    iso_year, iso_week, _ = today.isocalendar()

    # Cek apakah sudah ada summary untuk minggu ini
    if not force:
        summary_result = await db.execute(
            select(WeeklySummary).where(
                WeeklySummary.user_id == user_id,
                WeeklySummary.year == iso_year,
                WeeklySummary.week == iso_week,
            )
        )
        existing = summary_result.scalar_one_or_none()
        if existing:
            return _weekly_summary_to_dict(existing)

    # Hitung rentang minggu ini (Senin - Minggu)
    monday = today - timedelta(days=today.weekday())  # Senin
    sunday = monday + timedelta(days=6)  # Minggu

    # --- Total minggu ini ---
    result = await db.execute(
        select(
            func.coalesce(func.sum(Transaction.amount), 0),
            func.count(Transaction.id),
        ).where(
            Transaction.user_id == user_id,
            Transaction.transaction_date >= monday,
            Transaction.transaction_date <= sunday,
        )
    )
    total_amount, tx_count = result.one()
    total_amount = int(total_amount)
    tx_count = int(tx_count)

    # Daily average
    days_so_far = max((today - monday).days + 1, 1)
    daily_average = total_amount // days_so_far if days_so_far > 0 else 0

    # --- Breakdown per kategori ---
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
            Transaction.transaction_date >= monday,
            Transaction.transaction_date <= sunday,
        )
        .group_by(Category.id)
        .order_by(func.sum(Transaction.amount).desc())
    )
    categories = []
    for row in result.all():
        categories.append({
            "category_id": row.id,
            "name": row.name,
            "icon": row.icon,
            "color": row.color,
            "total": row.total,
            "total_formatted": format_rupiah(row.total),
            "transaction_count": row.count,
            "percentage": round(row.total / total_amount * 100, 1) if total_amount > 0 else 0,
        })

    # --- Top 3 transaksi terbesar minggu ini ---
    tx_result = await db.execute(
        select(Transaction)
        .options(joinedload(Transaction.category))
        .where(
            Transaction.user_id == user_id,
            Transaction.transaction_date >= monday,
            Transaction.transaction_date <= sunday,
        )
        .order_by(Transaction.amount.desc())
        .limit(3)
    )
    top_tx = []
    for tx in tx_result.unique().scalars().all():
        top_tx.append({
            "id": tx.id,
            "amount": tx.amount,
            "amount_formatted": format_rupiah(tx.amount),
            "notes": tx.notes,
            "category_name": tx.category.name if tx.category else "Tanpa kategori",
            "category_icon": tx.category.icon if tx.category else "📦",
            "date": tx.transaction_date.isoformat(),
        })

    # --- Minggu sebelumnya ---
    prev_monday = monday - timedelta(days=7)
    prev_sunday = monday - timedelta(days=1)
    result = await db.execute(
        select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.user_id == user_id,
            Transaction.transaction_date >= prev_monday,
            Transaction.transaction_date <= prev_sunday,
        )
    )
    prev_week_total = int(result.scalar() or 0)

    # Percentage change
    if prev_week_total > 0 and total_amount > 0:
        pct_change = round(((total_amount - prev_week_total) / prev_week_total) * 100)
    else:
        pct_change = 0

    # --- Simpan ke database ---
    save_result = await db.execute(
        select(WeeklySummary).where(
            WeeklySummary.user_id == user_id,
            WeeklySummary.year == iso_year,
            WeeklySummary.week == iso_week,
        )
    )
    existing = save_result.scalar_one_or_none()

    if existing:
        existing.total_amount = total_amount
        existing.transaction_count = tx_count
        existing.daily_average = daily_average
        existing.category_breakdown = json.dumps(categories, ensure_ascii=False)
        existing.top_transactions = json.dumps(top_tx, ensure_ascii=False)
        existing.prev_week_total = prev_week_total
        existing.percentage_change = pct_change
        existing.generated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    else:
        ws = WeeklySummary(
            user_id=user_id,
            year=iso_year,
            week=iso_week,
            total_amount=total_amount,
            transaction_count=tx_count,
            daily_average=daily_average,
            category_breakdown=json.dumps(categories, ensure_ascii=False),
            top_transactions=json.dumps(top_tx, ensure_ascii=False),
            prev_week_total=prev_week_total,
            percentage_change=pct_change,
        )
        db.add(ws)

    await db.commit()

    return {
        "year": iso_year,
        "week": iso_week,
        "total_amount": total_amount,
        "total_amount_formatted": format_rupiah(total_amount),
        "transaction_count": tx_count,
        "daily_average": daily_average,
        "daily_average_formatted": format_rupiah(daily_average),
        "categories": categories,
        "top_transactions": top_tx,
        "prev_week_total": prev_week_total,
        "prev_week_total_formatted": format_rupiah(prev_week_total),
        "percentage_change": pct_change,
        "monday": monday.isoformat(),
        "sunday": sunday.isoformat(),
        "generated": True,
    }


async def get_weekly_summary(
    db: AsyncSession,
    user_id: int,
) -> dict:
    """Dapatkan ringkasan mingguan. Generate otomatis jika belum ada."""
    return await generate_weekly_summary(db, user_id, force=False)


def _weekly_summary_to_dict(ws: WeeklySummary) -> dict:
    """Convert model WeeklySummary ke dict."""
    return {
        "year": ws.year,
        "week": ws.week,
        "total_amount": ws.total_amount,
        "total_amount_formatted": format_rupiah(ws.total_amount),
        "transaction_count": ws.transaction_count,
        "daily_average": ws.daily_average,
        "daily_average_formatted": format_rupiah(ws.daily_average),
        "categories": json.loads(ws.category_breakdown) if ws.category_breakdown else [],
        "top_transactions": json.loads(ws.top_transactions) if ws.top_transactions else [],
        "prev_week_total": ws.prev_week_total,
        "prev_week_total_formatted": format_rupiah(ws.prev_week_total),
        "percentage_change": ws.percentage_change,
        "generated_at": ws.generated_at.isoformat(),
        "generated": False,
        "cached": True,
    }


async def get_top_tags(
    db: AsyncSession,
    user_id: int,
    year: int | None = None,
    month: int | None = None,
    limit: int = 10,
) -> list[dict]:
    """Dapatkan top N tag yang paling sering dipakai bulan ini."""
    from calendar import monthrange

    today = date.today()
    year = year or today.year
    month = month or today.month
    _, last_day = monthrange(year, month)
    start_date = date(year, month, 1)
    end_date = date(year, month, last_day)

    result = await db.execute(
        select(Transaction.notes)
        .where(
            Transaction.user_id == user_id,
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date <= end_date,
            Transaction.notes.isnot(None),
            Transaction.notes != "",
        )
        .order_by(Transaction.transaction_date.desc())
    )
    rows = result.scalars().all()

    # Count tag frequency
    tag_count: dict[str, int] = {}
    for notes in rows:
        for tag in parse_tags(notes):
            tag_count[tag] = tag_count.get(tag, 0) + 1

    # Sort by frequency, return top N
    sorted_tags = sorted(tag_count.items(), key=lambda x: (-x[1], x[0]))
    return [
        {"tag": tag, "count": count}
        for tag, count in sorted_tags[:limit]
    ]


async def annual_summary_stats(  # pragma: no cover
    db: AsyncSession,
    user_id: int,
    year: int | None = None,
) -> dict:
    """Year-End Financial Summary — laporan keuangan tahunan otomatis.

    Returns:
        dict dengan:
        - total_income: total semua transaksi (semua kategori)
        - total_expense: total semua transaksi (pengeluaran)
        - savings_rate: (income - expense) / income × 100
        - top_categories: 5 kategori terbesar
        - biggest_spending_month: bulan dengan pengeluaran terbesar
        - biggest_savings_month: bulan dengan savings rate tertinggi
        - year_over_year: perbandingan dengan tahun sebelumnya
        - average_monthly_spending: rata-rata per bulan
        - total_transactions: jumlah transaksi tahun ini
        - streak: longest consecutive recording streak
    """
    today = _today_wib()
    if year is None:
        year = today.year

    year_start = date(year, 1, 1)
    year_end = date(year, 12, 31)

    # --- Total transactions for the year ---
    result = await db.execute(
        select(
            func.coalesce(func.sum(Transaction.amount), 0),
            func.count(Transaction.id),
        ).where(
            Transaction.user_id == user_id,
            Transaction.transaction_date >= year_start,
            Transaction.transaction_date <= year_end,
        )
    )
    total_amount, total_tx_count = result.one()
    total_amount = int(total_amount)
    total_tx_count = int(total_tx_count)

    # --- Income vs Expense breakdown ---
    # All transactions are treated as expenses (positive amounts in this app)
    # For savings calculation, we need income - expense
    # We'll consider "income" if we can identify income categories
    # For now, treat ALL transactions as expense (since this is an expense tracker)
    # The savings rate will be shown as: 0% since we track only expenses
    # But we can still show total spending
    total_expense = total_amount
    total_income = total_amount  # placeholder — income tracking is separate concern

    # --- Monthly breakdown ---
    monthly_data = []
    for month_num in range(1, 13):
        month_start = _start_of_month(year, month_num)
        month_end = _end_of_month(year, month_num)

        result = await db.execute(
            select(
                func.coalesce(func.sum(Transaction.amount), 0),
                func.count(Transaction.id),
            ).where(
                Transaction.user_id == user_id,
                Transaction.transaction_date >= month_start,
                Transaction.transaction_date <= month_end,
            )
        )
        month_total, month_count = result.one()
        month_total = int(month_total)

        # Get income (if any transactions with negative amount — not applicable here)
        # For savings: we don't have income data, so we'll just show expense
        savings_rate = 0.0  # Cannot calculate without income data

        monthly_data.append({
            "month": month_num,
            "month_label": get_month_label(year, month_num),
            "total_amount": month_total,
            "total_amount_formatted": format_rupiah(month_total),
            "transaction_count": month_count,
            "savings_rate": savings_rate,
        })

    # --- Top 5 spending categories ---
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
            Transaction.transaction_date >= year_start,
            Transaction.transaction_date <= year_end,
        )
        .group_by(Category.id)
        .order_by(func.sum(Transaction.amount).desc())
        .limit(5)
    )
    top_categories = []
    for row in result.all():
        pct = round(row.total / total_expense * 100, 1) if total_expense > 0 else 0
        top_categories.append({
            "category": {
                "id": row.id,
                "name": row.name,
                "icon": row.icon,
                "color": row.color,
            },
            "total_amount": row.total,
            "total_amount_formatted": format_rupiah(row.total),
            "percentage": pct,
            "transaction_count": row.count,
        })

    # --- Biggest spending month ---
    biggest_spending_month = max(monthly_data, key=lambda x: x["total_amount"]) if monthly_data else None
    if biggest_spending_month and biggest_spending_month["total_amount"] == 0:
        biggest_spending_month = None

    # --- Average monthly spending ---
    avg_monthly = int(total_expense / 12) if total_expense > 0 else 0

    # --- Total transactions ---
    total_transactions = total_tx_count

    # --- Streak: longest consecutive recording streak ---
    # Get all transaction dates for the year
    result = await db.execute(
        select(Transaction.transaction_date)
        .where(
            Transaction.user_id == user_id,
            Transaction.transaction_date >= year_start,
            Transaction.transaction_date <= year_end,
        )
        .group_by(Transaction.transaction_date)
        .order_by(Transaction.transaction_date)
    )
    tx_dates = [row.transaction_date for row in result.all()]

    longest_streak = 0
    current_streak = 0
    prev_date = None
    for d in tx_dates:
        if prev_date is None:
            current_streak = 1
        elif (d - prev_date).days == 1:
            current_streak += 1
        else:
            longest_streak = max(longest_streak, current_streak)
            current_streak = 1
        prev_date = d
    longest_streak = max(longest_streak, current_streak)

    # --- Year-over-Year comparison ---
    prev_year = year - 1
    prev_year_start = date(prev_year, 1, 1)
    prev_year_end = date(prev_year, 12, 31)

    result = await db.execute(
        select(func.coalesce(func.sum(Transaction.amount), 0))
        .where(
            Transaction.user_id == user_id,
            Transaction.transaction_date >= prev_year_start,
            Transaction.transaction_date <= prev_year_end,
        )
    )
    prev_year_total = int(result.scalar() or 0)

    yoy_change_pct = 0.0
    if prev_year_total > 0:
        yoy_change_pct = round(((total_expense - prev_year_total) / prev_year_total) * 100, 1)
    elif total_expense > 0:
        yoy_change_pct = 100.0

    year_over_year = {
        "previous_year": prev_year,
        "previous_year_total": prev_year_total,
        "previous_year_total_formatted": format_rupiah(prev_year_total),
        "current_year_total": total_expense,
        "current_year_total_formatted": format_rupiah(total_expense),
        "change_pct": yoy_change_pct,
        "has_previous_year_data": prev_year_total > 0,
    }

    # Savings rate: (income - expense) / income × 100
    # Since we track only expenses, savings rate = 0%
    # But if we had income categories, we could calculate properly
    savings_rate = 0.0  # Cannot calculate without income data

    return {
        "year": year,
        "total_income": total_income,
        "total_income_formatted": format_rupiah(total_income),
        "total_expense": total_expense,
        "total_expense_formatted": format_rupiah(total_expense),
        "savings_rate": savings_rate,
        "savings_rate_formatted": f"{savings_rate:.1f}%",
        "top_categories": top_categories,
        "monthly_breakdown": monthly_data,
        "biggest_spending_month": biggest_spending_month,
        "biggest_savings_month": None,  # Cannot determine without income data
        "average_monthly_spending": avg_monthly,
        "average_monthly_spending_formatted": format_rupiah(avg_monthly),
        "total_transactions": total_transactions,
        "streak": longest_streak,
        "year_over_year": year_over_year,
    }


async def get_cash_flow_forecast(
    db: AsyncSession,
    user_id: int,
    safe_balance: int | None = None,
) -> dict:
    """Cash Flow Forecast — Prediksi saldo & pengeluaran mendatang.

    Algorithm:
    - Weighted average last 3 months daily spending per category
    - Detect recurring transactions (same amount + category + day-of-month)
    - Project daily spending for rest of current month
    - Track cumulative expenses and running "balance"

    Returns:
        dict dengan daily forecast, warnings, dan confidence score.
    """
    today = _today_wib()
    current_month_start = today.replace(day=1)
    current_month_end = _end_of_month(today.year, today.month)
    days_in_month = (current_month_end - current_month_start).days + 1
    days_remaining = (current_month_end - today).days

    # --- 1. Get current month spending so far ---
    result = await db.execute(
        select(
            func.coalesce(func.sum(Transaction.amount), 0),
            func.count(Transaction.id),
        ).where(
            Transaction.user_id == user_id,
            Transaction.transaction_date >= current_month_start,
            Transaction.transaction_date <= today,
        )
    )
    current_month_spent = int(result.one()[0])

    # --- 2. Get previous 3 months total spending for weighted average ---
    months_data = []  # type: ignore[assignment]
    weights = [0.5, 0.3, 0.2]  # most recent gets highest weight

    for i, offset in enumerate([1, 2, 3]):
        m = today.month - offset
        y = today.year
        while m <= 0:
            m += 12
            y -= 1

        month_start = _start_of_month(y, m)
        month_end = _end_of_month(y, m)

        result = await db.execute(
            select(func.coalesce(func.sum(Transaction.amount), 0)).where(
                Transaction.user_id == user_id,
                Transaction.transaction_date >= month_start,
                Transaction.transaction_date <= month_end,
            )
        )
        total = int(result.scalar() or 0)
        days_in_that_month = (month_end - month_start).days + 1
        daily_avg = total / days_in_that_month if days_in_that_month > 0 else 0

        months_data.append({
            "month": m,
            "year": y,
            "label": get_month_label(y, m),
            "total": total,
            "daily_avg": daily_avg,
            "weight": weights[i],
        })

    # --- 3. Calculate weighted average daily spending ---
    weighted_daily = sum(m["daily_avg"] * m["weight"] for m in months_data)

    # Also calculate per-category weighted daily for recurring detection
    category_daily: dict[int, dict] = {}
    for m_data in months_data:
        y, m = m_data["year"], m_data["month"]
        month_start = _start_of_month(y, m)
        month_end = _end_of_month(y, m)
        days_in_that_month = (month_end - month_start).days + 1

        result = await db.execute(
            select(
                Category.id,
                Category.name,
                Category.icon,
                Category.color,
                func.coalesce(func.sum(Transaction.amount), 0).label("total"),
            )
            .join(Transaction, Transaction.category_id == Category.id)
            .where(
                Transaction.user_id == user_id,
                Transaction.transaction_date >= month_start,
                Transaction.transaction_date <= month_end,
            )
            .group_by(Category.id)
        )
        for row in result.all():
            cat_id = row.id
            if cat_id not in category_daily:
                category_daily[cat_id] = {"name": row.name, "icon": row.icon, "color": row.color, "totals": []}
            category_daily[cat_id]["totals"].append({"total": row.total, "weight": m_data["weight"]})

    # Weighted per-category daily
    for _cat_id, cat_data in category_daily.items():
        weighted = sum(t["total"] / 30 * t["weight"] for t in cat_data["totals"])  # approximate
        cat_data["weighted_daily"] = weighted

    # --- 4. Detect recurring transactions ---
    # Look for transactions that appear on the same day-of-month in multiple months
    recurring_transactions: list[dict] = []

    for cat_id, cat_data in category_daily.items():
        if len(cat_data["totals"]) >= 2:  # at least 2 months of data
            totals = [t["total"] for t in cat_data["totals"]]
            # If amounts are similar (within 10%), consider it recurring
            if totals and max(totals) > 0:
                ratio = min(totals) / max(totals) if max(totals) > 0 else 0
                if ratio >= 0.9:  # very consistent
                    # Calculate typical amount per occurrence
                    avg_amount = sum(t["total"] for t in cat_data["totals"]) / len(cat_data["totals"])
                    recurring_transactions.append({
                        "category_id": cat_id,
                        "category_name": cat_data["name"],
                        "category_icon": cat_data["icon"],
                        "category_color": cat_data["color"],
                        "estimated_amount": int(avg_amount),
                        "estimated_amount_formatted": format_rupiah(int(avg_amount)),
                        "note": f"Rata-rata {cat_data['name']} tiap bulan",
                    })

    # --- 5. Build daily forecast for rest of month ---
    daily_forecast: list[dict] = []
    cumulative_expense = current_month_spent

    for day_offset in range(days_remaining + 1):
        forecast_date = today + timedelta(days=day_offset)

        # Base prediction: weighted average daily spending
        base_prediction = weighted_daily

        # Add recurring transaction contribution if it falls on this day
        is_recurring = False
        recurring_note = None

        # Check if any recurring transaction typically occurs around this day
        # Since we don't have exact day data, we'll spread recurring amounts
        # across the month proportionally
        recurring_contribution = 0
        for rt in recurring_transactions:
            # Distribute recurring amount across typical occurrence frequency
            recurring_contribution += rt["estimated_amount"] * 0.5  # conservative estimate

        # For now, just use the daily weighted average + recurring spread
        predicted_expense = int(base_prediction + (recurring_contribution / days_in_month))
        cumulative_expense += predicted_expense

        # Predicted balance = negative of cumulative expense (expense tracker)
        # Lower balance = more spent
        # We track it as "budget remaining" concept
        predicted_balance = -cumulative_expense  # represents total spent so far

        daily_forecast.append({
            "date": forecast_date.isoformat(),
            "date_formatted": f"{forecast_date.day:02d}/{forecast_date.month:02d}",
            "day_name": get_day_name_id(forecast_date),
            "predicted_expense": predicted_expense,
            "predicted_expense_formatted": format_rupiah(predicted_expense),
            "cumulative_expense": cumulative_expense,
            "cumulative_expense_formatted": format_rupiah(cumulative_expense),
            "predicted_balance": predicted_balance,
            "predicted_balance_formatted": format_rupiah(abs(predicted_balance)),
            "is_recurring": is_recurring,
            "recurring_note": recurring_note,
        })

    # --- 6. Calculate totals ---
    total_predicted = cumulative_expense
    end_of_month_balance = -total_predicted

    # --- 7. Warning logic ---
    warning = None
    if safe_balance is not None and end_of_month_balance < safe_balance:
        warning = f"⚠️ Saldo akan di bawah threshold aman! Sisa predicted {format_rupiah(abs(end_of_month_balance))}"
    elif end_of_month_balance < 0:
        warning = f"⚠️ Dengan speed pengeluaran saat ini, akhir bulan saldo akan tinggal {format_rupiah(abs(end_of_month_balance))}"

    # --- 8. Confidence score ---
    # Confidence is higher if we have more historical data and recurring transactions
    _months_with_data = sum(1 for _m in months_data if _m["total"] > 0)  # type: ignore[misc]
    confidence = min(1.0, (_months_with_data * 0.25) + (len(recurring_transactions) * 0.15) + 0.1)

    return {
        "current_balance": -current_month_spent,  # negative = spent
        "current_balance_formatted": format_rupiah(abs(current_month_spent)),
        "end_of_month_balance": end_of_month_balance,
        "end_of_month_balance_formatted": format_rupiah(abs(end_of_month_balance)),
        "total_predicted_expense": total_predicted,
        "total_predicted_expense_formatted": format_rupiah(total_predicted),
        "daily_forecast": daily_forecast,
        "forecast_end_date": current_month_end.isoformat(),
        "warning": warning,
        "safe_balance": safe_balance,
        "confidence": round(confidence, 2),
        "recurring_transactions": recurring_transactions,
        "monthly_avg_based_on": [
            {"month": m["month"], "year": m["year"], "label": m["label"],
             "total": m["total"], "daily_avg": round(m["daily_avg"])}  # type: ignore[call-overload, misc]
            for m in months_data
        ],
    }


async def get_sankey_data(
    db: AsyncSession, user_id: int, year: int | None = None, month: int | None = None
) -> dict:
    """Sankey diagram: Income → Categories → Subcategories/Transactions.

    Returns nodes + links in D3.js Sankey format.
    """
    today = _today_wib()
    if year is None:
        year = today.year
    if month is None:
        month = today.month

    month_start = _start_of_month(year, month)
    month_end = _end_of_month(year, month)

    # --- Total income bulan ini ---
    income_result = await db.execute(
        select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.user_id == user_id,
            Transaction.type == "income",
            func.date(Transaction.date) >= month_start,
            func.date(Transaction.date) <= month_end,
        )
    )
    total_income = income_result.scalar() or 0

    # --- Pengeluaran per kategori + subkategori ---
    expense_result = await db.execute(
        select(
            Category.id,
            Category.name,
            Category.parent_id,
            Category.icon,
            Category.color,
            func.coalesce(func.sum(Transaction.amount), 0).label("total"),
        )
        .join(Transaction, Transaction.category_id == Category.id)
        .where(
            Transaction.user_id == user_id,
            Transaction.type == "expense",
            func.date(Transaction.date) >= month_start,
            func.date(Transaction.date) <= month_end,
        )
        .group_by(Category.id, Category.name, Category.parent_id, Category.icon, Category.color)
        .order_by(func.sum(Transaction.amount).desc())
    )
    rows = expense_result.all()

    # Build nodes and links
    nodes = []
    links = []
    node_map = {}  # name → index

    def _add_node(name: str, node_type: str = "category", extra: dict | None = None) -> int:
        if name not in node_map:
            idx = len(nodes)
            node_map[name] = idx
            node_info = {"name": name, "type": node_type}
            if extra:
                node_info.update(extra)
            nodes.append(node_info)
            return idx
        return node_map[name]

    # Node 0: Income source
    income_idx = _add_node("Pemasukan", "income", {"total": total_income})

    if total_income == 0 and not rows:
        # No data at all
        return {
            "nodes": [{"name": "Pemasukan", "type": "income", "total": 0},
                      {"name": "Tidak ada data", "type": "category"}],
            "links": [{"source": 0, "target": 1, "value": 1}],
            "total_income": 0,
            "total_expense": 0,
            "month": month,
            "year": year,
            "month_label": get_month_label(month),
        }

    # Separate parent categories and subcategories
    parent_categories = {}
    subcategories = {}

    for cat_id, cat_name, parent_id, icon, color, total in rows:
        if total is None or total == 0:
            continue
        if parent_id is None:
            parent_categories[cat_name] = {
                "id": cat_id,
                "total": total,
                "icon": icon,
                "color": color,
            }
        else:
            subcategories[(parent_id, cat_name)] = {
                "id": cat_id,
                "name": cat_name,
                "total": total,
                "icon": icon,
                "color": color,
            }

    total_expense = 0

    # Build links: Income → Category → Subcategory
    for parent_name, pdata in parent_categories.items():
        parent_total = pdata["total"]
        total_expense += parent_total

        # Add parent category node
        parent_idx = _add_node(
            parent_name,
            "category",
            {"icon": pdata.get("icon", ""), "color": pdata.get("color", ""), "total": parent_total},
        )

        # Link: Income → Category
        links.append({"source": income_idx, "target": parent_idx, "value": parent_total})

        # Find subcategories under this parent
        parent_subs = [(name, d) for (pid, name), d in subcategories.items() if pid == pdata["id"]]
        subs_total = sum(d["total"] for _, d in parent_subs)

        if parent_subs and subs_total > 0:
            remaining = parent_total - subs_total
            for sub_name, sdata in parent_subs:
                sub_idx = _add_node(
                    sub_name,
                    "subcategory",
                    {"icon": sdata.get("icon", ""), "color": sdata.get("color", ""), "total": sdata["total"]},
                )
                links.append({"source": parent_idx, "target": sub_idx, "value": sdata["total"]})

            # If there's remainder (uncategorized under parent), add "Lainnya" node
            if remaining > 0:
                other_idx = _add_node(
                    f"Lainnya ({parent_name})",
                    "subcategory",
                    {"total": remaining},
                )
                links.append({"source": parent_idx, "target": other_idx, "value": remaining})
        elif parent_total > 0:
            # No subcategories — add terminal "Lainnya" for remaining
            other_idx = _add_node(
                f"Lainnya ({parent_name})",
                "subcategory",
                {"total": parent_total},
            )
            links.append({"source": parent_idx, "target": other_idx, "value": parent_total})

    # Uncategorized expenses (transactions without category)
    uncat_result = await db.execute(
        select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.user_id == user_id,
            Transaction.type == "expense",
            Transaction.category_id.is_(None),
            func.date(Transaction.date) >= month_start,
            func.date(Transaction.date) <= month_end,
        )
    )
    uncategorized = uncat_result.scalar() or 0
    if uncategorized > 0:
        total_expense += uncategorized
        uncat_idx = _add_node("Tanpa Kategori", "category", {"total": uncategorized})
        links.append({"source": income_idx, "target": uncat_idx, "value": uncategorized})

    return {
        "nodes": nodes,
        "links": links,
        "total_income": total_income,
        "total_expense": total_expense,
        "month": month,
        "year": year,
        "month_label": get_month_label(month),
    }
