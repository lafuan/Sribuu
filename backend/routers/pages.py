"""
Router untuk page routes (HTML).
"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse

from ..models import User
from ..services.auth_service import get_current_user

router = APIRouter(tags=["Pages"])

# Try to import templates lazily
_templates = None


def _get_templates():
    global _templates
    if _templates is None:
        from ..main import templates
        _templates = templates
    return _templates


async def _optional_user(request: Request):
    """Dapatkan user jika login, None jika tidak."""
    try:
        return await get_current_user(request)
    except Exception:
        return None


@router.get("/login")
async def login_page(request: Request):
    """Halaman login. Redirect ke / jika sudah login."""
    user = await _optional_user(request)
    if user:
        return RedirectResponse(url="/", status_code=302)

    templates = _get_templates()
    return templates.TemplateResponse(
        "auth/login.html",
        {"request": request, "current_user": None},
    )


@router.get("/register")
async def register_page(request: Request):
    """Halaman registrasi. Redirect ke / jika sudah login."""
    user = await _optional_user(request)
    if user:
        return RedirectResponse(url="/", status_code=302)

    templates = _get_templates()
    return templates.TemplateResponse(
        "auth/register.html",
        {"request": request, "current_user": None},
    )


@router.get("/")
async def dashboard_page(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """Halaman dashboard."""
    templates = _get_templates()
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "current_user": current_user},
    )


@router.get("/transactions")
async def transactions_page(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """Halaman riwayat transaksi."""
    templates = _get_templates()
    return templates.TemplateResponse(
        "transactions/list.html",
        {"request": request, "current_user": current_user},
    )


@router.get("/transactions/new")
async def transactions_new_page(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """Halaman form input transaksi baru."""
    templates = _get_templates()
    return templates.TemplateResponse(
        "transactions/form.html",
        {"request": request, "current_user": current_user},
    )


@router.get("/transactions/{tx_id}/edit")
async def transactions_edit_page(
    tx_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """Halaman form edit transaksi."""
    templates = _get_templates()
    return templates.TemplateResponse(
        "transactions/form.html",
        {
            "request": request,
            "current_user": current_user,
            "tx_id": tx_id,
        },
    )


@router.get("/stats")
async def stats_page(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """Halaman statistik."""
    templates = _get_templates()
    return templates.TemplateResponse(
        "stats/index.html",
        {"request": request, "current_user": current_user},
    )


@router.get("/settings")
async def settings_page(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """Halaman pengaturan (redirect ke kategori)."""
    return RedirectResponse(url="/settings/categories", status_code=302)


@router.get("/settings/categories")
async def settings_categories_page(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """Halaman kelola kategori."""
    templates = _get_templates()
    return templates.TemplateResponse(
        "settings/categories.html",
        {"request": request, "current_user": current_user},
    )


@router.get("/settings/password")
async def settings_password_page(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """Halaman ganti password."""
    templates = _get_templates()
    return templates.TemplateResponse(
        "settings/password.html",
        {"request": request, "current_user": current_user},
    )
