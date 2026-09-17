# Project Architecture

## Overview
This quantitative portfolio research and backtesting platform is built using a modular 10-component Python architecture. It processes historical market data for a universe of 12 US large-cap stocks against the S&P 500 benchmark, executes multiple portfolio optimization strategies (Equal Weight, Minimum Variance, Risk Parity), runs a realistic historical backtest with transaction costs and rebalancing, computes comprehensive risk metrics, stores results in a columnar DuckDB database, and exports data for downstream visualization.

## Module Descriptions

### 1. config (src/config.py)
* **Purpose**: Centralized configuration management for the entire platform.
* **Inputs**: None (hardcoded or environment variables).
* **Outputs**: Constants (date ranges, tickers, risk-free rate, transaction costs, database paths).
* **Key Functions**: N/A (typically constant definitions or dataclasses).
* **Dependencies**: None.

### 2. data_loader (src/data_loader.py)
* **Purpose**: Fetches historical market data from Yahoo Finance.
* **Inputs**: Ticker list, start date, end date.
* **Outputs**: Raw Pandas DataFrame containing daily Adjusted Close prices.
* **Key Functions**: `download_market_data(tickers, start_date, end_date)`.
* **Dependencies**: `yfinance`, `pandas`, `config`.

### 3. data_cleaning (src/data_cleaning.py)
* **Purpose**: Validates and cleans raw market data.
* **Inputs**: Raw price DataFrame.
* **Outputs**: Cleaned price DataFrame (forward filled, dropped NAs).
* **Key Functions**: `clean_price_data(df)`.
* **Dependencies**: `pandas`.

### 4. returns (src/returns.py)
* **Purpose**: Computes log and simple returns.
* **Inputs**: Cleaned price DataFrame.
* **Outputs**: Log returns DataFrame, Simple returns DataFrame.
* **Key Functions**: `calculate_log_returns(prices)`, `calculate_simple_returns(prices)`.
* **Dependencies**: `pandas`, `numpy`.

### 5. portfolio (src/portfolio.py)
* **Purpose**: Handles portfolio state, holdings, and basic operations.
* **Inputs**: Asset prices, weights, current capital.
* **Outputs**: Portfolio value, asset allocations.
* **Key Functions**: `initialize_portfolio(capital)`, `update_holdings(prices, weights)`.
* **Dependencies**: `pandas`, `numpy`.

### 6. optimization (src/optimization.py)
* **Purpose**: Generates target weights using various quantitative strategies.
* **Inputs**: Covariance matrix, expected returns (optional), strategy type.
* **Outputs**: Optimal weight array.
* **Key Functions**: `equal_weight(n)`, `min_variance(cov_matrix)`, `risk_parity(cov_matrix)`.
* **Dependencies**: `numpy`, `scipy.optimize`.

### 7. backtest (src/backtest.py)
* **Purpose**: Simulates the portfolio performance over time with rebalancing and costs.
* **Inputs**: Returns data, strategy type, rebalance frequency, transaction cost rate.
* **Outputs**: Daily portfolio returns, equity curve, turnover.
* **Key Functions**: `run_backtest(returns, strategy, rebalance_freq, t_cost)`.
* **Dependencies**: `pandas`, `numpy`, `optimization`, `portfolio`, `config`.

### 8. risk_metrics (src/risk_metrics.py)
* **Purpose**: Calculates absolute and relative performance metrics.
* **Inputs**: Portfolio returns, benchmark returns, risk-free rate.
* **Outputs**: Dictionary of computed metrics (Sharpe, Max Drawdown, etc.).
* **Key Functions**: `compute_all_metrics(port_returns, bench_returns, rf_rate)`.
* **Dependencies**: `pandas`, `numpy`.

### 9. benchmark (src/benchmark.py)
* **Purpose**: Fetches and processes benchmark (S&P 500) performance.
* **Inputs**: Benchmark ticker, start date, end date.
* **Outputs**: Benchmark daily returns and equity curve.
* **Key Functions**: `get_benchmark_performance(ticker, start, end)`.
* **Dependencies**: `data_loader`, `returns`.

### 10. database (src/database.py)
* **Purpose**: Manages DuckDB connection, schema creation, and data persistence.
* **Inputs**: DataFrames, Metric dictionaries.
* **Outputs**: DuckDB database file updates.
* **Key Functions**: `init_db()`, `save_timeseries()`, `save_metrics()`.
* **Dependencies**: `duckdb`, `pandas`.

### 11. export_results (src/export_results.py)
* **Purpose**: Extracts data from DuckDB to CSV/Excel for BI tools (Power BI/Tableau).
* **Inputs**: DuckDB connection.
* **Outputs**: CSV/Excel files.
* **Key Functions**: `export_to_csv()`.
* **Dependencies**: `duckdb`, `pandas`.

## Data Flow Architecture

```text
[Yahoo Finance API]
       |
       v
+--------------+    +---------------+    +-----------+
| data_loader  |--->| data_cleaning |--->|  returns  |
+--------------+    +---------------+    +-----------+
                                               |
                                               v
+--------------+    +---------------+    +-----------+
| optimization |<---|   portfolio   |<---| backtest  |
+--------------+    +---------------+    +-----------+
       |                                       |
       v                                       v
+--------------+                         +--------------+
| benchmark    |                         | risk_metrics |
+--------------+                         +--------------+
       \                                       /
        \                                     /
         v                                   v
      +-----------------------------------------+
      |               database                  |
      +-----------------------------------------+
                          |
                          v
                  +----------------+
                  | export_results |
                  +----------------+
                          |
                          v
               [Power BI / Tableau]
```

## Database Architecture
**Why DuckDB?**
DuckDB was chosen for its exceptional performance on analytical (OLAP) queries, zero-configuration setup, and deep integration with Pandas. Because financial time-series data is fundamentally columnar (e.g., querying the 'AAPL' column across all dates), DuckDB provides massive speedups over row-oriented databases like SQLite.

**Schema Overview:**
*   `daily_returns` (date, ticker, return_val, strategy_name)
*   `equity_curves` (date, strategy_name, portfolio_value)
*   `portfolio_weights` (date, ticker, weight, strategy_name)
*   `risk_metrics` (strategy_name, metric_name, value)

**Migration Path to PostgreSQL:**
DuckDB uses PostgreSQL-compatible SQL syntax. Should the project require concurrent writes, web-server deployment, or distributed access, migrating to PostgreSQL involves setting up a Postgres instance, updating the connection string via SQLAlchemy, and using `psycopg2`. The underlying SQL schemas and queries will remain largely identical.

## Scalability and Future-Proofing
The current architecture elegantly handles 10-15 stocks. As the universe expands, architectural shifts are required:

*   **25-50 Stocks:**
    *   *Covariance Matrix:* The sample covariance matrix becomes noisy. We must implement Ledoit-Wolf shrinkage or condition the matrix to ensure the optimizer converges and weights aren't dominated by estimation error.
    *   *Optimizer Runtime:* SLSQP will slow down. Switching to OSQP or a specialized convex optimization solver becomes necessary.
*   **100+ Stocks:**
    *   *Memory:* Pandas DataFrames holding full tick data may exceed RAM. Polars or direct out-of-core DuckDB processing is needed.
    *   *Data Pipeline:* Sequential Yahoo Finance downloads will bottleneck. Asynchronous fetching (`asyncio`, `aiohttp`) or a dedicated financial data provider (e.g., Alpaca, Polygon) must replace `yfinance`.

## Module Dependency Graph
```text
config
  |-- data_loader
  |-- backtest

data_loader
  |-- benchmark

data_cleaning
  |-- (uses pandas)

returns
  |-- benchmark
  |-- backtest

portfolio
  |-- backtest

optimization
  |-- backtest

backtest
  |-- risk_metrics

database
  |-- export_results
```
