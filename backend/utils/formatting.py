"""
Formatting utilities: Rupiah, tanggal Indonesia.
"""

from datetime import date, datetime

# Nama bulan dalam Bahasa Indonesia
BULAN_ID = [
    "", "Januari", "Februari", "Maret", "April", "Mei", "Juni",
    "Juli", "Agustus", "September", "Oktober", "November", "Desember"
]

BULAN_ID_SHORT = [
    "", "Jan", "Feb", "Mar", "Apr", "Mei", "Jun",
    "Jul", "Agu", "Sep", "Okt", "Nov", "Des"
]

# Nama hari dalam Bahasa Indonesia
HARI_ID = ["Sen", "Sel", "Rab", "Kam", "Jum", "Sab", "Min"]


def format_rupiah(amount: int, with_rp: bool = True) -> str:
    """Format integer ke string Rupiah. Contoh: 45000 → 'Rp 45.000'"""
    # Gunakan locale-independent formatting
    formatted = f"{amount:,.0f}".replace(",", ".")
    if with_rp:
        return f"Rp {formatted}"
    return formatted


def format_date_id(d: date | str, fmt: str = "long") -> str:
    """Format tanggal ke string Indonesia.

    fmt: 'long' (15 Juni 2026), 'short' (15/06), 'iso' (2026-06-15)
    """
    if isinstance(d, str):
        d = date.fromisoformat(d)

    if fmt == "iso":
        return d.isoformat()
    elif fmt == "short":
        return f"{d.day:02d}/{d.month:02d}"
    else:  # long
        return f"{d.day} {BULAN_ID[d.month]} {d.year}"


def format_date_id_short(d: date) -> str:
    """Format: '15 Jun 2026'"""
    if isinstance(d, str):
        d = date.fromisoformat(d)
    return f"{d.day} {BULAN_ID_SHORT[d.month]} {d.year}"


def get_day_name_id(d: date) -> str:
    """Dapatkan nama hari dalam Bahasa Indonesia."""
    # Python weekday(): 0=Senin, 6=Minggu
    return HARI_ID[d.weekday()]


def get_month_label(year: int, month: int) -> str:
    """Format label bulan. Contoh: (2026, 6) → 'Juni 2026'"""
    return f"{BULAN_ID[month]} {year}"


def format_datetime_id(dt: datetime | None) -> str | None:
    """Format datetime ke ISO 8601 dengan timezone WIB."""
    if dt is None:
        return None
    return dt.replace(microsecond=0).isoformat()
