"""
Router untuk modul transaksi: CRUD, filter, pagination.
"""

from datetime import date

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import User
from ..schemas.auth import StandardResponse
from ..schemas.transaction import TransactionCreate, TransactionUpdate
from ..services.auth_service import get_current_user
from ..services.transaction_service import (
    create_transaction,
    delete_transaction,
    get_transaction_detail,
    list_transactions,
    update_transaction,
)

router = APIRouter(prefix="/api/transactions", tags=["Transactions"])


@router.get("")
async def list_tx(
    request: Request,
    date_from: date | None = Query(None, description="Awal rentang tanggal"),
    date_to: date | None = Query(None, description="Akhir rentang tanggal"),
    category_id: int | None = Query(None, description="Filter kategori"),
    payment_method_id: int | None = Query(None, description="Filter metode bayar"),
    search: str | None = Query(None, description="Pencarian teks pada catatan"),
    page: int = Query(1, ge=1, description="Nomor halaman"),
    per_page: int = Query(25, ge=1, le=100, description="Item per halaman"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List transaksi dengan filter, pencarian, dan pagination."""
    result = await list_transactions(
        db=db,
        user_id=current_user.id,
        date_from=date_from,
        date_to=date_to,
        category_id=category_id,
        payment_method_id=payment_method_id,
        search=search,
        page=page,
        per_page=per_page,
    )

    message = None
    if result["summary"]["total_filtered"] == 0:
        message = "Tidak ada transaksi ditemukan"

    return StandardResponse(
        status="success",
        data=result,
        message=message,
    ).model_dump()


@router.get("/{tx_id}")
async def get_tx(
    tx_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Detail satu transaksi."""
    result = await get_transaction_detail(db, tx_id, current_user.id)
    return StandardResponse(
        status="success",
        data=result,
    ).model_dump()


@router.post("", status_code=201)
async def create_tx(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Buat transaksi baru. Menerima JSON dan form-urlencoded (HTMX)."""
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        body = await request.json()
        data = TransactionCreate(**body)
    else:
        form = await request.form()
        raw_amount = form.get("amount", "0")
        raw_category_id = form.get("category_id", "0")
        raw_pm = form.get("payment_method_id")
        raw_notes = form.get("notes")
        data = TransactionCreate(
            amount=int(str(raw_amount)) if raw_amount else 0,
            category_id=int(str(raw_category_id)) if raw_category_id else 0,
            transaction_date=str(form["transaction_date"]) if form.get("transaction_date") else None,
            payment_method_id=int(str(raw_pm)) if raw_pm else None,
            notes=str(raw_notes) if raw_notes else None,
        )

    result = await create_transaction(db, current_user.id, data)
    await db.commit()

    # HTMX request: return HTML snippet untuk feedback visual
    if request.headers.get("HX-Request") == "true":
        msg = "✅ Transaksi berhasil disimpan — Rp {:,.0f}</div>".format(result["amount"])
        return HTMLResponse(
            '<div class="flex items-center gap-2 p-3 bg-emerald-50 text-emerald-700 rounded-xl text-sm border border-emerald-200">'
            '<i class="fas fa-check-circle text-emerald-500"></i> '
            + msg,
            status_code=200,
        )

    # Regular API request: return JSON
    return StandardResponse(
        status="success",
        data=result,
        message="Transaksi berhasil disimpan",
    ).model_dump()


@router.put("/{tx_id}")
async def update_tx(
    tx_id: int,
    data: TransactionUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Edit transaksi."""
    result = await update_transaction(db, tx_id, current_user.id, data)
    await db.commit()

    return StandardResponse(
        status="success",
        data=result,
        message="Transaksi berhasil diperbarui",
    ).model_dump()


@router.delete("/{tx_id}")
async def delete_tx(
    tx_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Hapus transaksi."""
    await delete_transaction(db, tx_id, current_user.id)
    await db.commit()

    return StandardResponse(
        status="success",
        message="Transaksi berhasil dihapus",
    ).model_dump()
