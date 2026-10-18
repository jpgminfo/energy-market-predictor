# scraper/tso_supply.py
#
# TSO area supply/demand scraper (でんき予報 — 9 TSOs).
# Responsibility: TSO-specific fetch, parse, and insert logic only.
# All shared logic delegated to scraper/base/.

from datetime import datetime, timedelta
from scraper.base import setup_logger, FetchError, ParseError
from scraper.base import fetcher
from scraper.base import storage as st
from scraper.base.parser import (
    read_csv,
    find_header_row,
    detect_interval,
    time_to_slot,
    parse_date,
    build_col_map,
    apply_col_map,
)
from scraper.base.inserter import upsert

logger = setup_logger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

# TSO file suffix → areas table area_code
TSO_AREA_MAP = {
    "01": "HOKKAIDO",
    "02": "TOHOKU",
    "03": "TOKYO",
    "04": "CHUBU",
    "05": "HOKURIKU",
    "06": "KANSAI",
    "07": "CHUGOKU",
    "08": "SHIKOKU",
    "09": "KYUSHU",
}

# Master column set — canonical order matching tso_area_supply_demand table
# Columns missing in a TSO's CSV → NULL
MASTER_COLUMNS = [
    "area_demand",
    "nuclear",
    "thermal_lng",
    "thermal_coal",
    "thermal_oil",
    "thermal_other",
    "thermal_curtailment",
    "thermal_total",        # computed: sum of thermal detail cols, or direct 2016 value
    "hydro",
    "geothermal",
    "biomass_actual",
    "biomass_curtailment",
    "solar_actual",
    "solar_curtailment",
    "wind_actual",
    "wind_curtailment",
    "pumped_storage",
    "battery",
    "interconnection",
    "other",
    "total_supply",
]

# DB columns for upsert
DB_COLUMNS = [
    "target_date", "trading_slot", "area_code", "interval_minutes",
] + MASTER_COLUMNS

# Japanese header → master column name
# Handles full-width/half-width bracket variants across TSOs
HEADER_MAP = {
    "エリア需要":             "area_demand",
    "原子力":                 "nuclear",
    # 2016 era — single thermal column → thermal_total directly
    "火力":                   "thermal_total",
    # 2026 era — split thermal columns
    "火力(LNG)":              "thermal_lng",
    "火力（LNG）":            "thermal_lng",
    "火力（ＬＮＧ）":        "thermal_lng",
    "火力(石炭)":             "thermal_coal",
    "火力（石炭）":           "thermal_coal",
    "火力(石油)":             "thermal_oil",
    "火力（石油）":           "thermal_oil",
    "火力(その他)":           "thermal_other",
    "火力（その他）":         "thermal_other",
    "火力出力制御量":         "thermal_curtailment",
    "水力":                   "hydro",
    "地熱":                   "geothermal",
    "バイオマス":             "biomass_actual",
    "バイオマス発電実績":     "biomass_actual",
    "バイオマス出力制御量":   "biomass_curtailment",
    "太陽光発電実績":         "solar_actual",
    "太陽光出力制御量":       "solar_curtailment",
    "風力発電実績":           "wind_actual",
    "風力出力制御量":         "wind_curtailment",
    "揚水":                   "pumped_storage",
    "蓄電池":                 "battery",
    "連系線":                 "interconnection",
    "その他":                 "other",
    "合計":                   "total_supply",
}

# Direct HTTP download URLs per TSO
DIRECT_URLS = {
    "01": lambda ym: f"https://www.hepco.co.jp/network/con_service/public_document/supply_demand_results/csv/eria_jukyu_{ym}_01.csv",
    "03": lambda ym: f"https://www.tepco.co.jp/forecast/html/images/eria_jukyu_{ym}_03.csv",
    "04": lambda ym: f"https://powergrid.chuden.co.jp/denki_yoho_content_data/eria_jukyu_{ym}_04.csv",
    "06": lambda ym: f"https://www.kansai-td.co.jp/interchange/denkiyoho/area-performance/eria_jukyu_{ym}_06.csv",
    "08": lambda ym: f"https://www.yonden.co.jp/nw/supply_demand/csv/eria_jukyu_{ym}_08.csv",
    "09": lambda ym: f"https://www.kyuden.co.jp/td_area_jukyu/csv/eria_jukyu_{ym}_09.csv?17390810",
}

TOHOKU_URL   = lambda year, m0: f"https://setsuden.nw.tohoku-epco.co.jp/get_realtime_jukyu.php?year={year}&month={m0}"
HOKURIKU_URL = "https://www.rikuden.co.jp/nw/denki-yoho/results_jyukyu.html"
CHUGOKU_URL  = "https://www.energia.co.jp/nw/jukyuu/eria_jukyu.html"

# ── Helpers ───────────────────────────────────────────────────────────────────

def _prev_year_month() -> tuple[int, int]:
    today = datetime.today()
    target = today.replace(day=1) - timedelta(days=1)
    return target.year, target.month


def _ym_str(year: int, month: int) -> str:
    return f"{year}{month:02d}"


def _storage_path(area_code: str, ym: str) -> str:
    return f"tso/eria_jukyu_{ym}_{area_code}.csv"


# ── Fetch ─────────────────────────────────────────────────────────────────────

def _interact_hokuriku(year: int, month: int):
    """Return Playwright interact callable for Hokuriku (05)."""
    def interact(page):
        page.locator("[name='year']").select_option(str(year))
        page.locator("[name='month']").select_option(str(month))
        page.locator(
            "/html/body/div[3]/div[3]/div/div/div/div[2]/div/form/ul/li[1]/a"
        ).click()
    return interact


def _interact_chugoku(year: int, month: int):
    """Return Playwright interact callable for Chugoku (07)."""
    def interact(page):
        page.locator("[name='year']").select_option(str(year))
        page.locator("[name='month']").select_option(str(month))
        page.locator("[id*='download']").click()
    return interact


def fetch_one(area_code: str, year: int, month: int) -> str:
    """
    Fetch one TSO's CSV and stage in Supabase Storage.
    Routes to correct fetch strategy per TSO.
    Returns storage_path on success.
    Raises FetchError on failure.
    """
    ym = _ym_str(year, month)
    path = _storage_path(area_code, ym)

    if area_code in DIRECT_URLS:
        url = DIRECT_URLS[area_code](ym)
        return fetcher.fetch_http(url, path)

    elif area_code == "02":
        url = TOHOKU_URL(year, f"{month:02d}")
        return fetcher.fetch_zip_concat(url, path, skip_header_rows=2)

    elif area_code == "05":
        return fetcher.fetch_browser(
            url=HOKURIKU_URL,
            storage_path=path,
            interact=_interact_hokuriku(year, month),
        )

    elif area_code == "07":
        return fetcher.fetch_browser(
            url=CHUGOKU_URL,
            storage_path=path,
            interact=_interact_chugoku(year, month),
        )

    else:
        raise FetchError(f"No fetch strategy for area_code: {area_code}")


# ── Parse ─────────────────────────────────────────────────────────────────────

def _compute_thermal_total(vals: dict) -> dict:
    """
    Compute thermal_total from detail columns if not already set.
    2016 era: thermal_total already set from single '火力' column.
    2026 era: sum thermal_lng + thermal_coal + thermal_oil + thermal_other.
    """
    if vals.get("thermal_total") is not None:
        return vals  # 2016 era — already set

    parts = [
        vals.get("thermal_lng"),
        vals.get("thermal_coal"),
        vals.get("thermal_oil"),
        vals.get("thermal_other"),
    ]
    valid = [p for p in parts if p is not None]
    vals["thermal_total"] = sum(valid) if valid else None
    return vals


def parse_one(area_code: str, year: int, month: int) -> list[dict]:
    """
    Download and parse one TSO's CSV from Supabase Storage.
    Returns list of dicts ready for DB insert.
    Raises ParseError if CSV cannot be parsed.
    """
    area_db_code = TSO_AREA_MAP.get(area_code)
    if not area_db_code:
        raise ParseError(f"No area mapping for area_code: {area_code}")

    ym = _ym_str(year, month)
    path = _storage_path(area_code, ym)

    text = st.download_text(path)
    all_rows = read_csv(text)

    result = find_header_row(all_rows)
    if not result:
        raise ParseError(
            f"Cannot find header row in TSO {area_code} CSV ({ym})"
        )

    header_idx, headers = result
    data_rows = [r for r in all_rows[header_idx + 1:] if r and r[0].strip()]

    if not data_rows:
        raise ParseError(f"No data rows in TSO {area_code} CSV ({ym})")

    col_map = build_col_map(headers, HEADER_MAP)
    interval = detect_interval(data_rows)

    missing = [c for c in MASTER_COLUMNS if c not in col_map and c != "thermal_total"]
    if missing:
        logger.info(
            f"TSO {area_code} ({ym}): columns missing → NULL: {missing}"
        )
    logger.info(
        f"TSO {area_code} ({ym}): {interval}min interval detected"
    )

    rows: list[dict] = []
    for row in data_rows:
        target_date = parse_date(row[0])
        if not target_date:
            continue
        try:
            slot = time_to_slot(row[1], interval)
        except IndexError:
            continue
        if not slot:
            continue

        vals = apply_col_map(row, col_map, MASTER_COLUMNS)
        vals = _compute_thermal_total(vals)

        record = {
            "target_date":      target_date,
            "trading_slot":     slot,
            "area_code":        area_db_code,
            "interval_minutes": interval,
            **vals,
        }
        rows.append(record)

    logger.info(f"Parsed TSO {area_code} ({ym}): {len(rows)} rows")
    return rows


# ── Insert ────────────────────────────────────────────────────────────────────

def insert(rows: list[dict]) -> None:
    """Insert parsed TSO supply/demand rows into PostgreSQL."""
    upsert(
        rows=rows,
        table="tso_area_supply_demand",
        columns=DB_COLUMNS,
        conflict_columns=["target_date", "trading_slot", "area_code"],
        # fetched_at handled by DB DEFAULT NOW() on insert,
        # update it on conflict to track latest fetch time
        update_columns=[c for c in DB_COLUMNS
                        if c not in ("target_date", "trading_slot", "area_code")]
                       + ["fetched_at"],
    )


# ── Main entry point ──────────────────────────────────────────────────────────

def run(
    year: int | None = None,
    month: int | None = None,
    area_codes: list[str] | None = None,
    download: bool = True,
) -> None:
    """
    Full pipeline for all (or selected) TSOs: fetch → parse → insert → archive.

    year, month:  target period (defaults to previous month)
    area_codes:   TSO codes to process e.g. ['03', '06'] (defaults to all 9)
    download:     if False, use existing files in storage (skip fetch)
    """
    if year is None or month is None:
        year, month = _prev_year_month()

    ym = _ym_str(year, month)
    codes = area_codes or list(TSO_AREA_MAP.keys())

    logger.info(f"TSO scraper starting — {ym}, areas: {codes}")

    for area_code in codes:
        area_name = TSO_AREA_MAP[area_code]
        logger.info(f"Processing {area_code} ({area_name})...")
        path = _storage_path(area_code, ym)

        try:
            if download:
                fetch_one(area_code, year, month)

            rows = parse_one(area_code, year, month)
            insert(rows)
            st.archive(path)

        except (FetchError, ParseError) as e:
            # Log and continue — don't let one TSO failure stop others
            logger.error(f"Failed {area_code} ({area_name}): {e}")
            continue

    logger.info(f"TSO scraper completed — {ym}")


if __name__ == "__main__":
    run(download=True)
