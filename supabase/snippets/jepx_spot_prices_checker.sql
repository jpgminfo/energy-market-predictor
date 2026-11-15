SELECT 
    MIN(target_date) AS earliest,
    MAX(target_date) AS latest,
    COUNT(DISTINCT target_date) AS total_days
FROM jepx_spot_prices;

SELECT 
    EXTRACT(YEAR FROM target_date) AS year,
    COUNT(DISTINCT target_date) AS days,
    MIN(target_date) AS from_date,
    MAX(target_date) AS to_date
FROM jepx_spot_prices
GROUP BY year
ORDER BY year;

SELECT 
    target_date,
    COUNT(*) as area_count
FROM jepx_spot_prices
WHERE target_date BETWEEN '2018-09-06' AND '2018-09-26'
AND area_code = 'HOKKAIDO'
GROUP BY target_date
ORDER BY target_date;

SELECT target_date, buy_block_bid_amount, buy_block_contract_amount
FROM jepx_spot_summary_fy2017
WHERE buy_block_bid_amount IS NOT NULL
ORDER BY target_date
LIMIT 1;

SELECT 'prices' AS t, COUNT(*) FROM jepx_spot_prices
 WHERE target_date >= '2016-04-01' AND target_date < '2017-04-01'
UNION ALL
SELECT 'summary', COUNT(*) FROM jepx_spot_summary
 WHERE target_date >= '2016-04-01' AND target_date < '2017-04-01';


SELECT MAX(target_date) FROM jepx_spot_summary;
select min(target_date) from tso_area_supply_demand_fy2026;