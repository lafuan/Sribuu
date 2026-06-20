"""
Router untuk notifikasi browser — preferences dan budget alerts.
"""
from datetime import date, datetime

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select

from ..database import get_db_session
from ..models import User
from ..services.auth_service import get_current_user

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])


@router.get("/preferences")
async def get_notification_preferences(
    current_user: User = Depends(get_current_user),
):
    """Dapatkan preferensi notifikasi user."""
    return {
        "notification_enabled": bool(current_user.notification_enabled),
        "reminder_time": current_user.reminder_time or "20:00",
    }


@router.post("/preferences")
async def update_notification_preferences(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """Update preferensi notifikasi user."""
    form = await request.form()
    enabled = form.get("notification_enabled", "0") == "1"
    reminder_time = str(form.get("reminder_time", "20:00")).strip()

    # Validate reminder_time format (HH:MM)
    if reminder_time:
        parts = reminder_time.split(":")
        if len(parts) != 2:
            reminder_time = "20:00"
        else:
            try:
                h, m = int(parts[0]), int(parts[1])
                if h < 0 or h > 23 or m < 0 or m > 59:
                    reminder_time = "20:00"
            except ValueError:
                reminder_time = "20:00"

    db = get_db_session()
    try:
        result = await db.execute(select(User).where(User.id == current_user.id))
        user = result.scalar_one_or_none()
        if user:
            user.notification_enabled = 1 if enabled else 0
            user.reminder_time = reminder_time
            await db.commit()
        return {"status": "ok", "notification_enabled": enabled, "reminder_time": reminder_time}
    finally:
        await db.close()


@router.get("/check-budgets")
async def check_budget_alerts(
    current_user: User = Depends(get_current_user),
):
    """Cek budget usage per kategori dan return alert jika ada yang >= 80% atau 100%."""
    from calendar import monthrange

    from sqlalchemy import func

    from ..models import Budget, Transaction

    today = date.today()
    month = today.month
    year = today.year

    db = get_db_session()
    try:
        # Get all budgets for current month
        result = await db.execute(
            select(Budget).where(
                Budget.user_id == current_user.id,
                Budget.month == month,
                Budget.year == year,
            )
        )
        budgets = list(result.scalars().all())

        if not budgets:
            return {"alerts": []}

        # Get spending by category
        _, last_day = monthrange(year, month)
        start_date = date(year, month, 1)
        end_date = date(year, month, last_day)

        spending_result = await db.execute(
            select(
                Transaction.category_id,
                func.coalesce(func.sum(Transaction.amount), 0).label("total_spent"),
            )
            .where(
                Transaction.user_id == current_user.id,
                Transaction.transaction_date >= start_date,
                Transaction.transaction_date <= end_date,
            )
            .group_by(Transaction.category_id)
        )
        spending_map = {row.category_id: int(row.total_spent) for row in spending_result.all()}

        # Also get category names
        from ..models import Category
        cat_result = await db.execute(
            select(Category).where(Category.is_active == 1)
        )
        categories = {c.id: c for c in cat_result.scalars().all()}

        alerts = []
        for budget in budgets:
            spent = spending_map.get(int(budget.category_id), 0)
            if budget.amount > 0:
                percentage = (spent / budget.amount) * 100
                category = categories.get(int(budget.category_id))

                if percentage >= 100:
                    alerts.append({
                        "type": "budget_exceeded",
                        "category_name": category.name if category else "Unknown",
                        "category_icon": category.icon if category else "📦",
                        "category_id": budget.category_id,
                        "percentage": round(percentage, 1),
                        "message": f"Anggaran {category.icon if category else '📦'} {category.name if category else 'Unknown'} sudah TERLEWATI! ({round(percentage, 1)}%)",
                        "urgent": True,
                    })
                elif percentage >= 80:
                    alerts.append({
                        "type": "budget_warning",
                        "category_name": category.name if category else "Unknown",
                        "category_icon": category.icon if category else "📦",
                        "category_id": budget.category_id,
                        "percentage": round(percentage, 1),
                        "message": f"Anggaran {category.icon if category else '📦'} {category.name if category else 'Unknown'} sudah {round(percentage, 1)}% terpakai!",
                        "urgent": False,
                    })

        return {"alerts": alerts}
    finally:
        await db.close()
