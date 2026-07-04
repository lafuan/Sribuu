"""Shared date & time utilities for Western Indonesia Time (WIB)."""

from datetime import date, datetime, timedelta, timezone

WIB = timezone(timedelta(hours=7))


def today_wib() -> date:
    """Current date in Western Indonesia Time (UTC+7)."""
    return datetime.now(WIB).date()


def start_of_month(year: int, month: int) -> date:
    """First day of the given month."""
    return date(year, month, 1)


def end_of_month(year: int, month: int) -> date:
    """Last day of the given month."""
    if month == 12:
        return date(year, month, 31)
    return date(year, month + 1, 1) - timedelta(days=1)
