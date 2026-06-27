"""
Router untuk modul Subscription: deteksi & manajemen transaksi berulang.
"""

from datetime import timedelta, timezone

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import User
from ..schemas.auth import StandardResponse
from ..schemas.subscription import SubscriptionCreate, SubscriptionToggle, SubscriptionUpdate
from ..services.auth_service import get_current_user
from ..services.subscription_service import (
    create_subscription,
    delete_subscription,
    detect_subscriptions,
    get_subscription_summary,
    list_subscriptions,
    run_detection_and_save,
    toggle_subscription,
    update_subscription,
)

WIB = timezone(timedelta(hours=7))

router = APIRouter(prefix="/api/subscriptions", tags=["Subscriptions"])


@router.get("")
async def list_subscriptions_api(
    request: Request,
    is_active: bool | None = Query(None, alias="is_active"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    subs = await list_subscriptions(db, current_user.id, is_active=is_active)

    if request.headers.get("HX-Request") == "true":
        from ..main import templates as tpl
        summary = await get_subscription_summary(db, current_user.id)
        return tpl.TemplateResponse(
            request, "subscriptions/partials/list_items.html",
            {"subscriptions": subs, "summary": summary},
        )

    summary = await get_subscription_summary(db, current_user.id)
    return StandardResponse(status="success", data={
        "subscriptions": subs,
        "summary": summary,
    }).model_dump()


@router.get("/summary")
async def subscription_summary_api(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    summary = await get_subscription_summary(db, current_user.id)
    return StandardResponse(status="success", data=summary).model_dump()


@router.get("/detect")
async def detect_subscriptions_api(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Deteksi transaksi berulang tanpa menyimpan."""
    detected = await detect_subscriptions(db, current_user.id)
    return StandardResponse(
        status="success",
        data={"detected": detected, "count": len(detected)},
    ).model_dump()


@router.post("/detect-save")
async def detect_and_save_api(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Deteksi + simpan ke database."""
    result = await run_detection_and_save(db, current_user.id)
    await db.commit()

    if request.headers.get("HX-Request") == "true":
        from ..main import templates as tpl
        return tpl.TemplateResponse(
            request, "subscriptions/partials/list_items.html",
            {
                "subscriptions": result["subscriptions"],
                "summary": result["summary"],
                "detected_message": f"Terdeteksi {result['detected_count']} subscription baru!",
            },
        )

    return StandardResponse(
        status="success",
        data=result,
        message=f"Deteksi selesai: {result['detected_count']} subscription ditemukan",
    ).model_dump()


@router.post("", status_code=201)
async def create_subscription_api(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if request.headers.get("HX-Request") == "true":
        form = await request.form()
        data = SubscriptionCreate(
            name=str(form.get("name", "")),
            amount=int(str(form.get("amount", "0"))),
            frequency=str(form.get("frequency", "monthly")),
            category_id=int(str(form.get("category_id", "0"))),
        )
    else:
        body = await request.json()
        data = SubscriptionCreate(**body)

    sub = await create_subscription(db, current_user.id, data)
    await db.commit()

    if request.headers.get("HX-Request") == "true":
        subs = await list_subscriptions(db, current_user.id)
        summary = await get_subscription_summary(db, current_user.id)
        from ..main import templates as tpl
        return tpl.TemplateResponse(
            request, "subscriptions/partials/list_items.html",
            {"subscriptions": subs, "summary": summary},
        )

    return StandardResponse(
        status="success", data=sub, message="Subscription berhasil ditambahkan"
    ).model_dump()


@router.put("/{sub_id}")
async def update_subscription_api(
    sub_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    body = await request.json() if request.headers.get("Content-Type", "").startswith("application/json") else {}
    if request.headers.get("HX-Request") == "true" and not body:
        form = await request.form()
        update_data: dict[str, int | str | None] = {}
        if form.get("name"):
            update_data["name"] = str(form["name"])
        if form.get("amount"):
            update_data["amount"] = int(str(form["amount"]))
        if form.get("frequency"):
            update_data["frequency"] = str(form["frequency"])
        if form.get("category_id"):
            update_data["category_id"] = int(str(form["category_id"]))
        data = SubscriptionUpdate(**update_data)  # type: ignore[arg-type]
    else:
        data = SubscriptionUpdate(**body)

    sub = await update_subscription(db, sub_id, current_user.id, data)
    await db.commit()

    if request.headers.get("HX-Request") == "true":
        subs = await list_subscriptions(db, current_user.id)
        summary = await get_subscription_summary(db, current_user.id)
        from ..main import templates as tpl
        return tpl.TemplateResponse(
            request, "subscriptions/partials/list_items.html",
            {"subscriptions": subs, "summary": summary},
        )

    return StandardResponse(
        status="success", data=sub, message="Subscription berhasil diperbarui"
    ).model_dump()


@router.delete("/{sub_id}")
async def delete_subscription_api(
    sub_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await delete_subscription(db, sub_id, current_user.id)
    await db.commit()

    if request.headers.get("HX-Request") == "true":
        subs = await list_subscriptions(db, current_user.id)
        summary = await get_subscription_summary(db, current_user.id)
        from ..main import templates as tpl
        return tpl.TemplateResponse(
            request, "subscriptions/partials/list_items.html",
            {"subscriptions": subs, "summary": summary},
        )

    return StandardResponse(status="success", message="Subscription berhasil dihapus").model_dump()


@router.post("/{sub_id}/toggle")
async def toggle_subscription_api(
    sub_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if request.headers.get("HX-Request") == "true":
        form = await request.form()
        is_active = str(form.get("is_active", "true")).lower() == "true"
    else:
        body = await request.json()
        is_active = body.get("is_active", True)

    sub = await toggle_subscription(db, sub_id, current_user.id, is_active)
    await db.commit()

    if request.headers.get("HX-Request") == "true":
        subs = await list_subscriptions(db, current_user.id)
        summary = await get_subscription_summary(db, current_user.id)
        from ..main import templates as tpl
        return tpl.TemplateResponse(
            request, "subscriptions/partials/list_items.html",
            {"subscriptions": subs, "summary": summary},
        )

    return StandardResponse(
        status="success", data=sub,
        message=f"Subscription {'diaktifkan' if is_active else 'dinonaktifkan'}"
    ).model_dump()


@router.post("/{sub_id}/toggle-json")
async def toggle_subscription_json_api(
    sub_id: int,
    body: SubscriptionToggle,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    sub = await toggle_subscription(db, sub_id, current_user.id, body.is_active)
    await db.commit()
    return StandardResponse(
        status="success", data=sub,
        message=f"Subscription {'diaktifkan' if body.is_active else 'dinonaktifkan'}"
    ).model_dump()
