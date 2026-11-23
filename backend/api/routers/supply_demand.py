# backend/api/routers/supply_demand.py
#
# One area, one day of TSO supply/demand actuals (tso_area_supply_demand).
# Thin query layer: no business logic here, so it ports to the Go API unchanged.

from datetime import date

from fastapi import APIRouter, Query

# Use the same import line as api/routers/prices.py
from db.connection import get_connection

router = APIRouter(prefix="/api/supply-demand", tags=["supply-demand"])

# Fixed list, never user input, so it is safe to put into the SQL text.
VALUE_COLUMNS = [
    "area_demand",
    "nuclear",
    "thermal_total",   # comparable across eras (see parse_one in tso_supply.py)
    "hydro",
    "geothermal",
    "biomass_actual",
    "solar_actual",
    "wind_actual",
    "pumped_storage",  # can be negative
    "battery",         # can be negative
    "interconnection", # can be negative
]


def slot_to_time(slot: int, interval_minutes: int) -> str:
    """Slot 1 is 00:00. Works for 15, 30 and 60 minute data."""
    minutes = (slot - 1) * interval_minutes
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


@router.get("")
def get_supply_demand(
    area: str = Query(..., description="Area code, e.g. TOKYO"),
    target_date: date = Query(..., alias="date", description="YYYY-MM-DD"),
):
    area = area.upper()
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            f"""
            SELECT trading_slot, interval_minutes, {", ".join(VALUE_COLUMNS)}
            FROM tso_area_supply_demand
            WHERE area_code = %s AND target_date = %s
            ORDER BY trading_slot
            """,
            (area, target_date),
        )
        names = [d[0] for d in cur.description]
        rows = []
        for raw in cur.fetchall():
            row = dict(zip(names, raw))
            for col in VALUE_COLUMNS:          # NUMERIC -> float, NULL stays None
                row[col] = float(row[col]) if row[col] is not None else None
            row["time"] = slot_to_time(row["trading_slot"], row["interval_minutes"])
            rows.append(row)

        # When there is no data, say how far the data goes so the UI can offer it.
        latest = None
        if not rows:
            cur.execute(
                "SELECT MAX(target_date) FROM tso_area_supply_demand WHERE area_code = %s",
                (area,),
            )
            latest = cur.fetchone()[0]

        return {
            "area": area,
            "date": target_date.isoformat(),
            "latest_date": latest.isoformat() if latest else None,
            "rows": rows,
        }
    finally:
        conn.close()
