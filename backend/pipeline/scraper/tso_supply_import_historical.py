"""
Usage:
    python -m scraper.tso_supply_import_historical
    python -m scraper.tso_supply_import_historical --start 2020-01 --end 2026-08
    python -m scraper.tso_supply_import_historical --areas 03 06 09
"""

import argparse
import time
from pipeline.scraper.base.periods import months_in_range, parse_year_month, previous_month
from pipeline.scraper.tso_supply import run, TSO_AREA_MAP
from pipeline import setup_logger

logger = setup_logger(__name__)


def run_historical(start, end, area_codes, download=True, delay_seconds=5):
    """
    Import historical data month by month.
    delay_seconds: wait between months to avoid overwhelming TSO servers.
    """
    months = list(months_in_range(start, end))

    logger.info(f"Historical import: {len(months)} months × {len(area_codes)} TSOs")
    logger.info(f"Range: {start[0]}-{start[1]:02d} to {end[0]}-{end[1]:02d}")
    logger.info(f"Areas: {[TSO_AREA_MAP[c] for c in area_codes]}")

    failed: list[str] = []

    for i, (year, month) in enumerate(months, 1):
        logger.info(f"[{i}/{len(months)}] Processing {year}-{month:02d}...")
        try:
            for code in run(year=year, month=month, area_codes=area_codes, download=download):
                failed.append(f"{year}-{month:02d} {code} ({TSO_AREA_MAP[code]})")
        except Exception as e:
            logger.error(f"Failed {year}-{month:02d}: {e}")
            failed.append(f"{year}-{month:02d} (whole month aborted)")

        # Be polite to TSO servers — wait between months
        if i < len(months):
            time.sleep(delay_seconds)

    logger.info(f"Historical import complete. Failed: {len(failed)}")
    for item in failed:
            logger.warning(f"  Failed: {item}")


def main() -> None:
    p = argparse.ArgumentParser(
        description="Import historical TSO area supply/demand data")
    p.add_argument("--start", type=parse_year_month, default="2016-04",
                    help="Start year-month (YYYY-MM). Default: 2016-04")
    p.add_argument("--end", type=parse_year_month, default=None,
                    help="End year-month (YYYY-MM). Default: previous month")
    p.add_argument("--areas", nargs="+", choices=list(TSO_AREA_MAP), default=list(TSO_AREA_MAP),
                    metavar="CODE", help=f"TSO area codes to process. Default: all. Options: {list(TSO_AREA_MAP.keys())}")
    p.add_argument("--no-download", action="store_true",
                    help="Skip fetching; parse files already staged in Supabase Storage")
    p.add_argument("--delay", type=int, default=5,
                    help="Seconds to wait between months (default: 5)")
    args = p.parse_args()

    run_historical(args.start, args.end or previous_month(), args.areas,
                    download=not args.no_download, delay_seconds=args.delay)

if __name__ == "__main__":
    main()