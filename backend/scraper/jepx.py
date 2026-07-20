import os
import csv
import time
from datetime import datetime
from playwright.sync_api import sync_playwright
from db.connection import get_connection

DOWNLOAD_DIR = os.getenv("JEPX_DOWNLOAD_DIR", "C:\\Users\\kotas\\Downloads")

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

def fiscal_year():
    year = int(time.strftime("%Y"))
    month = int(time.strftime("%m"))
    return year - 1 if month <= 3 else year

def timestamp():
    return time.strftime("%Y%m%d%H%M%S")

def log_status(status, message):
    print(f"[{timestamp()}] {status}: {message}")

def download_csv():
    url = "https://www.jepx.jp/electricpower/market-data/spot/"
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,  # set True once confirmed working
            downloads_path=DOWNLOAD_DIR
        )
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()

        try:
            page.goto(url, wait_until="networkidle")

            # Click download button
            with page.expect_download() as download_info:
                # Click the CSV download button (section 6, 3rd list item)
                page.locator("section:nth-of-type(6) ul li:nth-child(3) button").click()

                # Select current fiscal year option
                page.locator("form select option:nth-child(1)").click()

                # Click final download button
                page.locator("form button").click()

            download = download_info.value
            save_path = os.path.join(DOWNLOAD_DIR, f"spot_summary_{fiscal_year()}.csv")
            download.save_as(save_path)
            log_status("SUCCESS", f"Downloaded to {save_path}")
            return True

        except Exception as e:
            log_status("ERROR", f"Download failed: {e}")
            return False
        finally:
            browser.close()

def parse_csv(csv_file_path):
    summaries = []
    prices = []

    with open(csv_file_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        for _ in range(3):
            next(reader)
        for row in reader:
            if not row or not row[0]:
                continue

            target_date = datetime.strptime(row[0], "%Y/%m/%d").date()
            trading_slot = int(row[1])

            summary = {
                "target_date":                  target_date,
                "trading_slot":                 trading_slot,
                "system_price":                 float(row[5]) if row[5] else None,
                "sell_bid_amount":              float(row[2]) if row[2] else None,
                "buy_bid_amount":               float(row[3]) if row[3] else None,
                "total_contract_amount":        float(row[4]) if row[4] else None,
                "sell_block_bid_amount":        float(row[15]) if row[15] else None,
                "sell_block_contract_amount":   float(row[16]) if row[16] else None,
                "buy_block_bid_amount":         float(row[17]) if row[17] else None,
                "buy_block_contract_amount":    float(row[18]) if row[18] else None,
            }
            summaries.append(summary)

            for col_idx, area_code in AREA_COLUMNS.items():
                price = {
                    "target_date":  target_date,
                    "trading_slot": trading_slot,
                    "area_code":    area_code,
                    "area_price":   float(row[col_idx]) if row[col_idx] else None,
                }
                prices.append(price)

    log_status("INFO", f"Parsed {len(summaries)} slots, {len(prices)} area price rows")
    return summaries, prices

def insert_summaries(conn, summaries):
    cursor = conn.cursor()
    query = """
        INSERT INTO jepx_spot_summary (
            target_date, trading_slot, system_price,
            sell_bid_amount, buy_bid_amount, total_contract_amount,
            sell_block_bid_amount, sell_block_contract_amount,
            buy_block_bid_amount, buy_block_contract_amount
        ) VALUES (
            %(target_date)s, %(trading_slot)s, %(system_price)s,
            %(sell_bid_amount)s, %(buy_bid_amount)s, %(total_contract_amount)s,
            %(sell_block_bid_amount)s, %(sell_block_contract_amount)s,
            %(buy_block_bid_amount)s, %(buy_block_contract_amount)s
        )
        ON CONFLICT (target_date, trading_slot) DO UPDATE SET
            system_price               = EXCLUDED.system_price,
            sell_bid_amount            = EXCLUDED.sell_bid_amount,
            buy_bid_amount             = EXCLUDED.buy_bid_amount,
            total_contract_amount      = EXCLUDED.total_contract_amount,
            sell_block_bid_amount      = EXCLUDED.sell_block_bid_amount,
            sell_block_contract_amount = EXCLUDED.sell_block_contract_amount,
            buy_block_bid_amount       = EXCLUDED.buy_block_bid_amount,
            buy_block_contract_amount  = EXCLUDED.buy_block_contract_amount
    """
    cursor.executemany(query, summaries)
    conn.commit()
    log_status("INFO", f"Inserted/updated {len(summaries)} summary rows")
    cursor.close()

def insert_prices(conn, prices):
    cursor = conn.cursor()
    query = """
        INSERT INTO jepx_spot_prices (
            target_date, trading_slot, area_code, area_price
        ) VALUES (
            %(target_date)s, %(trading_slot)s, %(area_code)s, %(area_price)s
        )
        ON CONFLICT (target_date, trading_slot, area_code) DO UPDATE SET
            area_price = EXCLUDED.area_price
    """
    cursor.executemany(query, prices)
    conn.commit()
    log_status("INFO", f"Inserted/updated {len(prices)} area price rows")
    cursor.close()

def archive_csv(csv_file_path):
    new_name = f"{os.path.splitext(os.path.basename(csv_file_path))[0]}_{timestamp()}.csv"
    archive_dir = os.path.join(os.path.dirname(csv_file_path), "archive")
    os.makedirs(archive_dir, exist_ok=True)
    archived_path = os.path.join(archive_dir, new_name)
    os.rename(csv_file_path, archived_path)
    log_status("INFO", f"Archived to {archived_path}")

def run(download=True):
    csv_path = os.path.join(DOWNLOAD_DIR, f"spot_summary_{fiscal_year()}.csv")

    if download:
        success = download_csv()
        if not success:
            return

    if not os.path.exists(csv_path):
        log_status("ERROR", f"CSV not found: {csv_path}")
        return

    summaries, prices = parse_csv(csv_path)

    conn = get_connection()
    try:
        insert_summaries(conn, summaries)
        insert_prices(conn, prices)
    finally:
        conn.close()

    archive_csv(csv_path)
    log_status("SUCCESS", "JEPX scraper completed")

if __name__ == "__main__":
    run()