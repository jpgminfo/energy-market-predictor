from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from datetime import date
from db.connection import get_connection

router = APIRouter(prefix="/api/prices", tags=["prices"])

@router.get("/latest")
def get_latest_prices(area: Optional[str] = None):
    """Get prices for the most recent available date."""
    conn = get_connection()
    try:
        cursor = conn.cursor()

        # Get latest date
        cursor.execute("SELECT MAX(target_date) FROM jepx_spot_prices;")
        latest_date = cursor.fetchone()[0]

        if not latest_date:
            raise HTTPException(status_code=404, detail="No price data found")

        return get_prices_by_date(cursor, latest_date, area)
    finally:
        conn.close()

@router.get("/summary")
def get_summary_prices(
    date_from: date = Query(..., description="Start date YYYY-MM-DD"),
    date_to: date = Query(..., description="End date YYYY-MM-DD"),
    area: Optional[str] = None
):
    """Get system price summary for a date range."""
    if (date_to - date_from).days > 365:
        raise HTTPException(status_code=400, detail="Date range cannot exceed 365 days")

    conn = get_connection()
    try:
        cursor = conn.cursor()

        if area:
            cursor.execute("""
                SELECT 
                    p.target_date,
                    p.trading_slot,
                    p.area_code,
                    p.area_price,
                    s.system_price
                FROM jepx_spot_prices p
                JOIN jepx_spot_summary s 
                    ON p.target_date = s.target_date 
                    AND p.trading_slot = s.trading_slot
                WHERE p.target_date BETWEEN %s AND %s
                AND p.area_code = %s
                ORDER BY p.target_date, p.trading_slot
            """, (date_from, date_to, area.upper()))
        else:
            cursor.execute("""
                SELECT 
                    target_date,
                    trading_slot,
                    system_price,
                    sell_bid_amount,
                    buy_bid_amount,
                    total_contract_amount
                FROM jepx_spot_summary
                WHERE target_date BETWEEN %s AND %s
                ORDER BY target_date, trading_slot
            """, (date_from, date_to))

        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in rows]
    finally:
        conn.close()

@router.get("/{target_date}")
def get_prices_for_date(
    target_date: date,
    area: Optional[str] = None
):
    """Get all area prices for a specific date."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        return get_prices_by_date(cursor, target_date, area)
    finally:
        conn.close()

def get_prices_by_date(cursor, target_date: date, area: Optional[str] = None):
    """Shared query logic for fetching prices by date."""
    if area:
        cursor.execute("""
            SELECT 
                p.target_date,
                p.trading_slot,
                p.area_code,
                p.area_price,
                s.system_price
            FROM jepx_spot_prices p
            JOIN jepx_spot_summary s
                ON p.target_date = s.target_date
                AND p.trading_slot = s.trading_slot
            WHERE p.target_date = %s
            AND p.area_code = %s
            ORDER BY p.trading_slot
        """, (target_date, area.upper()))
    else:
        cursor.execute("""
            SELECT 
                p.target_date,
                p.trading_slot,
                p.area_code,
                p.area_price,
                s.system_price
            FROM jepx_spot_prices p
            JOIN jepx_spot_summary s
                ON p.target_date = s.target_date
                AND p.trading_slot = s.trading_slot
            WHERE p.target_date = %s
            ORDER BY p.trading_slot, p.area_code
        """, (target_date,))

    rows = cursor.fetchall()
    if not rows:
        raise HTTPException(
            status_code=404,
            detail=f"No price data found for {target_date}"
        )

    columns = [desc[0] for desc in cursor.description]
    return [dict(zip(columns, row)) for row in rows]