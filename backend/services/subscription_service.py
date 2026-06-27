"""
Service layer untuk Subscription: deteksi transaksi berulang + CRUD.
"""

from datetime import date, datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import and_, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from ..models import Category, Subscription, Transaction
from ..schemas.subscription import SubscriptionCreate, SubscriptionUpdate
from ..utils.formatting import format_rupiah

WIB = timezone(timedelta(hours=7))


def _sub_to_dict(sub: Subscription) -> dict:
    return {
        "id": sub.id,
        "name": sub.name,
        "amount": sub.amount,
        "amount_formatted": format_rupiah(sub.amount),
        "frequency": sub.frequency,
        "is_active": bool(sub.is_active),
        "category_id": sub.category_id,
        "category_name": sub.category.name if sub.category else "",
        "category_icon": sub.category.icon if sub.category else "",
        "category_color": sub.category.color if sub.category else "#6b7280",
        "occurrence_count": sub.occurrence_count,
        "last_detected_date": sub.last_detected_date.isoformat() if sub.last_detected_date else None,
        "first_detected_date": sub.first_detected_date.isoformat() if sub.first_detected_date else None,
        "created_at": sub.created_at.isoformat() if sub.created_at else None,
    }


async def _get_sub_or_404(db: AsyncSession, sub_id: int, user_id: int) -> Subscription:
    result = await db.execute(
        select(Subscription)
        .options(joinedload(Subscription.category))
        .where(Subscription.id == sub_id)
    )
    sub = result.scalar_one_or_none()
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"status": "error", "message": "Subscription tidak ditemukan"},
        )
    if sub.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"status": "error", "message": "Akses ditolak"},
        )
    return sub


async def detect_subscriptions(
    db: AsyncSession, user_id: int, min_occurrences: int = 2
) -> list[dict]:
    """
    Deteksi transaksi berulang berdasarkan pola:
    - Nominal SAMA persis
    - Kategori SAMA
    - Muncul di minimal 2 bulan berbeda

    Query: GROUP BY category_id, amount
    HAVING COUNT(DISTINCT strftime('%Y-%m', transaction_date)) >= min_occurrences
    """
    # Menggunakan fungsi PostgreSQL untuk ekstrak year-month
    stmt = text("""
        SELECT
            t.category_id,
            t.amount,
            COUNT(*) AS total_count,
            COUNT(DISTINCT to_char(t.transaction_date, 'YYYY-MM')) AS distinct_months,
            MAX(t.transaction_date) AS last_date,
            MIN(t.transaction_date) AS first_date,
            c.name AS category_name,
            c.icon AS category_icon,
            c.color AS category_color
        FROM transactions t
        JOIN categories c ON c.id = t.category_id
        WHERE t.user_id = :user_id
          AND t.parent_transaction_id IS NULL
        GROUP BY t.category_id, t.amount, c.name, c.icon, c.color
        HAVING COUNT(DISTINCT to_char(t.transaction_date, 'YYYY-MM')) >= :min_occurrences
           AND COUNT(*) >= :min_occurrences
        ORDER BY total_count DESC, last_date DESC
    """)
    result = await db.execute(stmt, {"user_id": user_id, "min_occurrences": min_occurrences})
    rows = result.fetchall()

    detected = []
    for row in rows:
        cat_name = row.category_name
        freq = "monthly"
        if row.distinct_months >= 3:
            freq = "monthly"

        detected.append({
            "category_id": row.category_id,
            "amount": row.amount,
            "amount_formatted": format_rupiah(row.amount),
            "occurrence_count": row.total_count,
            "distinct_months": row.distinct_months,
            "last_date": row.last_date.isoformat() if row.last_date else None,
            "first_date": row.first_date.isoformat() if row.first_date else None,
            "category_name": cat_name,
            "category_icon": row.category_icon,
            "category_color": row.category_color or "#6b7280",
            "suggested_name": f"{row.category_icon} {cat_name} (Rp {row.amount:,.0f})",
            "frequency": freq,
        })

    return detected


async def list_subscriptions(
    db: AsyncSession, user_id: int,
    is_active: bool | None = None,
) -> list[dict]:
    """List subscriptions user."""
    stmt = (
        select(Subscription)
        .options(joinedload(Subscription.category))
        .where(Subscription.user_id == user_id)
    )
    if is_active is not None:
        stmt = stmt.where(Subscription.is_active == (1 if is_active else 0))
    stmt = stmt.order_by(Subscription.is_active.desc(), Subscription.last_detected_date.desc())
    result = await db.execute(stmt)
    subs = list(result.unique().scalars().all())
    return [_sub_to_dict(s) for s in subs]


async def get_subscription_summary(db: AsyncSession, user_id: int) -> dict:
    """Total pengeluaran subscription per bulan (aktif saja)."""
    stmt = (
        select(func.coalesce(func.sum(Subscription.amount), 0))
        .where(
            Subscription.user_id == user_id,
            Subscription.is_active == 1,
        )
    )
    result = await db.execute(stmt)
    total_monthly = result.scalar() or 0

    count_stmt = (
        select(func.count())
        .select_from(Subscription)
        .where(
            Subscription.user_id == user_id,
            Subscription.is_active == 1,
        )
    )
    count_result = await db.execute(count_stmt)
    active_count = count_result.scalar() or 0

    return {
        "total_monthly": total_monthly,
        "total_monthly_formatted": format_rupiah(total_monthly),
        "active_count": active_count,
    }


async def create_subscription(
    db: AsyncSession, user_id: int, data: SubscriptionCreate
) -> dict:
    """Buat subscription manual."""
    # Validasi kategori
    cat_result = await db.execute(
        select(Category).where(Category.id == data.category_id, Category.is_active == 1)
    )
    if not cat_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"status": "error", "message": "Kategori tidak ditemukan"},
        )

    if data.frequency not in ("monthly", "weekly", "yearly"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"status": "error", "message": "Frekuensi harus 'monthly', 'weekly', atau 'yearly'"},
        )

    sub = Subscription(
        user_id=user_id,
        category_id=data.category_id,
        name=data.name,
        amount=data.amount,
        frequency=data.frequency,
        is_active=1 if data.is_active else 0,
        occurrence_count=1,
        last_detected_date=date.today(),
        first_detected_date=date.today(),
    )
    db.add(sub)
    await db.flush()
    await db.refresh(sub, ["category"])
    return _sub_to_dict(sub)


async def save_detected_subscription(
    db: AsyncSession, user_id: int, category_id: int, amount: int,
    name: str, frequency: str, last_date: date, first_date: date,
) -> dict:
    """Simpan subscription yang terdeteksi (jika belum ada, update jika sudah)."""
    # Cek apakah sudah ada subscription dengan kombinasi ini
    result = await db.execute(
        select(Subscription).where(
            Subscription.user_id == user_id,
            Subscription.category_id == category_id,
            Subscription.amount == amount,
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        # Update
        existing.last_detected_date = last_date
        existing.occurrence_count = existing.occurrence_count + 1
        await db.flush()
        await db.refresh(existing, ["category"])
        return _sub_to_dict(existing)
    else:
        # Buat baru
        sub = Subscription(
            user_id=user_id,
            category_id=category_id,
            name=name,
            amount=amount,
            frequency=frequency,
            is_active=1,
            occurrence_count=1,
            last_detected_date=last_date,
            first_detected_date=first_date,
        )
        db.add(sub)
        await db.flush()
        await db.refresh(sub, ["category"])
        return _sub_to_dict(sub)


async def toggle_subscription(
    db: AsyncSession, sub_id: int, user_id: int, is_active: bool,
) -> dict:
    """Toggle status aktif/nonaktif subscription."""
    sub = await _get_sub_or_404(db, sub_id, user_id)
    sub.is_active = 1 if is_active else 0
    await db.flush()
    await db.refresh(sub, ["category"])
    return _sub_to_dict(sub)


async def update_subscription(
    db: AsyncSession, sub_id: int, user_id: int, data: SubscriptionUpdate,
) -> dict:
    """Update subscription."""
    sub = await _get_sub_or_404(db, sub_id, user_id)

    if data.name is not None:
        sub.name = data.name
    if data.amount is not None:
        sub.amount = data.amount
    if data.frequency is not None:
        if data.frequency not in ("monthly", "weekly", "yearly"):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"status": "error", "message": "Frekuensi harus 'monthly', 'weekly', atau 'yearly'"},
            )
        sub.frequency = data.frequency
    if data.category_id is not None:
        cat_result = await db.execute(
            select(Category).where(Category.id == data.category_id, Category.is_active == 1)
        )
        if not cat_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"status": "error", "message": "Kategori tidak ditemukan"},
            )
        sub.category_id = data.category_id
    if data.is_active is not None:
        sub.is_active = 1 if data.is_active else 0

    await db.flush()
    await db.refresh(sub, ["category"])
    return _sub_to_dict(sub)


async def delete_subscription(
    db: AsyncSession, sub_id: int, user_id: int,
) -> None:
    """Hapus subscription."""
    sub = await _get_sub_or_404(db, sub_id, user_id)
    await db.delete(sub)
    await db.flush()


async def run_detection_and_save(
    db: AsyncSession, user_id: int,
) -> dict:
    """
    Jalankan deteksi + simpan hasilnya ke tabel subscriptions.
    Returns: jumlah yang baru terdeteksi dan daftar subscription.
    """
    detected = await detect_subscriptions(db, user_id, min_occurrences=2)
    new_count = 0

    for d in detected:
        last_date = date.fromisoformat(d["last_date"]) if d["last_date"] else date.today()
        first_date = date.fromisoformat(d["first_date"]) if d["first_date"] else date.today()
        await save_detected_subscription(
            db, user_id, d["category_id"], d["amount"],
            d["suggested_name"], d["frequency"],
            last_date, first_date,
        )
        new_count += 1

    subscriptions = await list_subscriptions(db, user_id)
    summary = await get_subscription_summary(db, user_id)

    return {
        "subscriptions": subscriptions,
        "summary": summary,
        "detected_count": len(detected),
        "new_count": new_count,
    }
