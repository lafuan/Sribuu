"""
Router untuk modul autentikasi: register, login, logout, me, password.
"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import User
from ..schemas.auth import (
    LoginRequest,
    PasswordChangeRequest,
    RegisterRequest,
    StandardResponse,
)
from ..services.auth_service import (
    change_password,
    clear_token_cookie,
    get_current_user,
    login_user,
    register_user,
    set_token_cookie,
    to_user_response,
)

router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.post("/register", status_code=201)
async def register(
    data: RegisterRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Registrasi user baru. Setelah berhasil, auto-login."""
    user = await register_user(db, data)
    await db.commit()

    # Buat token dan set cookie
    token = _make_token(user)

    content = StandardResponse(
        status="success",
        data={
            "user": to_user_response(user),
            "redirect": "/",
        },
        message="Registrasi berhasil. Selamat datang!",
    ).model_dump()

    response = JSONResponse(content=content, status_code=201)
    set_token_cookie(response, token)
    return response


@router.post("/login")
async def login(
    data: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Login user."""
    user = await login_user(db, data)
    token = _make_token(user)

    content = StandardResponse(
        status="success",
        data={
            "user": to_user_response(user),
            "redirect": "/",
        },
    ).model_dump()

    response = JSONResponse(content=content)
    set_token_cookie(response, token)
    return response


@router.post("/logout")
async def logout(request: Request):
    """Logout user."""
    content = StandardResponse(
        status="success",
        data={"redirect": "/login"},
        message="Anda telah logout",
    ).model_dump()

    response = JSONResponse(content=content)
    clear_token_cookie(response)
    return response


@router.get("/me")
async def get_me(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """Dapatkan info user yang sedang login."""
    return StandardResponse(
        status="success",
        data={"user": to_user_response(current_user)},
    ).model_dump()


@router.put("/password")
async def update_password(
    data: PasswordChangeRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Ganti password."""
    await change_password(db, current_user.id, data)
    await db.commit()

    return StandardResponse(
        status="success",
        message="Password berhasil diubah",
    ).model_dump()


def _make_token(user: User) -> str:
    """Helper: buat JWT token untuk user."""
    from ..utils.security import create_access_token
    return create_access_token(user.id, user.email)
