"""
Pydantic schemas untuk modul kategori.
"""

from pydantic import BaseModel, Field


class CategoryCreate(BaseModel):
    """Request body untuk membuat kategori kustom."""
    name: str = Field(..., min_length=1, max_length=50, description="Nama kategori")
    icon: str = Field("📦", min_length=1, max_length=5, description="Emoji ikon (1-2 karakter)")
    color: str = Field("#6b7280", pattern=r"^#[0-9a-fA-F]{6}$", description="Warna hex (#RRGGBB)")


class CategoryUpdate(BaseModel):
    """Request body untuk mengedit kategori."""
    name: str = Field(..., min_length=1, max_length=50, description="Nama kategori")
    icon: str = Field("📦", min_length=1, max_length=5, description="Emoji ikon")
    color: str = Field("#6b7280", pattern=r"^#[0-9a-fA-F]{6}$", description="Warna hex")


class CategoryResponse(BaseModel):
    """Response untuk satu kategori."""
    id: int
    name: str
    icon: str
    color: str
    is_default: bool
    is_active: bool
    transaction_count: int = 0

    class Config:
        from_attributes = True


class CategoryListResponse(BaseModel):
    """Response untuk list kategori."""
    categories: list[CategoryResponse]


class CategoryToggleResponse(BaseModel):
    """Response untuk toggle kategori."""
    id: int
    name: str
    is_active: bool
