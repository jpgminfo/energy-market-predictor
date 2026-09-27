-- Migration: tso_area_supply_demand_partitioned
-- TSO area supply/demand actual data from 9 TSOs (でんき予報).
-- Partitioned by target_date (fiscal year: Apr → Mar).
-- Composite PK: target_date + trading_slot + area_code is naturally unique.
-- Note: tso data availability starts FY2016 (Apr 2016).

CREATE TABLE tso_area_supply_demand (
    target_date             DATE        NOT NULL,
    trading_slot            SMALLINT    NOT NULL CHECK (trading_slot BETWEEN 1 AND 96),
    area_code               VARCHAR(20) NOT NULL REFERENCES areas(area_code),
    interval_minutes        SMALLINT    NOT NULL DEFAULT 30,
    -- Demand
    area_demand             NUMERIC(10,2),
    -- Supply by source (MW average)
    nuclear                 NUMERIC(10,2),
    thermal_lng             NUMERIC(10,2),
    thermal_coal            NUMERIC(10,2),
    thermal_oil             NUMERIC(10,2),
    thermal_other           NUMERIC(10,2),
    thermal_total           NUMERIC(10,2),
    thermal_curtailment     NUMERIC(10,2),
    hydro                   NUMERIC(10,2),
    geothermal              NUMERIC(10,2),
    biomass_actual          NUMERIC(10,2),
    biomass_curtailment     NUMERIC(10,2),
    solar_actual            NUMERIC(10,2),
    solar_curtailment       NUMERIC(10,2),
    wind_actual             NUMERIC(10,2),
    wind_curtailment        NUMERIC(10,2),
    pumped_storage          NUMERIC(10,2),
    battery                 NUMERIC(10,2),
    interconnection         NUMERIC(10,2),
    other                   NUMERIC(10,2),
    total_supply            NUMERIC(10,2),
    -- Metadata
    fetched_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at              TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (target_date, trading_slot, area_code)
) PARTITION BY RANGE (target_date);

COMMENT ON TABLE tso_area_supply_demand IS
    'Area supply/demand actual from 9 TSOs (でんき予報). 30min interval, MW average. '
    'Partitioned by fiscal year (Apr-Mar). No UUID — composite PK is naturally unique. '
    'fetched_at: when pulled from TSO source. created_at: when first inserted.';

-- ── Fiscal year partitions ────────────────────────────────────────────────────

CREATE TABLE tso_area_supply_demand_fy2016
    PARTITION OF tso_area_supply_demand
    FOR VALUES FROM ('2016-04-01') TO ('2017-04-01');

CREATE TABLE tso_area_supply_demand_fy2017
    PARTITION OF tso_area_supply_demand
    FOR VALUES FROM ('2017-04-01') TO ('2018-04-01');

CREATE TABLE tso_area_supply_demand_fy2018
    PARTITION OF tso_area_supply_demand
    FOR VALUES FROM ('2018-04-01') TO ('2019-04-01');

CREATE TABLE tso_area_supply_demand_fy2019
    PARTITION OF tso_area_supply_demand
    FOR VALUES FROM ('2019-04-01') TO ('2020-04-01');

CREATE TABLE tso_area_supply_demand_fy2020
    PARTITION OF tso_area_supply_demand
    FOR VALUES FROM ('2020-04-01') TO ('2021-04-01');

CREATE TABLE tso_area_supply_demand_fy2021
    PARTITION OF tso_area_supply_demand
    FOR VALUES FROM ('2021-04-01') TO ('2022-04-01');

CREATE TABLE tso_area_supply_demand_fy2022
    PARTITION OF tso_area_supply_demand
    FOR VALUES FROM ('2022-04-01') TO ('2023-04-01');

CREATE TABLE tso_area_supply_demand_fy2023
    PARTITION OF tso_area_supply_demand
    FOR VALUES FROM ('2023-04-01') TO ('2024-04-01');

CREATE TABLE tso_area_supply_demand_fy2024
    PARTITION OF tso_area_supply_demand
    FOR VALUES FROM ('2024-04-01') TO ('2025-04-01');

CREATE TABLE tso_area_supply_demand_fy2025
    PARTITION OF tso_area_supply_demand
    FOR VALUES FROM ('2025-04-01') TO ('2026-04-01');

CREATE TABLE tso_area_supply_demand_fy2026
    PARTITION OF tso_area_supply_demand
    FOR VALUES FROM ('2026-04-01') TO ('2027-04-01');

-- Safety net partition
CREATE TABLE tso_area_supply_demand_default
    PARTITION OF tso_area_supply_demand DEFAULT;

COMMENT ON TABLE tso_area_supply_demand_default IS
    'Default partition — catches data outside defined fiscal year ranges. '
    'If data lands here, create the appropriate FY partition and move it.';
