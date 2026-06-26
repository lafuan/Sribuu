"""
Router untuk modul Bill (tagihan): CRUD + mark as paid.
"""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import User
from ..schemas.auth import StandardResponse
from ..schemas.bill import BillCreate, BillUpdate
from ..services.auth_service import get_current_user
from ..services.bill_service import (
    create_bill,
    delete_bill,
    get_upcoming_bills,
    list_bills,
    mark_as_paid,
    unmark_paid,
    update_bill,
)

WIB = timezone(timedelta(hours=7))

router = APIRouter(prefix="/api/bills", tags=["Bills"])


def _now_wib() -> datetime:
    return datetime.now(WIB)


@router.get("")
async def list_bills_api(
    request: Request,
    is_paid: bool | None = Query(None, alias="is_paid"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    bills = await list_bills(db, current_user.id, is_paid=is_paid)

    if request.headers.get("HX-Request") == "true":
        from ..main import templates as tpl
        return tpl.TemplateResponse(
            request, "bills/partials/list_items.html",
            {"bills": bills},
        )

    return StandardResponse(status="success", data={"bills": bills}).model_dump()


@router.get("/upcoming")
async def upcoming_bills_api(
    request: Request,
    limit: int = Query(5, ge=1, le=10),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    bills = await get_upcoming_bills(db, current_user.id, limit=limit)

    if request.headers.get("HX-Request") == "true":
        from ..main import templates as tpl
        return tpl.TemplateResponse(
            request, "bills/partials/upcoming.html",
            {"upcoming_bills": bills},
        )

    return StandardResponse(status="success", data={"bills": bills}).model_dump()


@router.post("", status_code=201)
async def create_bill_api(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if request.headers.get("HX-Request") == "true":
        form = await request.form()
        data = BillCreate(
            name=str(form.get("name", "")),
            amount=int(str(form.get("amount", "0"))),
            due_date=datetime.strptime(str(form.get("due_date", "")), "%Y-%m-%d").date(),
            frequency=str(form.get("frequency", "monthly")),
            category_id=int(str(form.get("category_id", "0"))),
        )
    else:
        body = await request.json()
        data = BillCreate(**body)

    bill = await create_bill(db, current_user.id, data)
    await db.commit()

    if request.headers.get("HX-Request") == "true":
        bills = await list_bills(db, current_user.id)
        from ..main import templates as tpl
        return tpl.TemplateResponse(
            request, "bills/partials/list_items.html",
            {"bills": bills},
        )

    return StandardResponse(
        status="success", data=bill, message="Tagihan berhasil ditambahkan"
    ).model_dump()


@router.put("/{bill_id}")
async def update_bill_api(
    bill_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    body = await request.json() if request.headers.get("Content-Type", "").startswith("application/json") else {}
    if request.headers.get("HX-Request") == "true" and not body:
        form = await request.form()
        update_data = {}
        if form.get("name"):
            update_data["name"] = str(form["name"])
        if form.get("amount"):
            update_data["amount"] = int(str(form["amount"]))
        if form.get("due_date"):
            update_data["due_date"] = datetime.strptime(str(form["due_date"]), "%Y-%m-%d").date()
        if form.get("frequency"):
            update_data["frequency"] = str(form["frequency"])
        if form.get("category_id"):
            update_data["category_id"] = int(str(form["category_id"]))
        data = BillUpdate(**update_data)
    else:
        data = BillUpdate(**body)

    bill = await update_bill(db, bill_id, current_user.id, data)
    await db.commit()

    if request.headers.get("HX-Request") == "true":
        bills = await list_bills(db, current_user.id)
        from ..main import templates as tpl
        return tpl.TemplateResponse(
            request, "bills/partials/list_items.html",
            {"bills": bills},
        )

    return StandardResponse(
        status="success", data=bill, message="Tagihan berhasil diperbarui"
    ).model_dump()


@router.delete("/{bill_id}")
async def delete_bill_api(
    bill_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await delete_bill(db, bill_id, current_user.id)
    await db.commit()

    if request.headers.get("HX-Request") == "true":
        bills = await list_bills(db, current_user.id)
        from ..main import templates as tpl
        return tpl.TemplateResponse(
            request, "bills/partials/list_items.html",
            {"bills": bills},
        )

    return StandardResponse(status="success", message="Tagihan berhasil dihapus").model_dump()


@router.post("/{bill_id}/pay")
async def mark_bill_paid(
    bill_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    payment_method_id = 1
    if request.headers.get("HX-Request") == "true":
        form = await request.form()
        pm_str = str(form.get("payment_method_id", "1"))
        if pm_str.isdigit():
            payment_method_id = int(pm_str)

    bill = await mark_as_paid(db, bill_id, current_user.id, payment_method_id)
    await db.commit()

    if request.headers.get("HX-Request") == "true":
        bills = await list_bills(db, current_user.id)
        from ..main import templates as tpl

        source = request.headers.get("HX-Current-URL", "")
        if "/bills" in source:
            return tpl.TemplateResponse(
                request, "bills/partials/list_items.html",
                {"bills": bills},
            )

        response = tpl.TemplateResponse(
            request, "bills/partials/list_items.html",
            {"bills": bills},
        )
        response.headers["HX-Trigger"] = '{"reloadUpcoming": true}'
        return response

    return StandardResponse(
        status="success", data=bill, message="Tagihan ditandai lunas + transaksi dicatat"
    ).model_dump()


@router.post("/{bill_id}/unpay")
async def unmark_bill_paid(
    bill_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    bill = await unmark_paid(db, bill_id, current_user.id)
    await db.commit()

    if request.headers.get("HX-Request") == "true":
        bills = await list_bills(db, current_user.id)
        from ..main import templates as tpl
        return tpl.TemplateResponse(
            request, "bills/partials/list_items.html",
            {"bills": bills},
        )

    return StandardResponse(status="success", data=bill, message="Lunas dibatalkan").model_dump()
