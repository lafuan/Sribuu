"""
Service layer for notification preferences and budget alerts.
"""
from calendar import monthrange
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Budget, Category, Transaction, User


def _validate_reminder_time(reminder_time: str) -> str:
    """Validate HH:MM format, fallback to 20:00 on invalid input."""
    if not reminder_time:
        return "20:00"
    parts = reminder_time.split(":")
    if len(parts) != 2:
        return "20:00"
    try:
        h, m = int(parts[0]), int(parts[1])
        if h < 0 or h > 23 or m < 0 or m > 59:
            return "20:00"
    except ValueError:
        return "20:00"
    return reminder_time


async def get_preferences(db: AsyncSession, user_id: int) -> dict:
    """Get notification preferences for a user."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        return {"notification_enabled": False, "reminder_time": "20:00"}
    return {
        "notification_enabled": bool(user.notification_enabled),
        "reminder_time": user.reminder_time or "20:00",
    }


async def update_preferences(
    db: AsyncSession,
    user_id: int,
    enabled: bool,
    reminder_time: str,
) -> dict:
    """Update notification preferences for a user."""
    reminder_time = _validate_reminder_time(reminder_time)

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user:
        user.notification_enabled = 1 if enabled else 0
        user.reminder_time = reminder_time
        await db.commit()

    return {
        "status": "ok",
        "notification_enabled": enabled,
        "reminder_time": reminder_time,
    }


async def check_budget_alerts(
    db: AsyncSession,
    user_id: int,
    month: int | None = None,
    year: int | None = None,
) -> list[dict]:
    """Check budget usage per category and return alerts for >= 80% or >= 100%."""
    today = date.today()
    month = month or today.month
    year = year or today.year

    # Get all budgets for the given month/year
    result = await db.execute(
        select(Budget).where(
            Budget.user_id == user_id,
            Budget.month == month,
            Budget.year == year,
        )
    )
    budgets = list(result.scalars().all())

    if not budgets:
        return []

    # Get spending by category for the month
    _, last_day = monthrange(year, month)
    start_date = date(year, month, 1)
    end_date = date(year, month, last_day)

    spending_result = await db.execute(
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
    spending_map = {row.category_id: int(row.total_spent) for row in spending_result.all()}

    # Get active categories
    cat_result = await db.execute(
        select(Category).where(Category.is_active == 1)
    )
    categories = {int(c.id): c for c in cat_result.scalars().all()}

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
                    "message": (
                        f"Budget for {category.icon if category else '📦'}"
                        f" {category.name if category else 'Unknown'}"
                        f" EXCEEDED! ({round(percentage, 1)}%)"
                    ),
                    "urgent": True,
                })
            elif percentage >= 80:
                alerts.append({
                    "type": "budget_warning",
                    "category_name": category.name if category else "Unknown",
                    "category_icon": category.icon if category else "📦",
                    "category_id": budget.category_id,
                    "percentage": round(percentage, 1),
                    "message": (
                        f"Budget for {category.icon if category else '📦'}"
                        f" {category.name if category else 'Unknown'}"
                        f" is {round(percentage, 1)}% used!"
                    ),
                    "urgent": False,
                })

    return alerts
