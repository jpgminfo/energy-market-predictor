# scraper/base/inserter.py
#
# Responsibility: insert or update rows into PostgreSQL.
# Generic upsert — scrapers pass table name, columns, conflict keys.
# No scraper-specific SQL lives here.
#
# SOLID: open/closed — new scrapers extend by calling upsert(), not by modifying this file.
# KISS: one function, one responsibility.
# DRY: replaces repeated INSERT ... ON CONFLICT blocks in each scraper.

from scraper.base import log
from db.connection import get_connection


def upsert(
    rows: list[dict],
    table: str,
    columns: list[str],
    conflict_columns: list[str],
    update_columns: list[str] | None = None,
    conn=None,
) -> int:
    """
    Generic upsert for any scraper table.

    rows:             list of dicts — keys must match columns
    table:            target table name
    columns:          ordered list of columns to insert
    conflict_columns: columns in the UNIQUE constraint (for ON CONFLICT)
    update_columns:   columns to update on conflict (defaults to all non-conflict columns)
    conn:             optional existing connection — if None, opens a new one

    Returns: number of rows processed.

    Example:
        upsert(
            rows=parsed_rows,
            table="jepx_spot_summary",
            columns=["target_date", "trading_slot", "system_price", ...],
            conflict_columns=["target_date", "trading_slot"],
        )
    """
    if not rows:
        log("WARN", f"upsert({table}): no rows to insert")
        return 0

    update_cols = update_columns or [c for c in columns if c not in conflict_columns]

    col_str      = ", ".join(columns)
    placeholder  = ", ".join(f"%({c})s" for c in columns)
    conflict_str = ", ".join(conflict_columns)
    update_str   = ", ".join(f"{c} = EXCLUDED.{c}" for c in update_cols)

    query = f"""
        INSERT INTO {table} ({col_str})
        VALUES ({placeholder})
        ON CONFLICT ({conflict_str}) DO UPDATE SET
            {update_str}
    """

    close_after = conn is None
    if conn is None:
        conn = get_connection()

    try:
        cursor = conn.cursor()
        cursor.executemany(query, rows)
        conn.commit()
        log("INFO", f"upsert({table}): {len(rows)} rows inserted/updated")
        cursor.close()
    finally:
        if close_after:
            conn.close()

    return len(rows)
