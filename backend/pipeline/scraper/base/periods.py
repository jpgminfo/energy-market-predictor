from datetime import date, datetime, timedelta
from typing import Iterator

YearMonth = tuple[int, int]

def parse_year_month(s: str) -> YearMonth:
    """'YYYY-MM' -> (year, month). Raises ValueError if invalid."""
    try:
        dt = datetime.strptime(s, "%Y-%m")
        return dt.year, dt.month
    except ValueError:
        raise ValueError(f"Invalid year-month format: {s}. Use YYYY-MM.")


def previous_month(today: date | None = None) -> YearMonth:
    """Return (year, month) of the previous month."""
    if today is None:
        today = date.today()
    last = today.replace(day=1) - timedelta(days=1)
    return last.year, last.month


def current_month(today: date | None = None) -> YearMonth:
    """Return (year, month) of the current month."""
    if today is None:
        today = date.today()
    return today.year, today.month


def months_in_range(start: YearMonth, end: YearMonth) -> Iterator[YearMonth]:
    """Generate (year, month) tuples from start to end inclusive."""
    y, m = start
    while (y, m) <= end:
        yield y, m
        y, m = (y + (m // 12), (m % 12) + 1)


def fiscal_year() -> int:
    now = datetime.now()
    return now.year - 1 if now.month <= 3 else now.year
