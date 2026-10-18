# scraper/jepx.py
#
# JEPX spot market scraper.
# Responsibility: JEPX-specific fetch, parse, and insert logic only.
# All shared logic delegated to scraper/base/.

from datetime import datetime, timedelta
from scraper.base import setup_logger, timestamp, FetchError, ParseError
from scraper.base import fetcher
from scraper.base import storage as st
from scraper.base.parser import (
    read_csv,
    find_header_row,
    detect_interval,
    time_to_slot,
    parse_date,
    to_float,
)
from scraper.base.inserter import upsert

logger = setup_logger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

JEPX_URL = "https://www.jepx.jp/electricpower/market-data/spot/"

# JEPX CSV column index → area_code mapping
# Columns 6-14 in CSV correspond to area prices 01-09
AREA_COLUMNS = {
    6:  "HOKKAIDO",
    7:  "TOHOKU",
    8:  "TOKYO",
    9:  "CHUBU",
    10: "HOKURIKU",
    11: "KANSAI",
    12: "CHUGOKU",
    13: "SHIKOKU",
    14: "KYUSHU",
}

# DB columns for jepx_spot_summary
SUMMARY_COLUMNS = [
    "target_date", "trading_slot", "interval_minutes",
    "system_price",
    "sell_bid_amount", "buy_bid_amount", "total_contract_amount",
    "sell_block_bid_amount", "sell_block_contract_amount",
    "buy_block_bid_amount", "buy_block_contract_amount",
]

# DB columns for jepx_spot_prices
PRICES_COLUMNS = [
    "target_date", "trading_slot", "area_code",
    "interval_minutes", "area_price",
]

# ── Fiscal year helpers ───────────────────────────────────────────────────────

def fiscal_year() -> int:
    now = datetime.now()
    return now.year - 1 if now.month <= 3 else now.year


def storage_path(fy: int) -> str:
    return f"jepx/spot_summary_{fy}.csv"


# ── Fetch ─────────────────────────────────────────────────────────────────────

def _interact(page) -> None:
    """Playwright interaction to trigger JEPX CSV download."""
    fy = fiscal_year()

    # Open download modal
    page.locator(
        "section:nth-of-type(6) ul li:nth-child(3) button"
    ).click()

    # Wait for modal and select fiscal year
    page.wait_for_selector("#dl-select--spot_summary", state="visible")
    page.locator("#dl-select--spot_summary").select_option(
        f"spot_summary_{fy}.csv"
    )

    # Click submit button (not the close button)
    page.locator("#modal-box--spot_summary button[type='submit']").click()


def fetch(fy: int | None = None) -> str:
    """
    Download JEPX spot summary CSV via browser and stage in Supabase Storage.
    Returns storage_path on success.
    Raises FetchError on failure.
    """
    fy = fy or fiscal_year()
    path = storage_path(fy)
    logger.info(f"Fetching JEPX spot summary FY{fy}")
    return fetcher.fetch_browser(
        url=JEPX_URL,
        storage_path=path,
        interact=_interact,
    )


# ── Parse ─────────────────────────────────────────────────────────────────────

def parse(fy: int | None = None) -> tuple[list[dict], list[dict]]:
    """
    Download and parse JEPX CSV from Supabase Storage.
    Returns (summaries, prices) — two lists of dicts ready for DB insert.
    Raises ParseError if CSV cannot be parsed.
    """
    fy = fy or fiscal_year()
    path = storage_path(fy)

    text = st.download_text(path, encoding="shift_jis")
    rows = read_csv(text)

    # JEPX CSV has 3 header rows — skip to data
    # Row 0: blank/title
    # Row 1: column names in Japanese
    # Row 2: units
    # Row 3+: data
    data_rows = [r for r in rows[3:] if r and r[0].strip()]

    if not data_rows:
        raise ParseError(f"No data rows found in JEPX CSV FY{fy}")

    interval = detect_interval(data_rows)
    logger.info(f"Detected {interval}min interval for JEPX FY{fy}")

    summaries: list[dict] = []
    prices: list[dict] = []

    for row in data_rows:
        if len(row) < 15:
            continue

        target_date = parse_date(row[0])
        if not target_date:
            continue

        slot = time_to_slot(row[1], interval)
        if not slot:
            continue

        # Market-wide summary row
        summaries.append({
            "target_date":              target_date,
            "trading_slot":             slot,
            "interval_minutes":         interval,
            "system_price":             to_float(row[5]),
            "sell_bid_amount":          to_float(row[2]),
            "buy_bid_amount":           to_float(row[3]),
            "total_contract_amount":    to_float(row[4]),
            "sell_block_bid_amount":    to_float(row[15]) if len(row) > 15 else None,
            "sell_block_contract_amount": to_float(row[16]) if len(row) > 16 else None,
            "buy_block_bid_amount":     to_float(row[17]) if len(row) > 17 else None,
            "buy_block_contract_amount": to_float(row[18]) if len(row) > 18 else None,
        })

        # One price row per area
        for col_idx, area_code in AREA_COLUMNS.items():
            prices.append({
                "target_date":      target_date,
                "trading_slot":     slot,
                "area_code":        area_code,
                "interval_minutes": interval,
                "area_price":       to_float(row[col_idx]),
            })

    logger.info(
        f"Parsed JEPX FY{fy}: {len(summaries)} slots, {len(prices)} area price rows"
    )
    return summaries, prices


# ── Insert ────────────────────────────────────────────────────────────────────

def insert(summaries: list[dict], prices: list[dict]) -> None:
    """
    Insert parsed JEPX data into PostgreSQL.
    Uses generic upsert from base/inserter.py.
    """
    upsert(
        rows=summaries,
        table="jepx_spot_summary",
        columns=SUMMARY_COLUMNS,
        conflict_columns=["target_date", "trading_slot"],
    )
    upsert(
        rows=prices,
        table="jepx_spot_prices",
        columns=PRICES_COLUMNS,
        conflict_columns=["target_date", "trading_slot", "area_code"],
    )


# ── Main entry point ──────────────────────────────────────────────────────────

def run(fy: int | None = None, download: bool = True) -> None:
    """
    Full pipeline: fetch → parse → insert → archive.

    fy:       fiscal year to process (defaults to current)
    download: if False, use existing file in storage (skip fetch)
    """
    fy = fy or fiscal_year()
    path = storage_path(fy)

    logger.info(f"JEPX scraper starting — FY{fy}")

    if download:
        fetch(fy)

    summaries, prices = parse(fy)
    insert(summaries, prices)
    st.archive(path)

    logger.info(f"JEPX scraper completed — FY{fy}")


if __name__ == "__main__":
    run(download=True)
