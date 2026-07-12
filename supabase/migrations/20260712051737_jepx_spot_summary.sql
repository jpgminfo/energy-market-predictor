CREATE TABLE jepx_spot_summary (
    id                          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    target_date                 DATE        NOT NULL,
    trading_slot                SMALLINT    NOT NULL CHECK (trading_slot BETWEEN 1 AND 48),
    system_price                NUMERIC(10,4) NOT NULL,
    sell_bid_amount             NUMERIC(12,2),
    buy_bid_amount              NUMERIC(12,2),
    total_contract_amount       NUMERIC(12,2),
    sell_block_bid_amount       NUMERIC(12,2),
    sell_block_contract_amount  NUMERIC(12,2),
    buy_block_bid_amount        NUMERIC(12,2),
    buy_block_contract_amount   NUMERIC(12,2),
    created_at                  TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT uq_jepx_summary UNIQUE (target_date, trading_slot)
);