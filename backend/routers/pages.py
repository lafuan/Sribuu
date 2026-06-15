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


@router.get("/login", name="login_page")
async def login_page(request: Request):
    """Halaman login. Redirect ke / jika sudah login."""
    user = await _optional_user(request)
    if user:
        return RedirectResponse(url="/", status_code=302)

    templates = _get_templates()
    return templates.TemplateResponse(
        request,
        "auth/login.html",
        {"current_user": None},
    )


@router.get("/register", name="register_page")
async def register_page(request: Request):
    """Halaman registrasi. Redirect ke / jika sudah login."""
    user = await _optional_user(request)
    if user:
        return RedirectResponse(url="/", status_code=302)

    templates = _get_templates()
    return templates.TemplateResponse(
        request,
        "auth/register.html",
        {"current_user": None},
    )


@router.get("/", name="dashboard")
async def dashboard_page(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """Halaman dashboard."""
    templates = _get_templates()
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {"current_user": current_user},
    )


@router.get("/transactions", name="transactions_list")
async def transactions_page(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """Halaman riwayat transaksi."""
    templates = _get_templates()
    return templates.TemplateResponse(
        request,
        "transactions/list.html",
        {"current_user": current_user},
    )


@router.get("/transactions/new", name="transactions_new")
async def transactions_new_page(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """Halaman form input transaksi baru."""
    templates = _get_templates()
    return templates.TemplateResponse(
        request,
        "transactions/form.html",
        {"current_user": current_user},
    )


@router.get("/transactions/{tx_id}/edit", name="transactions_edit")
async def transactions_edit_page(
    tx_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """Halaman form edit transaksi."""
    templates = _get_templates()
    return templates.TemplateResponse(
        request,
        "transactions/form.html",
        {"current_user": current_user, "tx_id": tx_id},
    )


@router.get("/stats", name="stats")
async def stats_page(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """Halaman statistik."""
    templates = _get_templates()
    return templates.TemplateResponse(
        request,
        "stats.html",
        {"current_user": current_user},
    )


@router.get("/settings", name="settings")
async def settings_page(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """Halaman pengaturan."""
    templates = _get_templates()
    return templates.TemplateResponse(
        request,
        "settings.html",
        {"current_user": current_user},
    )


@router.get("/settings/password", name="settings_password")
async def settings_password_page(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """Halaman ganti password."""
    templates = _get_templates()
    return templates.TemplateResponse(
        request,
        "settings.html",
        {"current_user": current_user, "active_tab": "password"},
    )
