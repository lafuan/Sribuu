"""
Pydantic schemas untuk modul statistik.
"""

from pydantic import BaseModel


class TodaySummary(BaseModel):
    """Ringkasan pengeluaran hari ini."""
    total_amount: int
    total_amount_formatted: str
    transaction_count: int


class MonthSummary(BaseModel):
    """Ringkasan pengeluaran bulan ini."""
    total_amount: int
    total_amount_formatted: str
    transaction_count: int
    month_label: str


class TopCategory(BaseModel):
    """Kategori dengan pengeluaran tertinggi."""
    category: dict  # {id, name, icon, color}
    total_amount: int
    total_amount_formatted: str
    percentage: float


class DashboardResponse(BaseModel):
    """Response untuk dashboard."""
    today: TodaySummary
    this_month: MonthSummary
    top_categories: list[TopCategory]
    recent_transactions: list  # list TransactionResponse


class CategoryBreakdown(BaseModel):
    """Item dalam breakdown per kategori."""
    category: dict  # {id, name, icon, color}
    total_amount: int
    total_amount_formatted: str
    percentage: float
    transaction_count: int


class ByCategoryResponse(BaseModel):
    """Response untuk statistik by-category."""
    date_from: str
    date_to: str
    total_amount: int
    total_amount_formatted: str
    categories: list[CategoryBreakdown]


class DailyTrendItem(BaseModel):
    """Item tren harian."""
    date: str
    date_formatted: str
    day_name: str
    total_amount: int
    total_amount_formatted: str
    transaction_count: int


class DailyTrendResponse(BaseModel):
    """Response untuk tren harian."""
    date_from: str
    date_to: str
    daily: list[DailyTrendItem]
    max_amount: int


class MonthlyComparison(BaseModel):
    """Perbandingan dengan bulan sebelumnya."""
    previous_total: int
    previous_total_formatted: str
    difference: int
    difference_formatted: str
    percentage_change: float


class HighestTransaction(BaseModel):
    """Transaksi tertinggi dalam sebulan."""
    id: int
    amount: int
    amount_formatted: str
    category: dict
    transaction_date: str


class MonthlyResponse(BaseModel):
    """Response untuk statistik bulanan."""
    year: int
    month: int
    month_label: str
    total_amount: int
    total_amount_formatted: str
    transaction_count: int
    daily_average: int
    daily_average_formatted: str
    highest_transaction: HighestTransaction | None = None
    comparison_previous_month: MonthlyComparison | None = None


class MonthlyComparisonItem(BaseModel):
    """Item per bulan dalam perbandingan bulanan."""
    year: int
    month: int
    label: str
    total_amount: int
    total_amount_formatted: str
    transaction_count: int


class MonthlyComparisonResponse(BaseModel):
    """Response untuk perbandingan multi-bulan."""
    months: list[MonthlyComparisonItem]
    max_amount: int
