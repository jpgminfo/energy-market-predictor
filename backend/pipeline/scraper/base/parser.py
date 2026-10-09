# scraper/base/parser.py
#
# Responsibility: parse raw text into structured rows.
# No I/O, no DB, no storage — pure transformation.
# All functions are stateless and independently testable.
#
# SOLID: single responsibility (parsing only).
# KISS: each function does one thing.
# DRY: shared by all scrapers that read CSV.

import csv
from datetime import datetime
from scraper.base import log


def read_csv(text: str) -> list[list[str]]:
    """Parse CSV text into list of rows."""
    return list(csv.reader(text.splitlines()))


def find_header_row(
    rows: list[list[str]],
    date_keys: tuple[str, ...] = ("DATE", "年月日"),
) -> tuple[int, list[str]] | None:
    """
    Find the first row that contains a date column key.
    Returns (row_index, cleaned_headers) or None if not found.

    date_keys: column names that identify the header row.
    """
    for i, row in enumerate(rows):
        cleaned = [c.strip() for c in row]
        if any(key in cleaned for key in date_keys):
            return i, cleaned
    return None


def detect_interval(data_rows: list[list[str]], time_col: int = 1) -> int:
    """
    Detect trading interval (minutes) from time difference between first two rows.
    Returns 15, 30, or 60. Falls back to 30 if detection fails.
    """
    if len(data_rows) < 2:
        return 30
    try:
        t1 = _parse_time(data_rows[0][time_col])
        t2 = _parse_time(data_rows[1][time_col])
        if t1 is None or t2 is None:
            return 30
        diff = int(abs((t2 - t1).seconds) / 60)
        return diff if diff in (15, 30, 60) else 30
    except (IndexError, ValueError):
        return 30


def _parse_time(time_str: str) -> datetime | None:
    """Parse HH:MM string, treating 24:00 as 00:00."""
    s = time_str.strip()
    if s == "24:00":
        s = "00:00"
    try:
        return datetime.strptime(s, "%H:%M")
    except ValueError:
        return None


def time_to_slot(time_str: str, interval_minutes: int = 30) -> int | None:
    """
    Convert HH:MM to trading slot number (1-based).
    slot 1 = 00:00, slot 2 = 00:30 (for 30min), etc.
    Returns None if parsing fails.
    """
    s = time_str.strip()
    if s == "24:00":
        s = "00:00"
    try:
        dt = datetime.strptime(s, "%H:%M")
        total_minutes = dt.hour * 60 + dt.minute
        return total_minutes // interval_minutes + 1
    except ValueError:
        return None


def parse_date(date_str: str):
    """
    Parse date string to datetime.date.
    Handles: YYYY/M/D, YYYY/MM/DD, YYYYMMDD, YYYY-MM-DD.
    Returns None if all formats fail.
    """
    s = date_str.strip()
    for fmt in ("%Y/%m/%d", "%Y%m%d", "%Y-%m-%d", "%Y/%-m/%-d"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def to_float(val: str) -> float | None:
    """
    Convert string to float.
    Returns None for empty, dash, or unparseable values.
    """
    s = val.strip() if val else ""
    if s in ("", "-", "－", "―", "N/A", "n/a"):
        return None
    try:
        return float(s.replace(",", ""))
    except ValueError:
        return None


def build_col_map(
    headers: list[str],
    header_map: dict[str, str],
) -> dict[str, int]:
    """
    Map master column names to column indices using a Japanese→English header map.

    headers:    cleaned header row from find_header_row
    header_map: dict of {japanese_header: master_column_name}

    Returns: {master_column_name: column_index}
    """
    col_map: dict[str, int] = {}
    for idx, header in enumerate(headers):
        master_col = header_map.get(header)
        if master_col:
            col_map[master_col] = idx
    return col_map


def apply_col_map(
    row: list[str],
    col_map: dict[str, int],
    master_columns: list[str],
) -> dict[str, float | None]:
    """
    Extract values from a data row using col_map.
    Columns in master_columns but not in col_map → None (missing column).

    Returns: {master_column_name: float_or_None}
    """
    result: dict[str, float | None] = {}
    for col in master_columns:
        idx = col_map.get(col)
        if idx is not None:
            try:
                result[col] = to_float(row[idx])
            except IndexError:
                result[col] = None
        else:
            result[col] = None  # TSO doesn't publish this column
    return result
