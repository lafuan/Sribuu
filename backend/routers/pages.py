"""
Router untuk page routes (HTML).
"""

from datetime import date

from fastapi import APIRouter, Depends, Query, Request
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
    """Dapatkan user jika login, None jika tidak.
    Version ini panggil DB langsung (tanpa Depends) agar bisa dipanggil
    dari fungsi non-DI seperti handler redirect."""
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession

    from ..database import get_db
    from ..models import User
    from ..utils.security import verify_access_token

    token = request.cookies.get("access_token")
    if not token:
        return None

    payload = verify_access_token(token)
    if not payload:
        return None

    user_id = payload.get("sub")
    if not user_id:
        return None

    db: AsyncSession = await anext(get_db())
    try:
        result = await db.execute(select(User).where(User.id == int(user_id)))
        return result.scalar_one_or_none()
    except Exception:
        return None
    finally:
        await db.close()


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


@router.get("/logout", name="logout")
async def logout_page():
    """Logout user — clear cookie + redirect ke login."""
    from ..services.auth_service import clear_token_cookie
    response = RedirectResponse(url="/login", status_code=302)
    clear_token_cookie(response)
    return response


@router.get("/", name="dashboard")
async def dashboard_page(
    request: Request,
    current_user: User | None = Depends(_optional_user),
):
    """Halaman dashboard dengan ringkasan keuangan."""
    if current_user is None:
        return RedirectResponse(url="/login", status_code=302)

    from sqlalchemy.ext.asyncio import AsyncSession
    from ..database import get_db
    from datetime import date, datetime

    db: AsyncSession = await anext(get_db())
    try:
        from ..services.stats_service import get_dashboard
        from ..models import Category
        from ..services.category_service import list_categories

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

        # Categories for quick-add form
        categories = await list_categories(db, current_user.id)

        # Payment methods for quick-add form
        from sqlalchemy import select
        from ..models import PaymentMethod
        pm_result = await db.execute(
            select(PaymentMethod)
            .where(PaymentMethod.is_active == 1)
            .order_by(PaymentMethod.id)
        )
        payment_methods = [
            {"id": m.id, "name": m.name, "icon": m.icon}
            for m in pm_result.scalars().all()
        ]

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
                "categories": categories,
                "payment_methods": payment_methods,
            },
        )
    finally:
        await db.close()


@router.get("/transactions", name="transactions_list")
async def transactions_page(
    request: Request,
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    category_id: int | None = Query(None),
    payment_method_id: int | None = Query(None),
    search: str | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    current_user: User = Depends(get_current_user),
):
    """Halaman riwayat transaksi."""
    from urllib.parse import urlencode

    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession

    from ..database import get_db
    from ..models import PaymentMethod
    from ..services.category_service import list_categories
    from ..services.transaction_service import list_transactions

    db: AsyncSession = await anext(get_db())
    try:
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

        categories = await list_categories(db, current_user.id)

        pm_result = await db.execute(
            select(PaymentMethod)
            .where(PaymentMethod.is_active == 1)
            .order_by(PaymentMethod.id)
        )
        payment_methods = [
            {"id": m.id, "name": m.name, "icon": m.icon}
            for m in pm_result.scalars().all()
        ]

        transactions = [
            {
                "id": tx["id"],
                "amount": tx["amount"],
                "notes": tx["notes"],
                "transaction_date": tx["transaction_date"],
                "created_at": tx["created_at"],
                "category_name": tx["category"]["name"] if tx["category"] else "",
                "category_icon": tx["category"]["icon"] if tx["category"] else "",
                "payment_name": tx["payment_method"]["name"] if tx["payment_method"] else "",
                "payment_icon": tx["payment_method"]["icon"] if tx["payment_method"] else "",
            }
            for tx in result["transactions"]
        ]

        pagination = result["pagination"]
        summary = result["summary"]

        filters = {
            "date_from": date_from.isoformat() if date_from else "",
            "date_to": date_to.isoformat() if date_to else "",
            "category_id": category_id or "",
            "payment_method_id": payment_method_id or "",
            "search": search or "",
        }
        query_string = urlencode({k: v for k, v in filters.items() if v})

        templates = _get_templates()
        return templates.TemplateResponse(
            request,
            "transactions/list.html",
            {
                "current_user": current_user,
                "transactions": transactions,
                "categories": categories,
                "payment_methods": payment_methods,
                "filters": filters,
                "query_string": query_string,
                "total_amount": summary["total_amount"],
                "total_items": pagination["total_items"],
                "total_pages": pagination["total_pages"],
                "page": pagination["page"],
                "page_size": pagination["per_page"],
            },
        )
    finally:
        await db.close()


@router.get("/transactions/new", name="transactions_new")
async def transactions_new_page(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """Halaman form input transaksi baru."""
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession

    from ..database import get_db
    from ..models import PaymentMethod
    from ..services.category_service import list_categories

    db: AsyncSession = await anext(get_db())
    try:
        categories = await list_categories(db, current_user.id)
        pm_result = await db.execute(
            select(PaymentMethod)
            .where(PaymentMethod.is_active == 1)
            .order_by(PaymentMethod.id)
        )
        payment_methods = [
            {"id": m.id, "name": m.name, "icon": m.icon}
            for m in pm_result.scalars().all()
        ]

        templates = _get_templates()
        return templates.TemplateResponse(
            request,
            "transactions/form.html",
            {
                "current_user": current_user,
                "categories": categories,
                "payment_methods": payment_methods,
            },
        )
    finally:
        await db.close()


@router.get("/transactions/{tx_id}/edit", name="transactions_edit")
async def transactions_edit_page(
    tx_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """Halaman form edit transaksi."""
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession

    from ..database import get_db
    from ..models import PaymentMethod
    from ..services.category_service import list_categories
    from ..services.transaction_service import get_transaction_detail

    db: AsyncSession = await anext(get_db())
    try:
        categories = await list_categories(db, current_user.id)
        pm_result = await db.execute(
            select(PaymentMethod)
            .where(PaymentMethod.is_active == 1)
            .order_by(PaymentMethod.id)
        )
        payment_methods = [
            {"id": m.id, "name": m.name, "icon": m.icon}
            for m in pm_result.scalars().all()
        ]

        # Fetch existing transaction data for edit form
        try:
            tx_detail = await get_transaction_detail(db, tx_id, current_user.id)
            form_data = {
                "amount": tx_detail["amount"],
                "category_id": tx_detail["category"]["id"],
                "payment_method_id": tx_detail["payment_method"]["id"],
                "notes": tx_detail["notes"],
            }
        except Exception:
            form_data = {}

        templates = _get_templates()
        return templates.TemplateResponse(
            request,
            "transactions/form.html",
            {
                "current_user": current_user,
                "tx_id": tx_id,
                "categories": categories,
                "payment_methods": payment_methods,
                "form_data": form_data,
            },
        )
    finally:
        await db.close()


@router.get("/stats", name="stats")
async def stats_page(
    request: Request,
    year: int | None = None,
    month: int | None = None,
    current_user: User = Depends(get_current_user),
):
    """Halaman statistik."""
    from sqlalchemy.ext.asyncio import AsyncSession
    from datetime import date, timedelta

    from ..database import get_db
    from ..services.stats_service import (
        get_monthly_stats,
        get_stats_by_category,
        get_daily_trend,
        get_monthly_comparison,
    )

    today = date.today()
    if not year:
        year = today.year
    if not month:
        month = today.month

    month_start = date(year, month, 1)
    if month == 12:
        month_end = date(year, 12, 31)
    else:
        month_end = date(year, month + 1, 1) - timedelta(days=1)

    db: AsyncSession = await anext(get_db())
    try:
        monthly = await get_monthly_stats(db, current_user.id, year=year, month=month)
        by_category = await get_stats_by_category(
            db, current_user.id, date_from=month_start, date_to=month_end
        )
        daily = await get_daily_trend(
            db, current_user.id, date_from=month_start, date_to=month_end
        )
        comparison = await get_monthly_comparison(db, current_user.id, months=3)

        highest_tx = monthly.get("highest_transaction")
        summary = {
            "total": monthly["total_amount"],
            "count": monthly["transaction_count"],
            "avg_per_day": monthly["daily_average"],
            "highest": highest_tx["amount"] if highest_tx else 0,
        }

        category_stats = [
            {
                "name": c["category"]["name"],
                "icon": c["category"]["icon"],
                "color": c["category"]["color"],
                "amount": c["total_amount"],
                "percentage": c["percentage"],
            }
            for c in by_category["categories"]
        ]

        daily_trend = [
            {"date_label": d["date_formatted"], "amount": d["total_amount"]}
            for d in daily["daily"]
        ]

        month_comparisons = [
            {"month_label": m["label"], "amount": m["total_amount"]}
            for m in reversed(comparison["months"])
        ]

        templates = _get_templates()
        return templates.TemplateResponse(
            request,
            "stats.html",
            {
                "current_user": current_user,
                "current_year": year,
                "current_month": month,
                "summary": summary,
                "category_stats": category_stats,
                "daily_trend": daily_trend,
                "month_comparisons": month_comparisons,
            },
        )
    finally:
        await db.close()


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
