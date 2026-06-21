"""
Router untuk modul transaksi: CRUD, filter, pagination.
"""

from datetime import date
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile, status
from fastapi.responses import FileResponse, HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import User
from ..schemas.auth import StandardResponse
from ..schemas.transaction import TransactionCreate, TransactionUpdate
from ..services.auth_service import get_current_user
from ..services.transaction_service import (
    create_transaction,
    delete_transaction,
    get_transaction_by_id,
    get_transaction_detail,
    list_transactions,
    update_transaction,
)

router = APIRouter(prefix="/api/transactions", tags=["Transactions"])

# Allowed file extensions and max size
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "frontend" / "static" / "uploads"


@router.get("")
async def list_tx(
    request: Request,
    date_from: date | None = Query(None, description="Awal rentang tanggal"),
    date_to: date | None = Query(None, description="Akhir rentang tanggal"),
    category_id: int | None = Query(None, description="Filter kategori"),
    payment_method_id: int | None = Query(None, description="Filter metode bayar"),
    search: str | None = Query(None, description="Pencarian teks pada catatan"),
    tag: str | None = Query(None, description="Filter tag (contoh: kerja)"),
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
        tag=tag,
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
    from pydantic import ValidationError

    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        body = await request.json()
        try:
            data = TransactionCreate(**body)
        except ValidationError as e:
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=422,
                content={
                    "detail": {
                        "status": "error",
                        "data": None,
                        "message": "Validasi gagal",
                        "errors": e.errors(),
                    }
                },
            )
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
    tx = await get_transaction_by_id(db, tx_id, current_user.id)

    # Delete attachment file if exists
    if tx.attachment_path:
        _delete_attachment_file(tx.attachment_path)

    await delete_transaction(db, tx_id, current_user.id)
    await db.commit()

    return StandardResponse(
        status="success",
        message="Transaksi berhasil dihapus",
    ).model_dump()


@router.post("/{tx_id}/attachment")
async def upload_attachment(
    tx_id: int,
    request: Request,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload lampiran foto untuk transaksi."""
    tx = await get_transaction_by_id(db, tx_id, current_user.id)

    # Validate file type
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "status": "error",
                "message": f"Tipe file tidak diizinkan. Gunakan: {', '.join(ALLOWED_EXTENSIONS)}",
            },
        )

    # Read and validate file size
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "status": "error",
                "message": "Ukuran file maksimal 5MB",
            },
        )

    # Delete existing attachment if any
    if tx.attachment_path:
        _delete_attachment_file(tx.attachment_path)

    # Build storage path: uploads/{user_id}/{tx_id}.{ext}
    user_dir = UPLOAD_DIR / str(current_user.id)
    user_dir.mkdir(parents=True, exist_ok=True)
    storage_path = user_dir / f"{tx_id}{ext}"
    relative_path = f"uploads/{current_user.id}/{tx_id}{ext}"

    # Write file
    with open(storage_path, "wb") as f:
        f.write(contents)

    # Update database
    tx.attachment_path = relative_path
    await db.commit()

    return StandardResponse(
        status="success",
        data={"attachment_url": f"/api/transactions/{tx_id}/attachment"},
        message="Lampiran berhasil diunggah",
    ).model_dump()


@router.get("/{tx_id}/attachment")
async def get_attachment(
    tx_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Ambil lampiran transaksi."""
    tx = await get_transaction_by_id(db, tx_id, current_user.id)

    if not tx.attachment_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"status": "error", "message": "Lampiran tidak ditemukan"},
        )

    file_path = Path(__file__).resolve().parent.parent.parent / "frontend" / "static" / tx.attachment_path
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"status": "error", "message": "File lampiran tidak ditemukan"},
        )

    # Determine media type
    ext = file_path.suffix.lower()
    media_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
    }
    media_type = media_types.get(ext, "application/octet-stream")

    return FileResponse(
        str(file_path),
        media_type=media_type,
        filename=file_path.name,
    )


@router.delete("/{tx_id}/attachment")
async def delete_attachment(
    tx_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Hapus lampiran transaksi."""
    tx = await get_transaction_by_id(db, tx_id, current_user.id)

    if not tx.attachment_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"status": "error", "message": "Lampiran tidak ditemukan"},
        )

    _delete_attachment_file(tx.attachment_path)

    tx.attachment_path = None
    await db.commit()

    return StandardResponse(
        status="success",
        message="Lampiran berhasil dihapus",
    ).model_dump()


def _delete_attachment_file(attachment_path: str) -> None:
    """Delete attachment file from disk."""
    try:
        file_path = Path(__file__).resolve().parent.parent.parent / "frontend" / "static" / attachment_path
        if file_path.exists():
            file_path.unlink()
    except OSError:
        pass  # Ignore errors during file deletion (file may already be gone)
