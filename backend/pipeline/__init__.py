# Common scraper infrastructure — logging, timestamp
import time
import os
import logging
import sys
from pathlib import Path
from dotenv import load_dotenv

def timestamp() -> str:
    return time.strftime("%Y%m%d%H%M%S")

# load environment variables from .env file
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# setting log directory
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

# common logger setup
def setup_logger(name: str = "pipeline", level: int = logging.INFO) -> logging.Logger:

    logger = logging.getLogger(name)
    
    if logger.hasHandlers():
        return logger

    logger.setLevel(level)
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # console output
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # file output (pipeline/logs/scraper.log)
    file_handler = logging.FileHandler(LOG_DIR / "scraper.log", encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger

# custom exceptions for pipeline
class PipelineError(Exception):
    """Pipeline processing base exception class"""
    pass

class FetchError(PipelineError):
    """data fetching (fetcher.py) exception"""
    pass

class ParseError(PipelineError):
    """data transformation & parsing (parser.py) exception"""
    pass

class StorageError(PipelineError):
    """Raised when Supabase Storage operations fail (upload, download, archive)."""
    pass

