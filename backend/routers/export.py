"""
Router untuk export CSV dan JSON.
"""

from datetime import date

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import User
from ..services.auth_service import get_current_user
from ..services.export_service import export_csv, export_json

router = APIRouter(prefix="/api/export", tags=["Export"])


@router.get("/csv")
async def export_transactions_csv(
    request: Request,
    date_from: date | None = Query(None, description="Awal rentang tanggal"),
    date_to: date | None = Query(None, description="Akhir rentang tanggal"),
    category_id: int | None = Query(None, description="Filter kategori"),
    payment_method_id: int | None = Query(None, description="Filter metode bayar"),
    search: str | None = Query(None, description="Pencarian teks pada catatan"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Export transaksi ke CSV."""
    result = await export_csv(
        db=db,
        user_id=current_user.id,
        date_from=date_from,
        date_to=date_to,
        category_id=category_id,
        payment_method_id=payment_method_id,
        search=search,
    )

    if result is None:
        return Response(status_code=204)

    filename, csv_content = result

    return Response(
        content=csv_content.encode("utf-8"),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


@router.get("/json")
async def export_transactions_json(
    request: Request,
    date_from: date | None = Query(None, description="Awal rentang tanggal"),
    date_to: date | None = Query(None, description="Akhir rentang tanggal"),
    category_id: int | None = Query(None, description="Filter kategori"),
    payment_method_id: int | None = Query(None, description="Filter metode bayar"),
    search: str | None = Query(None, description="Pencarian teks pada catatan"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Export transaksi ke JSON."""
    result = await export_json(
        db=db,
        user_id=current_user.id,
        date_from=date_from,
        date_to=date_to,
        category_id=category_id,
        payment_method_id=payment_method_id,
        search=search,
    )

    if result is None:
        return Response(status_code=204)

    filename, json_content = result

    return Response(
        content=json_content.encode("utf-8"),
        media_type="application/json; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )
