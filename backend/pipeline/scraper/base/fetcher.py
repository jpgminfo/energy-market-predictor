# scraper/base/fetcher.py
#
# Responsibility: fetch data from external sources and stage in Supabase Storage.
# Returns storage_path strings — callers read from storage, never touch local disk.
#
# Three fetch strategies:
#   1. fetch_http    — direct URL download (most TSOs)
#   2. fetch_zip     — download zip, concat CSVs, upload result (Tohoku)
#   3. fetch_browser — Playwright interaction (JEPX, Hokuriku, Chugoku)

import io
import csv
import zipfile
import requests
from typing import Callable
from playwright.sync_api import sync_playwright, Page, TimeoutError as PlaywrightTimeoutError
from pipeline import setup_logger, FetchError
from pipeline import storage as st

logger = setup_logger(__name__)


def fetch_http(url: str, storage_path: str, timeout: int = 30) -> str:
    """
    Download a file via HTTP GET and upload to Supabase Storage.
    Returns storage_path on success.
    Raises FetchError on HTTP error or network failure.
    """
    logger.info(f"HTTP fetch: {url}")
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
    except requests.exceptions.HTTPError as e:
        raise FetchError(
            f"HTTP error fetching '{url}': {e.response.status_code} {e.response.reason}"
        ) from e
    except requests.exceptions.ConnectionError as e:
        raise FetchError(f"Connection error fetching '{url}': {e}") from e
    except requests.exceptions.Timeout:
        raise FetchError(f"Timeout fetching '{url}' after {timeout}s")
    except requests.exceptions.RequestException as e:
        raise FetchError(f"Failed to fetch '{url}': {e}") from e

    st.upload_bytes(resp.content, storage_path)
    logger.info(f"HTTP fetch complete: {storage_path} ({len(resp.content):,} bytes)")
    return storage_path


def fetch_zip_concat(
    url: str,
    storage_path: str,
    skip_header_rows: int = 1,
    timeout: int = 30,
) -> str:
    """
    Download a zip of daily CSV files, concatenate into one CSV,
    and upload the result to Supabase Storage.
    Used for: Tohoku TSO (daily zip → monthly CSV).

    skip_header_rows: header rows kept only from first file.
    Returns storage_path of the concatenated CSV.
    Raises FetchError on download failure or empty zip.
    """
    logger.info(f"Zip fetch: {url}")
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
    except requests.exceptions.HTTPError as e:
        raise FetchError(
            f"HTTP error fetching zip '{url}': {e.response.status_code} {e.response.reason}"
        ) from e
    except requests.exceptions.RequestException as e:
        raise FetchError(f"Failed to fetch zip '{url}': {e}") from e

    output_rows: list[list[str]] = []
    header_written = False
    skipped = 0
    files = []

    try:
        with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
            files = sorted(z.namelist())
            if not files:
                raise FetchError(f"Zip from '{url}' is empty")

            for fname in files:
                with z.open(fname) as f:
                    raw = f.read()

                text = None
                for enc in ("shift_jis", "utf-8-sig", "utf-8", "cp932"):
                    try:
                        text = raw.decode(enc)
                        break
                    except (UnicodeDecodeError, LookupError):
                        continue

                if text is None:
                    logger.warning(f"Cannot decode '{fname}' in zip — skipping")
                    skipped += 1
                    continue

                rows = list(csv.reader(text.splitlines()))
                if not header_written:
                    output_rows.extend(rows[:skip_header_rows])
                    header_written = True
                output_rows.extend(rows[skip_header_rows:])

    except zipfile.BadZipFile as e:
        raise FetchError(f"Invalid zip file from '{url}': {e}") from e

    if not output_rows:
        raise FetchError(
            f"No data extracted from zip '{url}' "
            f"({len(files)} files, {skipped} skipped)"
        )

    if skipped:
        logger.warning(
            f"Skipped {skipped}/{len(files)} files in zip due to encoding errors"
        )

    buf = io.StringIO()
    csv.writer(buf).writerows(output_rows)
    st.upload_bytes(buf.getvalue().encode("utf-8-sig"), storage_path)
    logger.info(
        f"Zip concat complete: {len(files) - skipped} files → {storage_path}"
    )
    return storage_path


def fetch_browser(
    url: str,
    storage_path: str,
    interact: Callable[[Page], None],
    headless: bool = True,
    timeout: int = 30000,
) -> str:
    """
    Launch a browser, run caller-supplied interaction, capture the download,
    and upload to Supabase Storage.

    interact(page): callable that performs all clicks/selects to trigger
                    the file download. Must NOT call expect_download itself.

    Returns storage_path on success.
    Raises FetchError on timeout, navigation failure, or download failure.

    Example:
        def interact(page):
            page.locator("#dl-select--spot_summary").select_option("spot_summary_2026.csv")
            page.locator("#modal-box--spot_summary button[type='submit']").click()

        fetch_browser(url, "jepx/spot_summary_2026.csv", interact)
    """
    logger.info(f"Browser fetch: {url}")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()
        try:
            try:
                page.goto(url, wait_until="networkidle")
            except PlaywrightTimeoutError as e:
                raise FetchError(f"Page load timeout for '{url}'") from e
            except Exception as e:
                raise FetchError(f"Navigation failed for '{url}': {e}") from e

            try:
                with page.expect_download(timeout=timeout) as dl_info:
                    interact(page)
                download = dl_info.value
            except PlaywrightTimeoutError as e:
                raise FetchError(
                    f"Download timeout after {timeout}ms on '{url}'"
                ) from e
            except Exception as e:
                raise FetchError(
                    f"Browser interaction failed on '{url}': {e}"
                ) from e

            try:
                raw_path = download.path()
                with open(raw_path, "rb") as f:
                    data = f.read()
            except OSError as e:
                raise FetchError(
                    f"Cannot read downloaded file from '{url}': {e}"
                ) from e

            st.upload_bytes(data, storage_path)
            logger.info(
                f"Browser fetch complete: {storage_path} ({len(data):,} bytes)"
            )
            return storage_path

        finally:
            browser.close()
