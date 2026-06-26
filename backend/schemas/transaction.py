"""
Pydantic schemas untuk modul transaksi.
"""

from datetime import date

from pydantic import BaseModel, Field, model_validator


class CategoryBrief(BaseModel):
    """Info ringkas kategori dalam response transaksi."""
    id: int
    name: str
    icon: str


class CategoryBriefWithColor(CategoryBrief):
    """Info ringkas kategori dengan warna."""
    color: str | None = None


class PaymentMethodBrief(BaseModel):
    """Info ringkas metode pembayaran."""
    id: int
    name: str
    icon: str


class TransactionCreate(BaseModel):
    """Request body untuk membuat transaksi."""
    amount: int = Field(..., gt=0, description="Jumlah dalam Rupiah (integer)")
    category_id: int = Field(..., gt=0, description="ID kategori")
    transaction_date: date | None = Field(None, description="Tanggal transaksi (opsional, default: hari ini)")
    payment_method_id: int | None = Field(None, gt=0, description="ID metode pembayaran (opsional)")
    notes: str | None = Field(None, max_length=500, description="Catatan (opsional, max 500 karakter)")

    @model_validator(mode="after")
    def validate_future_date(self):
        if self.transaction_date and self.transaction_date > date.today():
            raise ValueError("Tanggal transaksi tidak boleh di masa depan")
        return self


class TransactionUpdate(BaseModel):
    """Request body untuk mengedit transaksi."""
    amount: int = Field(..., gt=0, description="Jumlah dalam Rupiah (integer)")
    category_id: int = Field(..., gt=0, description="ID kategori")
    transaction_date: date = Field(..., description="Tanggal transaksi")
    payment_method_id: int | None = Field(None, gt=0, description="ID metode pembayaran (opsional)")
    notes: str | None = Field(None, max_length=500, description="Catatan (opsional, max 500 karakter)")

    @model_validator(mode="after")
    def validate_future_date(self):
        if self.transaction_date > date.today():
            raise ValueError("Tanggal transaksi tidak boleh di masa depan")
        return self


class TransactionResponse(BaseModel):
    """Response untuk satu transaksi."""
    id: int
    amount: int
    amount_formatted: str
    notes: str | None = None
    tags: list[str] = Field(default_factory=list, description="Tags yang di-parse dari notes")
    transaction_date: str  # YYYY-MM-DD
    transaction_date_formatted: str | None = None
    category: CategoryBrief | None = None
    payment_method: PaymentMethodBrief | None = None
    attachment_url: str | None = Field(None, description="URL ke lampiran transaksi")
    split_count: int = Field(0, description="Jumlah split children (0 jika tidak di-split)")
    created_at: str | None = None
    updated_at: str | None = None

    class Config:
        from_attributes = True


class PaginationInfo(BaseModel):
    """Info pagination."""
    page: int
    per_page: int
    total_items: int
    total_pages: int
    has_next: bool
    has_prev: bool


class TransactionSummary(BaseModel):
    """Ringkasan total dari hasil filter."""
    total_amount: int
    total_amount_formatted: str
    total_filtered: int


class TransactionListResponse(BaseModel):
    """Response untuk list transaksi dengan pagination."""
    transactions: list[TransactionResponse]
    pagination: PaginationInfo
    summary: TransactionSummary


class SplitItem(BaseModel):
    """Satu item dalam split transaksi."""
    category_id: int = Field(..., gt=0)
    amount: int = Field(..., gt=0, description="Jumlah dalam Rupiah")
    notes: str | None = Field(None, max_length=200)

    @model_validator(mode="after")
    def validate_amount_positive(self):
        if self.amount <= 0:
            raise ValueError("Jumlah harus > 0")
        return self


class SplitRequest(BaseModel):
    """Request untuk split transaksi."""
    items: list[SplitItem] = Field(..., min_length=2, max_length=10)

    @model_validator(mode="after")
    def validate_items_unique_category(self):
        cat_ids = [item.category_id for item in self.items]
        if len(cat_ids) != len(set(cat_ids)):
            raise ValueError("Kategori split tidak boleh duplikat")
        return self


class SplitResponse(BaseModel):
    """Response untuk split transaction item."""
    id: int
    category: CategoryBrief
    amount: int
    amount_formatted: str
    notes: str | None = None

    class Config:
        from_attributes = True
