# Supabase Storage wrapper for scraper staging.
# Replaces local Downloads folder — all scrapers read/write here.
#
# Bucket layout:
#   scraper-staging/
#     jepx/spot_summary_2026.csv
#     tso/eria_jukyu_202609_03.csv
#     weather/weather_202609.json
#     archive/jepx/spot_summary_2026_20260923.csv

import os
from supabase import create_client, Client
from supabase import StorageException
from pipeline import setup_logger, StorageError, timestamp

logger = setup_logger(__name__)

BUCKET = "scraper-staging"


def _client() -> Client:
    """Create Supabase client using service role key for storage write access."""
    url = os.environ["NEXT_PUBLIC_SUPABASE_URL"]
    key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    return create_client(url, key)


def ensure_bucket() -> None:
    """
    Create storage bucket if it doesn't exist.
    Call once at pipeline startup (e.g. FastAPI lifespan).
    """
    client = _client()
    try:
        client.storage.get_bucket(BUCKET)
        logger.info(f"Storage bucket exists: {BUCKET}")
    except StorageException as e:
        if "not found" in str(e).lower() or "404" in str(e):
            try:
                client.storage.create_bucket(BUCKET, options={"public": False})
                logger.info(f"Created storage bucket: {BUCKET}")
            except StorageException as create_err:
                raise StorageError(
                    f"Failed to create bucket '{BUCKET}': {create_err}"
                ) from create_err
        else:
            raise StorageError(
                f"Failed to check bucket '{BUCKET}': {e}"
            ) from e


def upload_bytes(
    data: bytes,
    storage_path: str,
    content_type: str = "text/csv",
) -> str:
    """
    Upload raw bytes to Supabase Storage.
    Removes existing file first (upsert behaviour).
    Returns storage_path on success.
    Raises StorageError on failure.
    """
    client = _client()
    try:
        client.storage.from_(BUCKET).remove([storage_path])
    except StorageException:
        pass  # file may not exist yet — that's fine

    try:
        client.storage.from_(BUCKET).upload(
            path=storage_path,
            file=data,
            file_options={"content-type": content_type},
        )
        logger.info(f"Uploaded to storage: {storage_path} ({len(data):,} bytes)")
        return storage_path
    except StorageException as e:
        raise StorageError(
            f"Failed to upload '{storage_path}': {e}"
        ) from e


def upload_file(local_path: str, storage_path: str) -> str:
    """
    Upload a local file to Supabase Storage.
    Returns storage_path on success.
    Raises StorageError on failure.
    """
    try:
        with open(local_path, "rb") as f:
            data = f.read()
    except OSError as e:
        raise StorageError(
            f"Cannot read local file '{local_path}': {e}"
        ) from e

    return upload_bytes(data, storage_path)


def download_bytes(storage_path: str) -> bytes:
    """
    Download file from Supabase Storage as raw bytes.
    Raises StorageError if file not found or download fails.
    """
    client = _client()
    try:
        data = client.storage.from_(BUCKET).download(storage_path)
        logger.info(f"Downloaded from storage: {storage_path} ({len(data):,} bytes)")
        return data
    except StorageException as e:
        raise StorageError(
            f"Failed to download '{storage_path}': {e}"
        ) from e


def download_text(
    storage_path: str,
    encoding: str = "utf-8-sig",
) -> str:
    """
    Download file from Supabase Storage as decoded text.
    Tries requested encoding first, then falls back through common ones.
    Raises StorageError if download fails or no encoding works.
    """
    raw = download_bytes(storage_path)

    for enc in [encoding, "shift_jis", "utf-8", "cp932"]:
        try:
            text = raw.decode(enc)
            logger.debug(f"Decoded '{storage_path}' with encoding: {enc}")
            return text
        except (UnicodeDecodeError, LookupError):
            continue

    raise StorageError(
        f"Cannot decode '{storage_path}' with any known encoding "
        f"(tried: {encoding}, shift_jis, utf-8, cp932)"
    )


def archive(storage_path: str, ts: str | None = None) -> str:
    """
    Move a staged file to archive/ prefix within the same bucket.

    archive('jepx/spot_summary_2026.csv')
    → 'archive/jepx/spot_summary_2026_20260923143022.csv'

    ts: timestamp string — defaults to current timestamp if not provided.
    Returns the archived storage_path.
    Raises StorageError on failure.
    """
    client = _client()
    ts = ts or timestamp()

    parts = storage_path.rsplit(".", 1)
    archived = (
        f"archive/{parts[0]}_{ts}.{parts[1]}"
        if len(parts) == 2
        else f"archive/{storage_path}_{ts}"
    )

    try:
        client.storage.from_(BUCKET).move(storage_path, archived)
        logger.info(f"Archived: {storage_path} → {archived}")
        return archived
    except StorageException as e:
        raise StorageError(
            f"Failed to archive '{storage_path}' → '{archived}': {e}"
        ) from e


def remove(storage_path: str) -> None:
    """
    Delete a file from storage.
    Use when archiving isn't needed (e.g. temp files).
    Raises StorageError on failure.
    """
    client = _client()
    try:
        client.storage.from_(BUCKET).remove([storage_path])
        logger.info(f"Removed from storage: {storage_path}")
    except StorageException as e:
        raise StorageError(
            f"Failed to remove '{storage_path}': {e}"
        ) from e


def exists(storage_path: str) -> bool:
    """
    Check if a file exists in storage.
    Returns True/False — does not raise.
    """
    client = _client()
    try:
        client.storage.from_(BUCKET).info(storage_path)
        return True
    except StorageException:
        return False
