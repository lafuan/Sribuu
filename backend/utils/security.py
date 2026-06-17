"""
Keamanan: password hashing (bcrypt) dan JWT token.
"""

from datetime import datetime, timedelta, timezone
from typing import cast

from jose import JWTError, jwt
from passlib.context import CryptContext

from ..config import settings

# Bcrypt context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# WIB timezone
WIB = timezone(timedelta(hours=7))


def hash_password(password: str) -> str:
    """Hash password dengan bcrypt."""
    return pwd_context.hash(password)  # type: ignore[no-any-return]


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifikasi password terhadap hash."""
    return pwd_context.verify(plain_password, hashed_password)  # type: ignore[no-any-return]


def create_access_token(user_id: int, email: str) -> str:
    """Buat JWT access token."""
    expire = datetime.now(WIB) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "email": email,
        "exp": expire,
        "iat": datetime.now(WIB),
    }
    return cast(str, jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM))


def verify_access_token(token: str) -> dict | None:
    """Verifikasi JWT token, kembalikan payload atau None."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return cast(dict, payload)
    except JWTError:
        return None


def get_token_expiry_days() -> int:
    """Dapatkan masa berlaku token dalam hari (untuk cookie max_age)."""
    return settings.ACCESS_TOKEN_EXPIRE_MINUTES // (60 * 24)
