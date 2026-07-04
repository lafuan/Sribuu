"""
Router untuk notifikasi browser — prefersi dan budget alerts.
Mendelegasikan semua logic ke notification_service.
"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import User
from ..services.auth_service import get_current_user
from ..services.notification_service import (
    check_budget_alerts,
    get_preferences,
    update_preferences,
)

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])


@router.get("/preferences")
async def get_notification_preferences(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Dapatkan preferensi notifikasi user."""
    return await get_preferences(db, current_user.id)


@router.post("/preferences")
async def update_notification_preferences(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update preferensi notifikasi user."""
    form = await request.form()
    enabled = form.get("notification_enabled", "0") == "1"
    reminder_time = str(form.get("reminder_time", "20:00")).strip()

    return await update_preferences(db, current_user.id, enabled, reminder_time)


@router.get("/check-budgets")
async def check_budget_alerts_endpoint(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Cek budget usage per kategori dan return alert jika ada yang >= 80% atau 100%."""
    alerts = await check_budget_alerts(db, current_user.id)
    return {"alerts": alerts}
