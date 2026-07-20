-- Migration: areas
-- TSO area master table for Japan electricity market
-- Area boundaries fixed since market liberalization April 2016

-- Trigger function must exist before this migration runs
-- (created in: 20260628094317_trigger_updated_at.sql)

CREATE TABLE areas (
    area_code       VARCHAR(20)     PRIMARY KEY,
    area_number     SMALLINT        UNIQUE,
    area_name_ja    VARCHAR(50)     NOT NULL,
    area_name_en    VARCHAR(50)     NOT NULL,
    valid_from      DATE            NOT NULL,
    valid_to        DATE,                        -- NULL = currently active
    created_at      TIMESTAMPTZ     DEFAULT NOW(),
    updated_at      TIMESTAMPTZ     DEFAULT NOW(),
    CONSTRAINT chk_area_number CHECK (area_number BETWEEN 1 AND 10)
);

COMMENT ON TABLE areas IS 'TSO area master. Area definitions fixed since Japan market liberalization 2016-04-01.';
COMMENT ON COLUMN areas.area_code IS 'Readable identifier used as FK across all tables. e.g. TOKYO, KANSAI.';
COMMENT ON COLUMN areas.area_number IS 'Official TSO number 1-10 per OCCTO/JEPX convention.';
COMMENT ON COLUMN areas.valid_from IS 'Date this area definition became effective.';
COMMENT ON COLUMN areas.valid_to IS 'Date this area definition was superseded. NULL = currently active.';

-- Auto-update updated_at on any row change
CREATE TRIGGER set_updated_at_areas
    BEFORE UPDATE ON areas
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- Seed data
-- valid_from = 2016-04-01: Japan electricity market liberalization date
-- Okinawa included as area master even though not in JEPX spot market
INSERT INTO areas (area_code, area_number, area_name_ja, area_name_en, valid_from) VALUES
    ('HOKKAIDO',    1, '北海道',           'Hokkaido',     '2016-04-01'),
    ('TOHOKU',      2, '東北',             'Tohoku',       '2016-04-01'),
    ('TOKYO',       3, '東京',             'Tokyo',        '2016-04-01'),
    ('CHUBU',       4, '中部',             'Chubu',        '2016-04-01'),
    ('HOKURIKU',    5, '北陸',             'Hokuriku',     '2016-04-01'),
    ('KANSAI',      6, '関西',             'Kansai',       '2016-04-01'),
    ('CHUGOKU',     7, '中国',             'Chugoku',      '2016-04-01'),
    ('SHIKOKU',     8, '四国',             'Shikoku',      '2016-04-01'),
    ('KYUSHU',      9, '九州',             'Kyushu',       '2016-04-01'),
    ('OKINAWA',    10, '沖縄',             'Okinawa',      '2016-04-01');