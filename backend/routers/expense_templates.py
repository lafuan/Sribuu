"""Router untuk modul TransactionTemplate (Favorit Transaksi)."""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db, get_db_session
from ..main import templates as jinja_templates
from ..models import User
from ..schemas.auth import StandardResponse
from ..schemas.template import TransactionTemplateCreate, TransactionTemplateUpdate
from ..services.auth_service import get_current_user
from ..services.template_service import (
    create_template,
    delete_template,
    list_templates,
    update_template,
)

router = APIRouter(prefix="/api/templates", tags=["Templates"])


@router.get("/manage-modal")
async def manage_templates_modal(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """HTMX partial: modal untuk manage templates."""
    db = get_db_session()
    try:
        from ..services.category_service import list_categories

        categories = await list_categories(db, current_user.id)
    finally:
        await db.close()

    return jinja_templates.TemplateResponse(
        request,
        "transactions/partials/manage_templates_modal.html",
        {"current_user": current_user, "categories": categories},
    )


@router.get("/manage-list")
async def manage_templates_list(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """HTMX partial: list template untuk manage modal."""
    db = get_db_session()
    try:
        result = await list_templates(db, current_user.id)
    finally:
        await db.close()

    return jinja_templates.TemplateResponse(
        request,
        "transactions/partials/template_manage_list.html",
        {"current_user": current_user, "templates": result},
    )


@router.get("")
async def list_tx_templates(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List semua template milik user."""
    result = await list_templates(db, current_user.id)
    return StandardResponse(
        status="success",
        data={"templates": result, "total": len(result)},
    ).model_dump()


@router.get("/partials/list")
async def list_templates_partial(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """HTMX partial: render template quick buttons."""
    db2 = get_db_session()
    try:
        result = await list_templates(db2, current_user.id)
    finally:
        await db2.close()

    return jinja_templates.TemplateResponse(
        request,
        "transactions/partials/template_buttons.html",
        {"current_user": current_user, "templates": result},
    )


@router.post("", status_code=201)
async def create_tx_template(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Buat template transaksi baru."""
    from pydantic import ValidationError

    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        body = await request.json()
        try:
            data = TransactionTemplateCreate(**body)
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
        data = TransactionTemplateCreate(
            label=str(form.get("label", "")),
            amount=int(str(form.get("amount", "0"))),
            category_id=int(str(form.get("category_id", "0"))),
            payment_method_id=int(str(form.get("payment_method_id", "0"))) if form.get("payment_method_id") else None,
            notes=str(form.get("notes", "")) or None,
            sort_order=int(str(form.get("sort_order", "0"))),
        )

    result = await create_template(db, current_user.id, data)
    await db.commit()

    # HTMX request: return updated template list partial
    if request.headers.get("HX-Request") == "true":
        all_templates = await list_templates(db, current_user.id)
        # Return both success message + updated buttons
        return HTMLResponse(
            '<div id="template-feedback" class="text-xs text-emerald-600 mb-2">'
            f'✅ Template "{result["label"]}" berhasil dibuat</div>'
            + await _render_template_buttons(all_templates),
        )

    return StandardResponse(
        status="success",
        data=result,
        message="Template berhasil dibuat",
    ).model_dump()


@router.put("/{template_id}")
async def update_tx_template(
    template_id: int,
    data: TransactionTemplateUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update template transaksi."""
    result = await update_template(db, template_id, current_user.id, data)
    await db.commit()

    return StandardResponse(
        status="success",
        data=result,
        message="Template berhasil diperbarui",
    ).model_dump()


@router.delete("/{template_id}")
async def delete_tx_template(
    template_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Hapus template transaksi."""
    await delete_template(db, template_id, current_user.id)
    await db.commit()

    if request.headers.get("HX-Request") == "true":
        all_templates = await list_templates(db, current_user.id)
        return HTMLResponse(await _render_template_buttons(all_templates))

    return StandardResponse(
        status="success",
        message="Template berhasil dihapus",
    ).model_dump()


async def _render_template_buttons(templates: list) -> str:
    """Render template buttons HTML."""
    if not templates:
        return '<div id="template-buttons"><p class="text-xs text-stone-400">Belum ada template.</p></div>'

    buttons_html = '<div id="template-buttons" class="flex flex-wrap gap-1.5 mt-2">'
    for t in templates[:12]:  # max 12 templates
        cat_icon = t.get("category", {}).get("icon", "📦") if t.get("category") else "📦"
        buttons_html += (
            f'<button type="button" class="template-quick-btn text-xs px-3 py-1.5 rounded-lg border border-stone-200 '
            f'hover:bg-emerald-50 hover:border-emerald-300 transition-colors flex items-center gap-1 cursor-pointer" '
            f'data-amount="{t["amount"]}" '
            f'data-category-id="{t["category"]["id"] if t.get("category") else ""}" '
            f'data-notes="{t.get("notes", "")}" '
            f'data-label="{t["label"]}">'
            f'{cat_icon} {t["label"]}'
            f'</button>'
        )
    buttons_html += '</div>'
    return buttons_html
