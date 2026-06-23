"""
Pydantic schemas untuk modul budget.
"""

from pydantic import BaseModel, Field


class BudgetCreate(BaseModel):
    """Request body untuk membuat budget baru."""
    category_id: int = Field(..., description="ID kategori")
    month: int = Field(..., ge=1, le=12, description="Bulan (1-12)")
    year: int = Field(..., description="Tahun")
    amount: int = Field(..., gt=0, description="Jumlah budget dalam Rupiah")


class BudgetUpdate(BaseModel):
    """Request body untuk mengedit budget (hanya amount)."""
    amount: int = Field(..., gt=0, description="Jumlah budget baru dalam Rupiah")


class BudgetBulkCreateItem(BaseModel):
    """Single item untuk bulk create."""
    category_id: int = Field(..., description="ID kategori")
    month: int = Field(..., ge=1, le=12, description="Bulan (1-12)")
    year: int = Field(..., description="Tahun")
    amount: int = Field(..., gt=0, description="Jumlah budget dalam Rupiah")


class BudgetBulkCreate(BaseModel):
    """Request body untuk membuat multiple budgets sekaligus."""
    budgets: list[BudgetBulkCreateItem]
