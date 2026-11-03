import os
import glob
from pipeline.scraper.jepx import parse, insert
from pipeline import setup_logger

logger = setup_logger(__name__)

DOWNLOAD_DIR = os.environ["PIPELINE_DOWNLOAD_DIR"]

def run():
    # Find all spot_summary CSV files
    pattern = os.path.join(DOWNLOAD_DIR, "spot_summary_*.csv")
    files = sorted(glob.glob(pattern))

    if not files:
        logger.info(f"No CSV files found in {DOWNLOAD_DIR}")
        return

    logger.info(f"Found {len(files)} files to import:")
    for csv_path in files:
        filename = os.path.basename(csv_path)
        logger.info(f"Processing {filename}...")
        try:
            import re
            match = re.search(r"spot_summary_(\d{4})\.csv", filename)
            if match:
                fy = int(match.group(1))
                summaries, prices = parse(fy)
                insert(summaries, prices)
                logger.info(f"  ✓ {len(summaries)} slots, {len(prices)} price rows")
            else:
                logger.error(f"  ✗ Could not extract fiscal year from filename: {filename}")
        except Exception as e:
            logger.error(f"  ✗ Failed: {e}")
            continue

    logger.info("\nHistorical import completed.")

if __name__ == "__main__":
    run()