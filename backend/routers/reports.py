"""
Router untuk download laporan PDF bulanan.
"""

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import User
from ..services.auth_service import get_current_user
from ..services.pdf_service import generate_monthly_report_pdf

router = APIRouter(prefix="/api/reports", tags=["Reports"])


@router.get("/monthly")
async def download_monthly_report(
    request: Request,
    year: int | None = Query(None, description="Tahun (YYYY), default: tahun sekarang"),
    month: int | None = Query(None, ge=1, le=12, description="Bulan (1-12), default: bulan sekarang"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Download laporan PDF bulanan — ringkasan pemasukan/pengeluaran, grafik,
    breakdown per kategori, budget vs actual."""
    filename, pdf_buf = await generate_monthly_report_pdf(
        db=db,
        user_id=current_user.id,
        year=year,
        month=month,
    )

    return Response(
        content=pdf_buf.getvalue(),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-cache",
        },
    )
