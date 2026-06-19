"""Pydantic schemas untuk modul TransactionTemplate (Favorit Transaksi)."""

from datetime import datetime

from pydantic import BaseModel, Field

from .transaction import CategoryBrief, PaymentMethodBrief


class TransactionTemplateCreate(BaseModel):
    """Request body untuk membuat template transaksi."""
    label: str = Field(..., min_length=1, max_length=50, description="Nama label tombol")
    amount: int = Field(..., gt=0, description="Jumlah dalam Rupiah")
    category_id: int = Field(..., gt=0, description="ID kategori")
    payment_method_id: int | None = Field(None, description="ID metode pembayaran (opsional)")
    notes: str | None = Field(None, max_length=500, description="Catatan (opsional)")
    sort_order: int = Field(0, description="Urutan tampilan")


class TransactionTemplateUpdate(BaseModel):
    """Request body untuk mengupdate template transaksi."""
    label: str = Field(..., min_length=1, max_length=50)
    amount: int = Field(..., gt=0)
    category_id: int = Field(..., gt=0)
    payment_method_id: int | None = Field(None)
    notes: str | None = Field(None, max_length=500)
    sort_order: int = Field(0)


class TransactionTemplateResponse(BaseModel):
    """Response untuk satu template transaksi."""
    id: int
    label: str
    amount: int
    amount_formatted: str | None = None
    notes: str | None = None
    sort_order: int
    category: CategoryBrief | None = None
    payment_method: PaymentMethodBrief | None = None
    created_at: str | None = None

    class Config:
        from_attributes = True


class TransactionTemplateListResponse(BaseModel):
    """Response untuk list template transaksi."""
    templates: list[TransactionTemplateResponse]
    total: int
