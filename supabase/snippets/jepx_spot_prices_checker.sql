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

select * from jepx_spot_summary;