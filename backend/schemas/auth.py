"""
Pydantic schemas untuk modul autentikasi.
"""

from pydantic import BaseModel, EmailStr, Field, model_validator


class RegisterRequest(BaseModel):
    """Request body untuk registrasi."""
    name: str = Field(..., min_length=2, max_length=100, description="Nama lengkap")
    email: EmailStr = Field(..., description="Email (case-insensitive)")
    password: str = Field(..., min_length=6, max_length=128, description="Password (min 6 karakter)")
    password_confirm: str = Field(..., description="Konfirmasi password")

    @model_validator(mode="after")
    def validate_passwords_match(self):
        if self.password != self.password_confirm:
            raise ValueError("Password dan konfirmasi tidak sama")
        return self


class LoginRequest(BaseModel):
    """Request body untuk login."""
    email: EmailStr = Field(..., description="Email terdaftar")
    password: str = Field(..., min_length=1, description="Password")


class PasswordChangeRequest(BaseModel):
    """Request body untuk ganti password."""
    old_password: str = Field(..., min_length=1, description="Password lama")
    new_password: str = Field(..., min_length=6, max_length=128, description="Password baru (min 6 karakter)")
    new_password_confirm: str = Field(..., description="Konfirmasi password baru")

    @model_validator(mode="after")
    def validate_passwords_match(self):
        if self.new_password != self.new_password_confirm:
            raise ValueError("Password baru dan konfirmasi tidak sama")
        return self


class UserResponse(BaseModel):
    """Response data user (tanpa password hash)."""
    id: int
    name: str
    email: str

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Response setelah login/register berhasil."""
    user: UserResponse
    redirect: str = "/"


class StandardResponse(BaseModel):
    """Format response standar API."""
    status: str  # "success" | "error"
    data: dict | list | None = None
    message: str | None = None
    errors: dict | None = None
