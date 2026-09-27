# scraper/base/__init__.py
# Common scraper infrastructure — logging, timestamp
import time
import os
import logging
import sys
from pathlib import Path
from dotenv import load_dotenv

def timestamp() -> str:
    return time.strftime("%Y%m%d%H%M%S")

# 1. 環境変数の自動ロード (.env)
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# ログ保存ディレクトリの設定
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

# 2. 共通ロガー生成関数
def setup_logger(name: str = "pipeline", level: int = logging.INFO) -> logging.Logger:
    """
    全処理モジュール共通のロガーを生成する
    """
    logger = logging.getLogger(name)
    
    if logger.hasHandlers():
        return logger

    logger.setLevel(level)
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # コンソール出力
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # ファイル出力 (pipeline/logs/scraper.log)
    file_handler = logging.FileHandler(LOG_DIR / "scraper.log", encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger

# 3. 各パイプライン処理共通のカスタム例外定義
class PipelineError(Exception):
    """パイプライン処理のベース例外クラス"""
    pass

class FetchError(PipelineError):
    """データ取得 (fetcher.py) 時の例外"""
    pass

class ParseError(PipelineError):
    """データ変換・パース (parser.py) 時の例外"""
    pass

class StorageError(PipelineError):
    """DB・ストレージ処理 (storage.py / inserter.py) 時の例外"""
    pass

