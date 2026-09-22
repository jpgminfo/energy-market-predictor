-- Add interval_minutes column to all three tables
-- Default 30 = current Japan market standard (30min slots)

-- jepx_spot_prices
ALTER TABLE jepx_spot_prices
    ADD COLUMN interval_minutes SMALLINT NOT NULL DEFAULT 30,
    DROP CONSTRAINT jepx_spot_prices_trading_slot_check,
    ADD CONSTRAINT jepx_spot_prices_trading_slot_check
        CHECK (trading_slot BETWEEN 1 AND 96);

-- jepx_spot_summary
ALTER TABLE jepx_spot_summary
    ADD COLUMN interval_minutes SMALLINT NOT NULL DEFAULT 30,
    DROP CONSTRAINT jepx_spot_summary_trading_slot_check,
    ADD CONSTRAINT jepx_spot_summary_trading_slot_check
        CHECK (trading_slot BETWEEN 1 AND 96);

-- tso_area_supply_demand
ALTER TABLE tso_area_supply_demand
    ADD COLUMN interval_minutes SMALLINT NOT NULL DEFAULT 30,
    DROP CONSTRAINT tso_area_supply_demand_trading_slot_check,
    ADD CONSTRAINT tso_area_supply_demand_trading_slot_check
        CHECK (trading_slot BETWEEN 1 AND 96);