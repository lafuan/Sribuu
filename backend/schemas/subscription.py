"""
Pydantic schemas untuk modul Subscription (deteksi transaksi berulang).
"""

from datetime import date, datetime

from pydantic import BaseModel, Field


class SubscriptionCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Nama subscription")
    amount: int = Field(..., gt=0, description="Jumlah dalam Rupiah")
    frequency: str = Field(default="monthly", description="Frekuensi: monthly / weekly")
    category_id: int = Field(..., description="ID kategori")
    is_active: bool = Field(default=True, description="Status aktif")


class SubscriptionUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    amount: int | None = Field(None, gt=0)
    frequency: str | None = Field(None)
    category_id: int | None = Field(None)
    is_active: bool | None = Field(None)


class SubscriptionToggle(BaseModel):
    is_active: bool = Field(..., description="Status aktif baru")
