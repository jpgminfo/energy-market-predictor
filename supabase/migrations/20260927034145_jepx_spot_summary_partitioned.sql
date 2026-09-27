-- Migration: jepx_spot_summary_partitioned
-- Market-wide bid/volume data per trading slot.
-- Partitioned by target_date (fiscal year: Apr → Mar).
-- Composite PK replaces UUID — target_date + trading_slot is naturally unique.

CREATE TABLE jepx_spot_summary (
    target_date                 DATE        NOT NULL,
    trading_slot                SMALLINT    NOT NULL CHECK (trading_slot BETWEEN 1 AND 96),
    interval_minutes            SMALLINT    NOT NULL DEFAULT 30,
    system_price                NUMERIC(10,4),
    sell_bid_amount             NUMERIC(12,2),
    buy_bid_amount              NUMERIC(12,2),
    total_contract_amount       NUMERIC(12,2),
    sell_block_bid_amount       NUMERIC(12,2),
    sell_block_contract_amount  NUMERIC(12,2),
    buy_block_bid_amount        NUMERIC(12,2),
    buy_block_contract_amount   NUMERIC(12,2),
    created_at                  TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (target_date, trading_slot)
) PARTITION BY RANGE (target_date);

COMMENT ON TABLE jepx_spot_summary IS
    'JEPX spot market summary: system price and bid volumes per slot. '
    'Partitioned by fiscal year (Apr-Mar). No UUID — composite PK is naturally unique.';

-- ── Fiscal year partitions ────────────────────────────────────────────────────
-- FY = April 1 of year N → March 31 of year N+1
-- PostgreSQL RANGE upper bound is exclusive so TO date = Apr 1 of next year

CREATE TABLE jepx_spot_summary_fy2016
    PARTITION OF jepx_spot_summary
    FOR VALUES FROM ('2016-04-01') TO ('2017-04-01');

CREATE TABLE jepx_spot_summary_fy2017
    PARTITION OF jepx_spot_summary
    FOR VALUES FROM ('2017-04-01') TO ('2018-04-01');

CREATE TABLE jepx_spot_summary_fy2018
    PARTITION OF jepx_spot_summary
    FOR VALUES FROM ('2018-04-01') TO ('2019-04-01');

CREATE TABLE jepx_spot_summary_fy2019
    PARTITION OF jepx_spot_summary
    FOR VALUES FROM ('2019-04-01') TO ('2020-04-01');

CREATE TABLE jepx_spot_summary_fy2020
    PARTITION OF jepx_spot_summary
    FOR VALUES FROM ('2020-04-01') TO ('2021-04-01');

CREATE TABLE jepx_spot_summary_fy2021
    PARTITION OF jepx_spot_summary
    FOR VALUES FROM ('2021-04-01') TO ('2022-04-01');

CREATE TABLE jepx_spot_summary_fy2022
    PARTITION OF jepx_spot_summary
    FOR VALUES FROM ('2022-04-01') TO ('2023-04-01');

CREATE TABLE jepx_spot_summary_fy2023
    PARTITION OF jepx_spot_summary
    FOR VALUES FROM ('2023-04-01') TO ('2024-04-01');

CREATE TABLE jepx_spot_summary_fy2024
    PARTITION OF jepx_spot_summary
    FOR VALUES FROM ('2024-04-01') TO ('2025-04-01');

CREATE TABLE jepx_spot_summary_fy2025
    PARTITION OF jepx_spot_summary
    FOR VALUES FROM ('2025-04-01') TO ('2026-04-01');

CREATE TABLE jepx_spot_summary_fy2026
    PARTITION OF jepx_spot_summary
    FOR VALUES FROM ('2026-04-01') TO ('2027-04-01');

-- Safety net: catches data outside defined partitions
-- Prevents insert failures if FY2027 partition is not yet created
CREATE TABLE jepx_spot_summary_default
    PARTITION OF jepx_spot_summary DEFAULT;

COMMENT ON TABLE jepx_spot_summary_default IS
    'Default partition — catches data outside defined fiscal year ranges. '
    'If data lands here, create the appropriate FY partition and move it.';
