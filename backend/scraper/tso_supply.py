import os
import csv
import time
import zipfile
import requests
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright
from db.connection import get_connection

# This tool will download previous month's area supply and demand for 10 TSOs.
# No  Area        Constraits
# 01  Hokkaido    N/A
# 02  Tohoku      N-1 month CSV file is not available until 25th of N month (current). Wait until the day or concatenate each file as below.
# 03  Tokyo       N/A
# 04  Chubu       CSV is only available for N month (current).
# 05  Hokuriku    Select target year and month and click download.
# 06  Kansai      N/A
# 07  Chugoku     Select target year and month and click download.
# 08  Shikoku     N/A
# 09  Kyushu      N/A
# 10  Okinawa     Excluded from scope '10': lambda ym: f"https://www.okiden.co.jp/business-support/service/supply-and-demand/csv/eria_jukyu_{ym}_10.csv"

DOWNLOAD_DIR = os.getenv("JEPX_DOWNLOAD_DIR", "C:\\Users\\kotas\\Downloads")

# Area code mapping: TSO file suffix → areas table area_code
TSO_AREA_MAP = {
    '01': 'HOKKAIDO',
    '02': 'TOHOKU',
    '03': 'TOKYO',
    '04': 'CHUBU',
    '05': 'HOKURIKU',
    '06': 'KANSAI',
    '07': 'CHUGOKU',
    '08': 'SHIKOKU',
    '09': 'KYUSHU'
}

# TSOs with direct CSV download URL (no browser interaction needed)
DIRECT_DOWNLOAD_TSOS = {
    '01': lambda ym: f"https://www.hepco.co.jp/network/con_service/public_document/supply_demand_results/csv/eria_jukyu_{ym}_01.csv",
    '03': lambda ym: f"https://www.tepco.co.jp/forecast/html/images/eria_jukyu_{ym}_03.csv",
    '04': lambda ym: f"https://powergrid.chuden.co.jp/denki_yoho_content_data/eria_jukyu_{ym}_04.csv",
    '06': lambda ym: f"https://www.kansai-td.co.jp/interchange/denkiyoho/area-performance/eria_jukyu_{ym}_06.csv",
    '08': lambda ym: f"https://www.yonden.co.jp/nw/supply_demand/csv/eria_jukyu_{ym}_08.csv",
    '09': lambda ym: f"https://www.kyuden.co.jp/td_area_jukyu/csv/eria_jukyu_{ym}_09.csv"
}

# TSO 02 (Tohoku) uses zip download
TOHOKU_URL = lambda year, month0: f"https://setsuden.nw.tohoku-epco.co.jp/get_realtime_jukyu.php?year={year}&month={month0}"

# TSO 05 (Hokuriku) and 07 (Chugoku) need browser interaction
HOKURIKU_URL = "https://www.rikuden.co.jp/nw/denki-yoho/results_jyukyu.html"
CHUGOKU_URL  = "https://www.energia.co.jp/nw/jukyuu/eria_jukyu.html"


def timestamp():
    return time.strftime("%Y%m%d%H%M%S")

def log_status(status, message):
    print(f"[{timestamp()}] {status}: {message}")

def get_target_year_month(year=None, month=None):
    """Get target year/month. Defaults to previous month."""
    if year and month:
        return year, month
    today = datetime.today()
    target = today.replace(day=1) - timedelta(days=1)
    return target.year, target.month

def year_month_str(year, month):
    return f"{year}{month:02d}"

def time_to_slot(time_str: str, interval_minutes: int = 30) -> int:
    """Convert HH:MM to trading slot based on interval."""
    h, m = map(int, time_str.strip().split(':'))
    if h == 24:
        h = 0
    total_minutes = h * 60 + m
    return total_minutes // interval_minutes + 1

def detect_interval(rows: list) -> int:
    """Detect interval from CSV by checking time difference between rows."""
    if len(rows) < 2:
        return 30
    times = [r[1] for r in rows[:3]]
    try:
        t1 = datetime.strptime(times[0].strip(), '%H:%M')
        t2 = datetime.strptime(times[1].strip(), '%H:%M')
        diff = int((t2 - t1).seconds / 60)
        return diff if diff in (15, 30, 60) else 30
    except Exception:
        return 30

def parse_date(date_str: str):
    """Parse date string to date object."""
    for fmt in ('%Y/%m/%d', '%Y%m%d', '%Y-%m-%d'):
        try:
            return datetime.strptime(date_str.strip(), fmt).date()
        except ValueError:
            continue
    return None

def to_float(val: str):
    """Convert string to float, return None if empty or invalid."""
    val = val.strip()
    if val == '' or val == '-':
        return None
    try:
        return float(val.replace(',', ''))
    except ValueError:
        return None

# ── Download functions ────────────────────────────────────────────────────────

def download_direct(area_code: str, year: int, month: int) -> str | None:
    """Download CSV directly via HTTP for TSOs with direct URLs."""
    ym = year_month_str(year, month)
    url = DIRECT_DOWNLOAD_TSOS[area_code](ym)
    save_path = os.path.join(DOWNLOAD_DIR, f"eria_jukyu_{ym}_{area_code}.csv")
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        with open(save_path, 'wb') as f:
            f.write(resp.content)
        log_status("SUCCESS", f"Downloaded {area_code} from {url}")
        return save_path
    except Exception as e:
        log_status("ERROR", f"Failed to download {area_code}: {e}")
        return None

def download_tohoku(year: int, month: int) -> str | None:
    """Download Tohoku (02) zip and concatenate into single CSV."""
    month0 = f"{month:02d}"
    ym = year_month_str(year, month)
    url = TOHOKU_URL(year, month0)
    zip_path = os.path.join(DOWNLOAD_DIR, f"realtime_jukyu_{ym}_02.zip")
    csv_path = os.path.join(DOWNLOAD_DIR, f"eria_jukyu_{ym}_02.csv")
    unzip_dir = os.path.join(DOWNLOAD_DIR, f"unzip_files_{ym}")

    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        with open(zip_path, 'wb') as f:
            f.write(resp.content)
        log_status("SUCCESS", f"Downloaded Tohoku zip from {url}")
    except Exception as e:
        log_status("ERROR", f"Failed to download Tohoku: {e}")
        return None

    try:
        import pandas as pd
        os.makedirs(unzip_dir, exist_ok=True)
        with zipfile.ZipFile(zip_path, 'r') as z:
            z.extractall(unzip_dir)
            files = sorted(z.namelist(), key=lambda x: x.split('_')[2] if len(x.split('_')) > 2 else x)

        dfs = []
        for f in files:
            fp = os.path.join(unzip_dir, f)
            try:
                df = pd.read_csv(fp, encoding='sjis', skiprows=1)
                dfs.append(df)
            except Exception:
                continue

        if dfs:
            import pandas as pd
            combined = pd.concat(dfs, ignore_index=True)
            header = "単位[MW平均],,,供給力"
            combined.to_csv(csv_path, index=False, encoding='utf-8-sig')
            with open(csv_path, 'r', encoding='utf-8-sig') as f:
                data = f.read()
            with open(csv_path, 'w', encoding='utf-8-sig') as f:
                f.write(header + '\n' + data)
            log_status("SUCCESS", f"Concatenated Tohoku CSV to {csv_path}")
            return csv_path
    except Exception as e:
        log_status("ERROR", f"Failed to process Tohoku zip: {e}")
        return None

def download_browser(area_code: str, year: int, month: int) -> str | None:
    """Download Hokuriku (05) or Chugoku (07) via Playwright."""
    ym = year_month_str(year, month)
    save_path = os.path.join(DOWNLOAD_DIR, f"eria_jukyu_{ym}_{area_code}.csv")
    url = HOKURIKU_URL if area_code == '05' else CHUGOKU_URL

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, downloads_path=DOWNLOAD_DIR)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()
        try:
            page.goto(url, wait_until="networkidle")
            # Select year and month
            page.locator("[name='year']").select_option(str(year))
            page.locator("[name='month']").select_option(str(month))

            with page.expect_download(timeout=30000) as dl:
                if area_code == '05':
                    page.locator("/html/body/div[3]/div[3]/div/div/div/div[2]/div/form/ul/li[1]/a").click()
                else:
                    page.locator("[id*='download']").click()

            download = dl.value
            download.save_as(save_path)
            log_status("SUCCESS", f"Downloaded {area_code} via browser to {save_path}")
            return save_path
        except Exception as e:
            log_status("ERROR", f"Browser download failed for {area_code}: {e}")
            return None
        finally:
            browser.close()

def download_tso(area_code: str, year: int, month: int) -> str | None:
    """Route to correct download method per TSO."""
    if area_code in DIRECT_DOWNLOAD_TSOS:
        return download_direct(area_code, year, month)
    elif area_code == '02':
        return download_tohoku(year, month)
    elif area_code in ('05', '07'):
        return download_browser(area_code, year, month)
    else:
        log_status("ERROR", f"Unknown area_code: {area_code}")
        return None

# ── Parse function ────────────────────────────────────────────────────────────

def parse_csv(csv_path: str, area_code: str) -> list[dict]:
    """Parse TSO supply/demand CSV into list of dicts."""
    rows = []
    area_db_code = TSO_AREA_MAP.get(area_code)
    if not area_db_code:
        log_status("ERROR", f"No area mapping for {area_code}")
        return []

    # Try encodings
    for encoding in ('shift_jis', 'utf-8-sig', 'utf-8'):
        try:
            with open(csv_path, 'r', encoding=encoding) as f:
                content = f.read()
            break
        except (UnicodeDecodeError, FileNotFoundError):
            continue
    else:
        log_status("ERROR", f"Cannot read {csv_path}")
        return []

    reader = csv.reader(content.splitlines())

    # Skip header rows until we find DATE row
    headers_found = False
    for row in reader:
        if not row:
            continue
        # Look for the data header row containing DATE
        if 'DATE' in row or '年月日' in row or (len(row) > 1 and 'DATE' in str(row)):
            headers_found = True
            continue
        if not headers_found:
            continue

        # Parse data rows
        if len(row) < 19:
            continue
        date_val = parse_date(row[0])
        if not date_val:
            continue
        slot = time_to_slot(row[1])
        if not slot:
            continue

        # Column mapping based on CSV structure:
        # DATE, TIME, エリア需要, 原子力, 火力(LNG), 火力(石炭), 火力(石油),
        # 火力(その他), 水力, 地熱, バイオマス, 太陽光発電実績, 太陽光出力制御量,
        # 風力発電実績, 風力出力制御量, 揚水, 蓄電池, 連系線, その他, 合計
        rows.append({
            'target_date':        date_val,
            'trading_slot':       slot,
            'area_code':          area_db_code,
            'area_demand':        to_float(row[2]),
            'nuclear':            to_float(row[3]),
            'thermal_lng':        to_float(row[4]),
            'thermal_coal':       to_float(row[5]),
            'thermal_oil':        to_float(row[6]),
            'thermal_other':      to_float(row[7]),
            'thermal_curtailment': to_float(row[8]),
            'hydro':              to_float(row[9]), 
            'geothermal':         to_float(row[10]),
            'biomass_actual':     to_float(row[11]),
            'biomass_curtailment': to_float(row[12]),
            'solar_actual':       to_float(row[13]),
            'solar_curtailment':  to_float(row[14]),
            'wind_actual':        to_float(row[15]),
            'wind_curtailment':   to_float(row[16]),
            'pumped_storage':     to_float(row[17]),
            'battery':            to_float(row[18]),
            'interconnection':    to_float(row[19]),
            'other':              to_float(row[20]),
            'total_supply':       to_float(row[21]) if len(row) > 21 else None,
        })

    log_status("INFO", f"Parsed {len(rows)} rows for {area_db_code}")
    return rows

# ── Insert function ───────────────────────────────────────────────────────────

def insert_supply_demand(conn, rows: list[dict]):
    """Insert or update TSO supply/demand records."""
    if not rows:
        return
    cursor = conn.cursor()
    query = """
        INSERT INTO tso_area_supply_demand (
            target_date, trading_slot, area_code,
            area_demand, nuclear, thermal_lng, thermal_coal, thermal_oil,
            thermal_other, thermal_curtailment, hydro, geothermal, biomass_actual, biomass_curtailment,
            solar_actual, solar_curtailment, wind_actual, wind_curtailment,
            pumped_storage, battery, interconnection, other, total_supply
        ) VALUES (
            %(target_date)s, %(trading_slot)s, %(area_code)s,
            %(area_demand)s, %(nuclear)s, %(thermal_lng)s, %(thermal_coal)s,
            %(thermal_oil)s, %(thermal_other)s, %(thermal_curtailment)s, %(hydro)s, %(geothermal)s,
            %(biomass_actual)s, %(biomass_curtailment)s, %(solar_actual)s, %(solar_curtailment)s,
            %(wind_actual)s, %(wind_curtailment)s, %(pumped_storage)s,
            %(battery)s, %(interconnection)s, %(other)s, %(total_supply)s
        )
        ON CONFLICT (target_date, trading_slot, area_code) DO UPDATE SET
            area_demand       = EXCLUDED.area_demand,
            nuclear           = EXCLUDED.nuclear,
            thermal_lng       = EXCLUDED.thermal_lng,
            thermal_coal      = EXCLUDED.thermal_coal,
            thermal_oil       = EXCLUDED.thermal_oil,
            thermal_other     = EXCLUDED.thermal_other,
            thermal_curtailment = EXCLUDED.thermal_curtailment,
            hydro             = EXCLUDED.hydro,
            geothermal        = EXCLUDED.geothermal,
            biomass_actual    = EXCLUDED.biomass_actual,
            biomass_curtailment = EXCLUDED.biomass_curtailment,
            solar_actual      = EXCLUDED.solar_actual,
            solar_curtailment = EXCLUDED.solar_curtailment,
            wind_actual       = EXCLUDED.wind_actual,
            wind_curtailment  = EXCLUDED.wind_curtailment,
            pumped_storage    = EXCLUDED.pumped_storage,
            battery           = EXCLUDED.battery,
            interconnection   = EXCLUDED.interconnection,
            other             = EXCLUDED.other,
            total_supply      = EXCLUDED.total_supply,
            fetched_at        = NOW()
    """
    cursor.executemany(query, rows)
    conn.commit()
    log_status("INFO", f"Inserted/updated {len(rows)} rows for {rows[0]['area_code']}")
    cursor.close()

def archive_csv(csv_path: str):
    """Move processed CSV to archive folder."""
    new_name = f"{os.path.splitext(os.path.basename(csv_path))[0]}_{timestamp()}.csv"
    archive_dir = os.path.join(os.path.dirname(csv_path), "archive")
    os.makedirs(archive_dir, exist_ok=True)
    archived = os.path.join(archive_dir, new_name)
    os.rename(csv_path, archived)
    log_status("INFO", f"Archived to {archived}")

# ── Main entry point ──────────────────────────────────────────────────────────

def run(year=None, month=None, area_codes=None, download=True):
    """
    Main entry point.
    year, month: target period (defaults to previous month)
    area_codes: list of TSO codes to process e.g. ['03', '06']
                defaults to all 9 TSOs
    download: if False, skip download and use existing CSV files
    """
    target_year, target_month = get_target_year_month(year, month)
    ym = year_month_str(target_year, target_month)
    codes = area_codes or list(TSO_AREA_MAP.keys())

    log_status("INFO", f"Processing {ym} for areas: {codes}")

    conn = get_connection()
    try:
        for area_code in codes:
            log_status("INFO", f"Processing TSO {area_code} ({TSO_AREA_MAP[area_code]})...")

            if download:
                csv_path = download_tso(area_code, target_year, target_month)
            else:
                # Use existing file
                csv_path = os.path.join(
                    DOWNLOAD_DIR, f"eria_jukyu_{ym}_{area_code}.csv"
                )
                if not os.path.exists(csv_path):
                    log_status("ERROR", f"File not found: {csv_path}")
                    continue

            if not csv_path:
                continue

            rows = parse_csv(csv_path, area_code)
            if rows:
                insert_supply_demand(conn, rows)
                archive_csv(csv_path)
            else:
                log_status("WARN", f"No rows parsed for {area_code}")

    finally:
        conn.close()

    log_status("SUCCESS", f"TSO supply/demand scraper completed for {ym}")

if __name__ == "__main__":
    # Manual trigger — previous month, all TSOs
    run(download=True)
