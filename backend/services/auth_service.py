"""
Service layer untuk autentikasi: register, login, get_current_user.
"""

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..database import get_db
from ..models import User
from ..schemas.auth import LoginRequest, PasswordChangeRequest, RegisterRequest
from ..utils.security import (
    get_token_expiry_days,
    hash_password,
    verify_access_token,
    verify_password,
)


async def register_user(db: AsyncSession, data: RegisterRequest) -> User:
    """Registrasi user baru. Raise HTTPException jika email sudah terdaftar."""
    # Cek email (case-insensitive)
    result = await db.execute(
        select(User).where(User.email.ilike(data.email.strip()))
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "status": "error",
                "data": None,
                "message": "Email sudah terdaftar",
                "errors": {"email": ["Email sudah terdaftar"]},
            },
        )

    user = User(
        name=data.name.strip(),
        email=data.email.strip().lower(),
        password_hash=hash_password(data.password),
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


async def login_user(db: AsyncSession, data: LoginRequest) -> User:
    """Login user. Raise HTTPException jika kredensial salah."""
    result = await db.execute(
        select(User).where(User.email.ilike(data.email.strip()))
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "status": "error",
                "data": None,
                "message": "Email atau password salah",
                "errors": None,
            },
        )

    return user


async def change_password(
    db: AsyncSession, user_id: int, data: PasswordChangeRequest
) -> None:
    """Ganti password user. Raise HTTPException jika password lama salah."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one()

    if not verify_password(data.old_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "status": "error",
                "data": None,
                "message": "Gagal mengubah password",
                "errors": {"old_password": ["Password lama tidak sesuai"]},
            },
        )

    user.password_hash = hash_password(data.new_password)
    await db.flush()


def set_token_cookie(response, token: str) -> None:
    """Set JWT token ke HTTP-only cookie."""
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=not settings.DEBUG,  # True in production (DEBUG=False)
        samesite="lax",
        max_age=get_token_expiry_days() * 86400,
        path="/",
    )


def clear_token_cookie(response) -> None:
    """Hapus cookie token."""
    response.delete_cookie(
        key="access_token",
        path="/",
        httponly=True,
        secure=not settings.DEBUG,
        samesite="lax",
    )


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    """Dependency: dapatkan user dari JWT token di cookie."""
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "status": "error",
                "data": None,
                "message": "Silakan login terlebih dahulu",
                "errors": None,
            },
        )

    payload = verify_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "status": "error",
                "data": None,
                "message": "Sesi telah berakhir. Silakan login kembali",
                "errors": None,
            },
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "status": "error",
                "data": None,
                "message": "Token tidak valid",
                "errors": None,
            },
        )

    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "status": "error",
                "data": None,
                "message": "Pengguna tidak ditemukan",
                "errors": None,
            },
        )

    return user


def to_user_response(user: User) -> dict:
    """Konversi User model ke dict response."""
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
    }
