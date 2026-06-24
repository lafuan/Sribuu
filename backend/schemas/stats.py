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


class ForecastDay(BaseModel):
    """Data forecast per hari."""
    date: str
    date_formatted: str
    day_name: str
    predicted_expense: int
    predicted_expense_formatted: str
    cumulative_expense: int
    cumulative_expense_formatted: str
    predicted_balance: int
    predicted_balance_formatted: str
    is_recurring: bool = False
    recurring_note: str | None = None


class CashFlowForecastResponse(BaseModel):
    """Response untuk Cash Flow Forecast."""
    current_balance: int
    current_balance_formatted: str
    end_of_month_balance: int
    end_of_month_balance_formatted: str
    total_predicted_expense: int
    total_predicted_expense_formatted: str
    daily_forecast: list[ForecastDay]
    forecast_end_date: str
    warning: str | None = None
    safe_balance: int | None = None
    confidence: float  # 0.0 - 1.0
    recurring_transactions: list[dict]
    monthly_avg_based_on: list[dict]  # [{month, total, label}]
