-- Migration: jepx_spot_prices_partitioned
-- Area prices per trading slot per area.
-- Partitioned by target_date (fiscal year: Apr → Mar).
-- Composite PK: target_date + trading_slot + area_code is naturally unique.
-- FK to areas table: supported in PostgreSQL 12+ from partitioned table.

CREATE TABLE jepx_spot_prices (
    target_date         DATE        NOT NULL,
    trading_slot        SMALLINT    NOT NULL CHECK (trading_slot BETWEEN 1 AND 96),
    area_code           VARCHAR(20) NOT NULL REFERENCES areas(area_code),
    interval_minutes    SMALLINT    NOT NULL DEFAULT 30,
    area_price          NUMERIC(10,4),
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (target_date, trading_slot, area_code)
) PARTITION BY RANGE (target_date);

COMMENT ON TABLE jepx_spot_prices IS
    'JEPX area prices per slot. Partitioned by fiscal year (Apr-Mar). '
    'No UUID — composite PK is naturally unique. '
    'JOIN with jepx_spot_summary on (target_date, trading_slot) for system price.';

-- ── Fiscal year partitions ────────────────────────────────────────────────────

CREATE TABLE jepx_spot_prices_fy2016
    PARTITION OF jepx_spot_prices
    FOR VALUES FROM ('2016-04-01') TO ('2017-04-01');

CREATE TABLE jepx_spot_prices_fy2017
    PARTITION OF jepx_spot_prices
    FOR VALUES FROM ('2017-04-01') TO ('2018-04-01');

CREATE TABLE jepx_spot_prices_fy2018
    PARTITION OF jepx_spot_prices
    FOR VALUES FROM ('2018-04-01') TO ('2019-04-01');

CREATE TABLE jepx_spot_prices_fy2019
    PARTITION OF jepx_spot_prices
    FOR VALUES FROM ('2019-04-01') TO ('2020-04-01');

CREATE TABLE jepx_spot_prices_fy2020
    PARTITION OF jepx_spot_prices
    FOR VALUES FROM ('2020-04-01') TO ('2021-04-01');

CREATE TABLE jepx_spot_prices_fy2021
    PARTITION OF jepx_spot_prices
    FOR VALUES FROM ('2021-04-01') TO ('2022-04-01');

CREATE TABLE jepx_spot_prices_fy2022
    PARTITION OF jepx_spot_prices
    FOR VALUES FROM ('2022-04-01') TO ('2023-04-01');

CREATE TABLE jepx_spot_prices_fy2023
    PARTITION OF jepx_spot_prices
    FOR VALUES FROM ('2023-04-01') TO ('2024-04-01');

CREATE TABLE jepx_spot_prices_fy2024
    PARTITION OF jepx_spot_prices
    FOR VALUES FROM ('2024-04-01') TO ('2025-04-01');

CREATE TABLE jepx_spot_prices_fy2025
    PARTITION OF jepx_spot_prices
    FOR VALUES FROM ('2025-04-01') TO ('2026-04-01');

CREATE TABLE jepx_spot_prices_fy2026
    PARTITION OF jepx_spot_prices
    FOR VALUES FROM ('2026-04-01') TO ('2027-04-01');

-- Safety net partition
CREATE TABLE jepx_spot_prices_default
    PARTITION OF jepx_spot_prices DEFAULT;

COMMENT ON TABLE jepx_spot_prices_default IS
    'Default partition — catches data outside defined fiscal year ranges. '
    'If data lands here, create the appropriate FY partition and move it.';
