import os
import glob
from pipeline.storage import upload_bytes
from pipeline import setup_logger

logger = setup_logger(__name__)

DOWNLOAD_DIR = os.environ["PIPELINE_DOWNLOAD_DIR"]
BUCKET = "jepx"

def upload_historical_files():
    pattern = os.path.join(DOWNLOAD_DIR, "spot_summary_*.csv")
    files = glob.glob(pattern)
    
    for file_path in files:
        filename = os.path.basename(file_path)
        storage_path = f"jepx/{filename}"
        
        logger.info(f"Uploading {filename} to Storage -> {storage_path}...")
        with open(file_path, "rb") as f:
            file_bytes = f.read()
        upload_bytes(file_bytes, storage_path)
        logger.info(f"  ✓ Uploaded successfully.")

if __name__ == "__main__":
    upload_historical_files()