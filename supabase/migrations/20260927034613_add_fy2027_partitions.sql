-- Migration: add_fy2027_partitions
-- Template for adding next fiscal year partitions each April.
-- Copy this file, update year, and run npx supabase migration up.
-- Run this in March before FY2027 data starts arriving.

CREATE TABLE jepx_spot_summary_fy2027
    PARTITION OF jepx_spot_summary
    FOR VALUES FROM ('2027-04-01') TO ('2028-04-01');

CREATE TABLE jepx_spot_prices_fy2027
    PARTITION OF jepx_spot_prices
    FOR VALUES FROM ('2027-04-01') TO ('2028-04-01');

CREATE TABLE tso_area_supply_demand_fy2027
    PARTITION OF tso_area_supply_demand
    FOR VALUES FROM ('2027-04-01') TO ('2028-04-01');
