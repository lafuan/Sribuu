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
    """Request body untuk mengedit budget (amount + rollover)."""
    amount: int | None = Field(None, gt=0, description="Jumlah budget baru dalam Rupiah")
    rollover: int | None = Field(None, ge=0, description="Sisa budget bulan lalu yang di-rollover")


class BudgetBulkCreateItem(BaseModel):
    """Single item untuk bulk create."""
    category_id: int = Field(..., description="ID kategori")
    month: int = Field(..., ge=1, le=12, description="Bulan (1-12)")
    year: int = Field(..., description="Tahun")
    amount: int = Field(..., gt=0, description="Jumlah budget dalam Rupiah")
    rollover: int = Field(0, ge=0, description="Sisa budget bulan lalu (rollover)")


class BudgetBulkCreate(BaseModel):
    """Request body untuk membuat multiple budgets sekaligus."""
    budgets: list[BudgetBulkCreateItem]
