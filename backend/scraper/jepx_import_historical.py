import os
import glob
from scraper.jepx import parse_csv, insert_summaries, insert_prices
from db.connection import get_connection

DOWNLOAD_DIR = os.getenv("JEPX_DOWNLOAD_DIR", "C:\\Users\\kotas\\Downloads")

def run():
    # Find all spot_summary CSV files
    pattern = os.path.join(DOWNLOAD_DIR, "spot_summary_*.csv")
    files = sorted(glob.glob(pattern))

    if not files:
        print(f"No CSV files found in {DOWNLOAD_DIR}")
        return

    print(f"Found {len(files)} files to import:")
    for f in files:
        print(f"  {os.path.basename(f)}")

    conn = get_connection()
    try:
        for csv_path in files:
            print(f"\nProcessing {os.path.basename(csv_path)}...")
            try:
                summaries, prices = parse_csv(csv_path)
                insert_summaries(conn, summaries)
                insert_prices(conn, prices)
                print(f"  ✓ {len(summaries)} slots, {len(prices)} price rows")
            except Exception as e:
                print(f"  ✗ Failed: {e}")
                continue
    finally:
        conn.close()

    print("\nHistorical import completed.")

if __name__ == "__main__":
    run()