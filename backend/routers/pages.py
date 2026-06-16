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


@router.post("/login", name="login_post")
async def login_post(request: Request):
    """Handle form login POST — set cookie + redirect."""
    from sqlalchemy.ext.asyncio import AsyncSession
    from ..database import get_db
    from ..services.auth_service import login_user, set_token_cookie
    from ..utils.security import create_access_token

    form = await request.form()
    email = form.get("email")
    password = form.get("password")

    if not email or not password:
        templates = _get_templates()
        return templates.TemplateResponse(
            request,
            "auth/login.html",
            {"current_user": None, "email": email, "error": "Email dan kata sandi wajib diisi."},
            status_code=400,
        )

    db: AsyncSession = await anext(get_db())
    try:
        from ..schemas.auth import LoginRequest
        user = await login_user(db, LoginRequest(email=str(email), password=str(password)))
        token = create_access_token(user.id, user.email)
        response = RedirectResponse(url="/", status_code=302)
        set_token_cookie(response, token)
        return response
    except Exception as e:
        templates = _get_templates()
        return templates.TemplateResponse(
            request,
            "auth/login.html",
            {"current_user": None, "email": email, "error": str(getattr(e, "detail", e))},
            status_code=401,
        )
    finally:
        await db.close()


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


@router.post("/register", name="register_post")
async def register_post(request: Request):
    """Handle form register POST — set cookie + redirect."""
    form = await request.form()
    name = form.get("name")
    email = form.get("email")
    password = form.get("password")
    password_confirm = form.get("password_confirm")

    errors = {}
    if not name:
        errors["name"] = "Nama wajib diisi."
    if not email:
        errors["email"] = "Email wajib diisi."
    if not password:
        errors["password"] = "Kata sandi wajib diisi."
    if password != password_confirm:
        errors["password_confirm"] = "Konfirmasi kata sandi tidak cocok."

    if errors:
        templates = _get_templates()
        return templates.TemplateResponse(
            request,
            "auth/register.html",
            {"current_user": None, "errors": errors, "name": name, "email": email},
            status_code=400,
        )

    from sqlalchemy.ext.asyncio import AsyncSession
    from ..database import get_db
    from ..services.auth_service import register_user, set_token_cookie
    from ..utils.security import create_access_token

    db: AsyncSession = await anext(get_db())
    try:
        from ..schemas.auth import RegisterRequest
        user = await register_user(db, RegisterRequest(
            name=str(name), email=str(email),
            password=str(password), password_confirm=str(password_confirm)
        ))
        await db.commit()
        token = create_access_token(user.id, user.email)
        response = RedirectResponse(url="/", status_code=302)
        set_token_cookie(response, token)
        return response
    except Exception as e:
        await db.rollback()
        templates = _get_templates()
        return templates.TemplateResponse(
            request,
            "auth/register.html",
            {"current_user": None, "errors": {"general": str(getattr(e, "detail", e))},
             "name": name, "email": email},
            status_code=400,
        )
    finally:
        await db.close()


@router.get("/", name="dashboard")
async def dashboard_page(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """Halaman dashboard dengan ringkasan keuangan."""
    from sqlalchemy.ext.asyncio import AsyncSession
    from ..database import get_db
    from datetime import date, datetime

    db: AsyncSession = await anext(get_db())
    try:
        from ..services.stats_service import get_dashboard
        from ..models import Category

        today = date.today()
        data = await get_dashboard(db, current_user.id)

        # Extract values
        today_total = data["today"]["total_amount"]
        today_count = data["today"]["transaction_count"]
        month_total = data["this_month"]["total_amount"]
        month_name = today.strftime("%B %Y")

        # Top category
        top_categories = data.get("top_categories", [])
        if top_categories:
            tc = top_categories[0]
            top_category = {"icon": tc["category"]["icon"], "name": tc["category"]["name"], "amount": tc["total_amount"]}
        else:
            top_category = None

        templates = _get_templates()
        return templates.TemplateResponse(
            request,
            "dashboard.html",
            {
                "current_user": current_user,
                "today_total": today_total,
                "today_count": today_count,
                "month_total": month_total,
                "month_name": month_name,
                "top_category": top_category,
            },
        )
    finally:
        await db.close()


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
