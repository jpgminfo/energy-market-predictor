CREATE TABLE jepx_spot_prices (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    target_date     DATE        NOT NULL,
    trading_slot    SMALLINT    NOT NULL CHECK (trading_slot BETWEEN 1 AND 48),
    area_code       VARCHAR(20) NOT NULL REFERENCES areas(area_code),
    area_price      NUMERIC(10,4) NOT NULL,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT uq_jepx_spot UNIQUE (target_date, trading_slot, area_code)
);