-- Migration: drop_existing_tables
-- Drop UUID-based tables before recreating as partitioned.
-- Order matters: drop tables with FKs first.
-- areas table is NOT dropped — it has no UUID and needs no change.

DROP TABLE IF EXISTS tso_area_supply_demand;
DROP TABLE IF EXISTS jepx_spot_prices;
DROP TABLE IF EXISTS jepx_spot_summary;