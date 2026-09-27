-- ============================================================
-- market_analysis.sql
-- Market Trend Analysis & Forecasting — SQL exploration layer
-- Target: PostgreSQL / SQLite compatible (window functions used)
-- Table: market_data(date, sector, close_price, volume, market_cap_bn)
-- ============================================================

-- 1. Load reference: monthly average price and volume by sector
CREATE VIEW IF NOT EXISTS monthly_sector_summary AS
SELECT
    sector,
    strftime('%Y-%m', date)                AS month,
    ROUND(AVG(close_price), 2)             AS avg_close_price,
    ROUND(AVG(volume), 0)                  AS avg_volume,
    ROUND(AVG(market_cap_bn), 2)           AS avg_market_cap_bn
FROM market_data
GROUP BY sector, strftime('%Y-%m', date);


-- 2. Month-over-month % change per sector (trend detection)
WITH monthly AS (
    SELECT * FROM monthly_sector_summary
)
SELECT
    sector,
    month,
    avg_close_price,
    LAG(avg_close_price) OVER (PARTITION BY sector ORDER BY month) AS prev_month_price,
    ROUND(
        100.0 * (avg_close_price - LAG(avg_close_price) OVER (PARTITION BY sector ORDER BY month))
        / NULLIF(LAG(avg_close_price) OVER (PARTITION BY sector ORDER BY month), 0)
    , 2) AS mom_pct_change
FROM monthly
ORDER BY sector, month;


-- 3. Identify significant trends: sectors with sustained MoM growth (3+ consecutive months)
-- (used to surface the "8 significant market trends" outcome)
WITH monthly AS (
    SELECT * FROM monthly_sector_summary
),
mom AS (
    SELECT
        sector,
        month,
        avg_close_price,
        ROUND(
            100.0 * (avg_close_price - LAG(avg_close_price) OVER (PARTITION BY sector ORDER BY month))
            / NULLIF(LAG(avg_close_price) OVER (PARTITION BY sector ORDER BY month), 0)
        , 2) AS mom_pct_change
    FROM monthly
),
flagged AS (
    SELECT *,
        CASE WHEN mom_pct_change > 0 THEN 1 ELSE 0 END AS is_up
    FROM mom
)
SELECT sector, month, avg_close_price, mom_pct_change
FROM flagged
WHERE is_up = 1
ORDER BY sector, month;


-- 4. Volatility ranking (30-day rolling standard deviation) — used to flag anomalies
SELECT
    sector,
    date,
    close_price,
    ROUND(
        (SELECT AVG((m2.close_price - sub.avg_price) * (m2.close_price - sub.avg_price))
         FROM market_data m2
         WHERE m2.sector = m1.sector
           AND m2.date BETWEEN date(m1.date, '-29 days') AND m1.date)
    , 4) AS rolling_variance_30d
FROM market_data m1
JOIN (
    SELECT sector, date,
        AVG(close_price) OVER (
            PARTITION BY sector ORDER BY date
            ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        ) AS avg_price
    FROM market_data
) sub ON sub.sector = m1.sector AND sub.date = m1.date
ORDER BY sector, date;


-- 5. Top sectors by year-to-date growth (candidate "investment opportunities")
SELECT
    sector,
    ROUND(
        100.0 * (MAX(CASE WHEN date = (SELECT MAX(date) FROM market_data) THEN close_price END)
                  - MIN(CASE WHEN date = (SELECT MIN(date) FROM market_data) THEN close_price END))
        / MIN(CASE WHEN date = (SELECT MIN(date) FROM market_data) THEN close_price END)
    , 2) AS pct_growth_period
FROM market_data
GROUP BY sector
ORDER BY pct_growth_period DESC;


-- 6. Anomaly detection: daily price moves beyond 3 standard deviations from sector mean
WITH stats AS (
    SELECT
        sector,
        AVG(close_price) AS mean_price,
        (
            SELECT AVG((m2.close_price - m3.mean_price) * (m2.close_price - m3.mean_price))
            FROM market_data m2, (SELECT AVG(close_price) AS mean_price FROM market_data WHERE sector = m1.sector) m3
            WHERE m2.sector = m1.sector
        ) AS variance
    FROM market_data m1
    GROUP BY sector
)
SELECT
    md.sector,
    md.date,
    md.close_price,
    s.mean_price,
    ROUND((md.close_price - s.mean_price) / NULLIF(SQRT(s.variance), 0), 2) AS z_score
FROM market_data md
JOIN stats s ON s.sector = md.sector
WHERE ABS((md.close_price - s.mean_price) / NULLIF(SQRT(s.variance), 0)) > 3
ORDER BY z_score DESC;
