# scraper/base/inserter.py
#
# Responsibility: insert or update rows into PostgreSQL.
# Generic upsert — scrapers pass table name, columns, conflict keys.
# No scraper-specific SQL lives here.
from psycopg2.extras import execute_values
from pipeline import setup_logger
from db.connection import get_connection

logger = setup_logger(__name__)

def upsert(
    rows: list[dict],
    table: str,
    columns: list[str],
    conflict_columns: list[str],
    update_columns: list[str] | None = None,
    conn=None,
    page_size=1000
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
        logger.warning(f"upsert({table}): no rows to insert")
        return 0

    update_cols = update_columns or [c for c in columns if c not in conflict_columns]

    col_str      = ", ".join(columns)
    placeholder  = ", ".join(f"%({c})s" for c in columns)
    conflict_str = ", ".join(conflict_columns)
    update_str   = ", ".join(f"{c} = EXCLUDED.{c}" for c in update_cols)

    deduped = {tuple(r[c] for c in conflict_columns): r for r in rows}
    if len(deduped) != len(rows):
        logger.info(f"upsert({table}): deduplicated {len(rows)} rows to {len(deduped)} unique rows")
    values = [tuple(r[c] for c in columns) for r in deduped.values()]

    query = f"""
        INSERT INTO {table} ({col_str})
        VALUES %s
        ON CONFLICT ({conflict_str}) DO UPDATE SET
            {update_str}
    """

    close_after = conn is None
    if conn is None:
        conn = get_connection()

    try:
        cursor = conn.cursor()
        execute_values(cursor, query, values, page_size=page_size)
        conn.commit()
        logger.info(f"upsert({table}): {len(rows)} rows inserted/updated")
        cursor.close()
    finally:
        if close_after:
            conn.close()

    return len(rows)
