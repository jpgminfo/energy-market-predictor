from datetime import date, datetime, timedelta
from typing import Iterator

YearMonth = tuple[int, int]


def parse_period(s: str) -> tuple[int, int | None]:
    """'YYYY-MM' -> (year, month); 'YYYY' -> (year, None). Raises ValueError."""
    s = s.strip()
    for fmt, has_month in (("%Y-%m", True), ("%Y", False)):
        try:
            dt = datetime.strptime(s, fmt)
        except ValueError:
            continue
        return dt.year, (dt.month if has_month else None)
    raise ValueError(f"expected YYYY-MM or YYYY, got {s!r}")


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
    if None in start or None in end:
            raise ValueError(f"months_in_range needs (year, month) pairs, got {start}, {end}")
    y, m = start
    while (y, m) <= end:
        yield y, m
        y, m = (y + (m // 12), (m % 12) + 1)


def fiscal_year() -> int:
    now = datetime.now()
    return now.year - 1 if now.month <= 3 else now.year


def ym_str(year: int, month: int) -> str:
    return f"{year}{month:02d}"

def y_str(year: int) -> str:
    return f"{year}"