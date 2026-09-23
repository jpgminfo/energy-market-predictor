DROP TABLE IF EXISTS tso_area_supply_demand;

CREATE TABLE tso_area_supply_demand (
    id                      UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
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
    CONSTRAINT uq_tso_supply_demand UNIQUE (target_date, trading_slot, area_code)
);

COMMENT ON TABLE tso_area_supply_demand IS
    'Area supply/demand actual data from 9 TSOs (でんき予報). 30min interval, MW average.';