"""
Router untuk metode pembayaran (read-only).
"""

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import PaymentMethod, User
from ..schemas.auth import StandardResponse
from ..services.auth_service import get_current_user

router = APIRouter(prefix="/api/payment-methods", tags=["Payment Methods"])


@router.get("")
async def list_payment_methods(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List metode pembayaran aktif."""
    result = await db.execute(
        select(PaymentMethod).where(PaymentMethod.is_active == 1).order_by(PaymentMethod.id)
    )
    methods = result.scalars().all()

    return StandardResponse(
        status="success",
        data={
            "payment_methods": [
                {"id": m.id, "name": m.name, "icon": m.icon}
                for m in methods
            ]
        },
    ).model_dump()
