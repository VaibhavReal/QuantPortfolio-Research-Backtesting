-- ==============================================================================
-- Quantitative Portfolio Backtesting Platform - Useful SQL Queries
-- ==============================================================================
-- These queries demonstrate analytical SQL workflows for quantitative investment
-- analysis in DuckDB (and are 100% compatible with PostgreSQL syntax).

-- ------------------------------------------------------------------------------
-- 1. Get the latest adjusted close price for each asset
-- Use Case: Fetching the most recent pricing data to calculate current portfolio 
-- value or generate today's trading signals.
-- ------------------------------------------------------------------------------
WITH LatestDates AS (
    SELECT asset_id, MAX(date) as max_date
    FROM price_data
    GROUP BY asset_id
)
SELECT a.ticker, a.name, a.sector, p.date, p.adj_close
FROM price_data p
JOIN assets a ON p.asset_id = a.asset_id
JOIN LatestDates ld ON p.asset_id = ld.asset_id AND p.date = ld.max_date
ORDER BY a.ticker;

-- ------------------------------------------------------------------------------
-- 2. Calculate daily log returns for all assets
-- Use Case: Generating input features for statistical models or calculating volatility.
-- We use the LAG window function to get the previous day's price.
-- ------------------------------------------------------------------------------
SELECT 
    a.ticker,
    p.date,
    p.adj_close,
    LN(p.adj_close / LAG(p.adj_close) OVER (PARTITION BY p.asset_id ORDER BY p.date)) as log_return
FROM price_data p
JOIN assets a ON p.asset_id = a.asset_id
ORDER BY a.ticker, p.date;

-- ------------------------------------------------------------------------------
-- 3. Calculate total return per asset over the full backtest period
-- Use Case: Evaluating the buy-and-hold performance of individual assets.
-- ------------------------------------------------------------------------------
WITH FirstLastPrices AS (
    SELECT 
        asset_id,
        FIRST_VALUE(adj_close) OVER (PARTITION BY asset_id ORDER BY date) as start_price,
        LAST_VALUE(adj_close) OVER (PARTITION BY asset_id ORDER BY date RANGE BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) as end_price
    FROM price_data
)
SELECT DISTINCT 
    a.ticker,
    a.name,
    a.sector,
    ROUND(f.start_price, 2) AS start_price,
    ROUND(f.end_price, 2) AS end_price,
    ROUND((f.end_price - f.start_price) / f.start_price * 100, 2) AS total_return_pct
FROM FirstLastPrices f
JOIN assets a ON f.asset_id = a.asset_id
ORDER BY total_return_pct DESC;

-- ------------------------------------------------------------------------------
-- 4. Compare annualized return (CAGR) across all strategies
-- Use Case: High-level comparison of long-term profitability of different models.
-- ------------------------------------------------------------------------------
SELECT 
    s.name AS strategy_name, 
    ROUND(rm.metric_value * 100, 2) AS cagr_pct,
    rm.computed_date
FROM risk_metrics rm
JOIN strategies s ON rm.strategy_id = s.strategy_id
WHERE rm.metric_name = 'CAGR'
ORDER BY rm.metric_value DESC;

-- ------------------------------------------------------------------------------
-- 5. Compare Sharpe ratios across all strategies
-- Use Case: Evaluating the risk-adjusted returns of strategies to find the best 
-- balance between return and volatility.
-- ------------------------------------------------------------------------------
SELECT 
    s.name AS strategy_name, 
    ROUND(rm.metric_value, 4) AS sharpe_ratio
FROM risk_metrics rm
JOIN strategies s ON rm.strategy_id = s.strategy_id
WHERE rm.metric_name = 'Sharpe Ratio'
ORDER BY rm.metric_value DESC;

-- ------------------------------------------------------------------------------
-- 6. Get maximum drawdown per strategy
-- Use Case: Understanding the worst-case historical scenario (peak-to-trough drop) 
-- for risk management purposes.
-- ------------------------------------------------------------------------------
SELECT 
    s.name AS strategy_name, 
    ROUND(rm.metric_value * 100, 2) AS max_drawdown_pct
FROM risk_metrics rm
JOIN strategies s ON rm.strategy_id = s.strategy_id
WHERE rm.metric_name = 'Max Drawdown'
ORDER BY rm.metric_value DESC;

-- ------------------------------------------------------------------------------
-- 7. Get portfolio weights for a specific strategy on the most recent rebalance date
-- Use Case: Executing trades based on the latest generated allocations from a model.
-- ------------------------------------------------------------------------------
WITH LatestRebalance AS (
    SELECT strategy_id, MAX(date) as max_date
    FROM portfolio_weights
    GROUP BY strategy_id
)
SELECT 
    s.name AS strategy_name,
    a.ticker,
    a.name AS asset_name,
    pw.date AS rebalance_date,
    ROUND(pw.weight * 100, 2) AS weight_pct
FROM portfolio_weights pw
JOIN strategies s ON pw.strategy_id = s.strategy_id
JOIN assets a ON pw.asset_id = a.asset_id
JOIN LatestRebalance lr ON pw.strategy_id = lr.strategy_id AND pw.date = lr.max_date
WHERE s.name = 'Risk Parity'
ORDER BY pw.weight DESC;

-- ------------------------------------------------------------------------------
-- 8. Get the average portfolio weight per asset per strategy over the full backtest
-- Use Case: Analyzing long-term strategy behavior and identifying structural biases 
-- (e.g., is the strategy persistently overweight tech stocks?).
-- ------------------------------------------------------------------------------
SELECT 
    s.name AS strategy_name,
    a.ticker,
    ROUND(AVG(pw.weight) * 100, 2) AS average_weight_pct
FROM portfolio_weights pw
JOIN strategies s ON pw.strategy_id = s.strategy_id
JOIN assets a ON pw.asset_id = a.asset_id
GROUP BY s.name, a.ticker
ORDER BY s.name, AVG(pw.weight) DESC;

-- ------------------------------------------------------------------------------
-- 9. Get the strategy with the highest Sharpe ratio
-- Use Case: Programmatically identifying the best performing model for deployment.
-- ------------------------------------------------------------------------------
SELECT 
    s.name AS strategy_name, 
    ROUND(rm.metric_value, 4) AS sharpe_ratio
FROM risk_metrics rm
JOIN strategies s ON rm.strategy_id = s.strategy_id
WHERE rm.metric_name = 'Sharpe Ratio'
ORDER BY rm.metric_value DESC
LIMIT 1;

-- ------------------------------------------------------------------------------
-- 10. Get daily portfolio value for all strategies on a specific date range
-- Use Case: Plotting comparative equity curves over a specific market regime 
-- (e.g., the 2020 COVID crash).
-- ------------------------------------------------------------------------------
SELECT 
    s.name AS strategy_name,
    br.date,
    ROUND(br.portfolio_value, 2) AS portfolio_value,
    ROUND(br.daily_return * 100, 4) AS daily_return_pct
FROM backtest_results br
JOIN strategies s ON br.strategy_id = s.strategy_id
WHERE br.date BETWEEN '2020-02-01' AND '2020-04-30'
ORDER BY br.date, s.name;

-- ------------------------------------------------------------------------------
-- 11. Calculate rolling 21-day average portfolio value per strategy
-- Use Case: Smoothing out equity curves to analyze longer-term trends or applying 
-- moving average crossover rules on strategy equity.
-- ------------------------------------------------------------------------------
SELECT 
    s.name AS strategy_name,
    br.date,
    ROUND(br.portfolio_value, 2) AS portfolio_value,
    ROUND(AVG(br.portfolio_value) OVER (
        PARTITION BY br.strategy_id 
        ORDER BY br.date 
        ROWS BETWEEN 20 PRECEDING AND CURRENT ROW
    ), 2) AS ma_21_portfolio_value
FROM backtest_results br
JOIN strategies s ON br.strategy_id = s.strategy_id
ORDER BY s.name, br.date;

-- ------------------------------------------------------------------------------
-- 12. Count total number of rebalances per strategy
-- Use Case: Estimating transaction costs and turnover. Frequent rebalancing 
-- strategies will have higher costs.
-- ------------------------------------------------------------------------------
SELECT 
    s.name AS strategy_name,
    COUNT(DISTINCT pw.date) AS total_rebalances
FROM portfolio_weights pw
JOIN strategies s ON pw.strategy_id = s.strategy_id
GROUP BY s.name
ORDER BY total_rebalances DESC;

-- ------------------------------------------------------------------------------
-- 13. Get the top 3 best performing assets by total return
-- Use Case: Identifying outliers in the investable universe that might be driving 
-- aggregate strategy performance.
-- ------------------------------------------------------------------------------
WITH AssetReturns AS (
    SELECT 
        asset_id,
        (LAST_VALUE(adj_close) OVER (PARTITION BY asset_id ORDER BY date RANGE BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) - 
         FIRST_VALUE(adj_close) OVER (PARTITION BY asset_id ORDER BY date)) / 
         FIRST_VALUE(adj_close) OVER (PARTITION BY asset_id ORDER BY date) AS total_return
    FROM price_data
)
SELECT DISTINCT 
    a.ticker, 
    a.name,
    ROUND(ar.total_return * 100, 2) AS total_return_pct
FROM AssetReturns ar
JOIN assets a ON ar.asset_id = a.asset_id
ORDER BY ar.total_return DESC
LIMIT 3;

-- ------------------------------------------------------------------------------
-- 14. Get risk metrics side-by-side for all strategies (pivot-style)
-- Use Case: Generating a comprehensive tear sheet or summary table comparing 
-- key metrics for all models simultaneously.
-- ------------------------------------------------------------------------------
SELECT 
    s.name AS strategy_name,
    ROUND(MAX(CASE WHEN rm.metric_name = 'CAGR' THEN rm.metric_value END) * 100, 2) AS cagr_pct,
    ROUND(MAX(CASE WHEN rm.metric_name = 'Ann. Volatility' THEN rm.metric_value END) * 100, 2) AS volatility_pct,
    ROUND(MAX(CASE WHEN rm.metric_name = 'Sharpe Ratio' THEN rm.metric_value END), 4) AS sharpe_ratio,
    ROUND(MAX(CASE WHEN rm.metric_name = 'Sortino Ratio' THEN rm.metric_value END), 4) AS sortino_ratio,
    ROUND(MAX(CASE WHEN rm.metric_name = 'Max Drawdown' THEN rm.metric_value END) * 100, 2) AS max_drawdown_pct,
    ROUND(MAX(CASE WHEN rm.metric_name = 'Beta' THEN rm.metric_value END), 4) AS beta
FROM strategies s
LEFT JOIN risk_metrics rm ON s.strategy_id = rm.strategy_id
GROUP BY s.name
ORDER BY sharpe_ratio DESC;

-- ------------------------------------------------------------------------------
-- 15. Get the dates with the largest single-day portfolio loss per strategy
-- Use Case: Investigating extreme tail events or identifying bugs/data errors 
-- that cause massive single-day drops in simulated performance.
-- ------------------------------------------------------------------------------
WITH RankedLosses AS (
    SELECT 
        strategy_id,
        date,
        daily_return,
        RANK() OVER (PARTITION BY strategy_id ORDER BY daily_return ASC) as loss_rank
    FROM backtest_results
    WHERE daily_return IS NOT NULL
)
SELECT 
    s.name AS strategy_name,
    rl.date,
    ROUND(rl.daily_return * 100, 2) AS worst_single_day_return_pct
FROM RankedLosses rl
JOIN strategies s ON rl.strategy_id = s.strategy_id
WHERE rl.loss_rank = 1
ORDER BY rl.daily_return ASC;
