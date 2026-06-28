"""
Pydantic schemas untuk Rule Engine.
"""
from datetime import datetime

from pydantic import BaseModel, Field


class RuleCreate(BaseModel):
    """Request body untuk membuat rule baru."""
    name: str = Field(..., max_length=100, description="Nama rule")
    match_keywords: str = Field(..., max_length=500, description="Keyword (comma-separated)")
    category_id: int = Field(..., description="ID kategori target")
    match_mode: str = Field("contains", description="contains | exact | startswith")
    priority: int = Field(0, ge=0, description="Prioritas (makin tinggi = dicek duluan)")


class RuleUpdate(BaseModel):
    """Request body untuk update rule."""
    name: str | None = Field(None, max_length=100)
    match_keywords: str | None = Field(None, max_length=500)
    category_id: int | None = Field(None)
    match_mode: str | None = Field(None, description="contains | exact | startswith")
    is_active: bool | None = Field(None)
    priority: int | None = Field(None, ge=0)


class RuleResponse(BaseModel):
    """Response untuk rule."""
    id: int
    name: str
    match_keywords: str
    category_id: int
    category_name: str | None = None
    category_icon: str | None = None
    category_color: str | None = None
    match_mode: str
    is_active: bool
    priority: int
    match_count: int
    last_matched_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
