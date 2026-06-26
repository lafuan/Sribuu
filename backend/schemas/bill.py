"""
Pydantic schemas untuk modul Bill (tagihan).
"""

from datetime import date

from pydantic import BaseModel, Field


class BillCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Nama tagihan")
    amount: int = Field(..., gt=0, description="Jumlah tagihan dalam Rupiah")
    due_date: date = Field(..., description="Tanggal jatuh tempo")
    frequency: str = Field(default="monthly", description="Frekuensi: monthly / yearly")
    category_id: int = Field(..., description="ID kategori pengeluaran")


class BillUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100, description="Nama tagihan")
    amount: int | None = Field(None, gt=0, description="Jumlah tagihan")
    due_date: date | None = Field(None, description="Tanggal jatuh tempo")
    frequency: str | None = Field(None, description="Frekuensi: monthly / yearly")
    category_id: int | None = Field(None, description="ID kategori")
