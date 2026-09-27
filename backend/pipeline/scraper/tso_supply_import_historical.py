"""
tso_supply_import_historical.py

Batch import historical TSO area supply/demand data.
Downloads and inserts data month by month for specified year range.

Usage:
    python -m scraper.tso_supply_import_historical
    python -m scraper.tso_supply_import_historical --start 2020-01 --end 2026-08
    python -m scraper.tso_supply_import_historical --areas 03 06 09
"""

import argparse
import time
from datetime import datetime, date
from scraper.tso_supply import run, log_status, TSO_AREA_MAP


def months_in_range(start_year: int, start_month: int,
                    end_year: int, end_month: int):
    """Generate (year, month) tuples from start to end inclusive."""
    y, m = start_year, start_month
    while (y, m) <= (end_year, end_month):
        yield y, m
        m += 1
        if m > 12:
            m = 1
            y += 1


def parse_year_month(ym_str: str):
    """Parse YYYY-MM string to (year, month) tuple."""
    try:
        dt = datetime.strptime(ym_str, '%Y-%m')
        return dt.year, dt.month
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"Invalid year-month format: {ym_str}. Use YYYY-MM."
        )


def run_historical(start_year: int, start_month: int,
                   end_year: int, end_month: int,
                   area_codes: list[str],
                   download: bool = True,
                   delay_seconds: int = 5):
    """
    Import historical data month by month.
    delay_seconds: wait between months to avoid overwhelming TSO servers.
    """
    months = list(months_in_range(start_year, start_month, end_year, end_month))
    total = len(months)

    log_status("INFO", f"Historical import: {total} months × {len(area_codes)} TSOs")
    log_status("INFO", f"Range: {start_year}-{start_month:02d} to {end_year}-{end_month:02d}")
    log_status("INFO", f"Areas: {[TSO_AREA_MAP[c] for c in area_codes]}")

    failed = []

    for i, (year, month) in enumerate(months, 1):
        log_status("INFO", f"[{i}/{total}] Processing {year}-{month:02d}...")
        try:
            run(
                year=year,
                month=month,
                area_codes=area_codes,
                download=download,
            )
        except Exception as e:
            log_status("ERROR", f"Failed {year}-{month:02d}: {e}")
            failed.append((year, month))

        # Be polite to TSO servers — wait between months
        if i < total:
            time.sleep(delay_seconds)

    log_status("SUCCESS", f"Historical import complete. Failed: {len(failed)} months")
    if failed:
        for y, m in failed:
            log_status("WARN", f"  Failed: {y}-{m:02d}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Import historical TSO area supply/demand data"
    )
    parser.add_argument(
        "--start",
        default="2016-04",
        help="Start year-month (YYYY-MM). Default: 2016-04"
    )
    parser.add_argument(
        "--end",
        default=None,
        help="End year-month (YYYY-MM). Default: previous month"
    )
    parser.add_argument(
        "--areas",
        nargs="+",
        default=list(TSO_AREA_MAP.keys()),
        help=f"TSO area codes to process. Default: all. Options: {list(TSO_AREA_MAP.keys())}"
    )
    parser.add_argument(
        "--no-download",
        action="store_true",
        help="Skip download, use existing CSV files in DOWNLOAD_DIR"
    )
    parser.add_argument(
        "--delay",
        type=int,
        default=5,
        help="Seconds to wait between months (default: 5)"
    )

    args = parser.parse_args()

    # Parse start
    start_year, start_month = parse_year_month(args.start)

    # Parse end — default to previous month
    if args.end:
        end_year, end_month = parse_year_month(args.end)
    else:
        today = datetime.today()
        prev = today.replace(day=1) - __import__('datetime').timedelta(days=1)
        end_year, end_month = prev.year, prev.month

    # Validate area codes
    invalid = [c for c in args.areas if c not in TSO_AREA_MAP]
    if invalid:
        print(f"Invalid area codes: {invalid}. Valid: {list(TSO_AREA_MAP.keys())}")
        exit(1)

    run_historical(
        start_year=start_year,
        start_month=start_month,
        end_year=end_year,
        end_month=end_month,
        area_codes=args.areas,
        download=not args.no_download,
        delay_seconds=args.delay,
    )
