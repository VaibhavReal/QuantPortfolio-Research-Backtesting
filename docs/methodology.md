# Methodology

## 1. Market Data Pipeline
*   **Source:** Yahoo Finance via `yfinance` library.
*   **Download:** Daily Adjusted Close prices (which account for dividends and stock splits).
*   **Cleaning:** Missing values are forward-filled (`ffill`). If initial dates lack data, they are backward-filled (`bfill`) or dropped based on configuration.

## 2. Return Calculation
*   **Log Returns:** Used for covariance matrix estimation and optimization. Log returns are time-additive and normally distributed (approximately), making statistical estimation more robust.
    $R_{log, t} = \ln(\frac{P_t}{P_{t-1}})$
*   **Simple Returns:** Used for calculating the actual portfolio equity curve. Portfolio returns are cross-sectionally additive using simple returns, whereas log returns are not.
    $R_{simple, t} = \frac{P_t - P_{t-1}}{P_{t-1}}$

## 3. Portfolio Construction Strategies

### Equal Weight (1/N)
A naive allocation where capital is distributed equally among all $N$ assets.
*   **Formula:** $w_i = \frac{1}{N} \quad \forall i \in [1, N]$

### Minimum Variance
Seeks the portfolio with the absolute lowest overall volatility, regardless of expected return.
*   **Objective Function:** $\min_{w} w^T \Sigma w$
*   **Constraints:**
    *   Fully invested: $\sum_{i=1}^N w_i = 1$
    *   Long only: $w_i \ge 0$
*   **Solver:** SLSQP (Sequential Least SQuares Programming) via `scipy.optimize`.

### Risk Parity (Equal Risk Contribution)
Allocates weights such that each asset contributes equally to the total portfolio variance.
*   **Marginal Risk Contribution (MRC):** $\frac{\partial \sigma_p}{\partial w} = \frac{\Sigma w}{\sqrt{w^T \Sigma w}}$
*   **Total Risk Contribution (TRC):** $TRC_i = w_i \times MRC_i$
*   **Objective Function:** $\min_{w} \sum_{i=1}^N \sum_{j=1}^N (TRC_i - TRC_j)^2$
*   **Constraints:** Fully invested, long only.

## 4. Covariance Matrix Estimation
The covariance matrix ($\Sigma$) is estimated using historical log returns over a rolling window (e.g., 252 days) prior to the rebalancing date.
$\Sigma = \frac{1}{T-1} \sum_{t=1}^T (R_t - \bar{R})(R_t - \bar{R})^T$

## 5. Rebalancing and Backtesting Mechanics
*   **Timeline:** The backtest steps through time daily.
*   **Rebalancing:** Occurs on the last trading day of each month.
*   **Estimation Window:** To prevent look-ahead bias, weights for month $M$ are calculated using only data available up to the end of month $M-1$.
*   **Transaction Costs:** Applied upon rebalancing. Cost = $\sum_{i=1}^N |w_{i, target} - w_{i, current}| \times \text{Cost}_{bps}$

## 6. Risk Metric Formulas
Let $R_p$ be portfolio returns, $R_b$ be benchmark returns, $R_f$ be risk-free rate, $T$ be trading days in a year (252).

1.  **Annualized Return (CAGR):**
    $CAGR = (1 + \text{Cumulative Return})^{\frac{252}{\text{Days}}} - 1$
2.  **Annualized Volatility:**
    $\sigma_{ann} = \sigma_p \times \sqrt{252}$
3.  **Sharpe Ratio:**
    $\text{Sharpe} = \frac{\bar{R}_p - R_f}{\sigma_p} \times \sqrt{252}$
4.  **Sortino Ratio:** (Downside deviation $\sigma_d$)
    $\text{Sortino} = \frac{\bar{R}_p - R_f}{\sigma_d} \times \sqrt{252}$
5.  **Maximum Drawdown:**
    $MDD = \min_{t} (\frac{V_t}{V_{peak, t}} - 1)$
6.  **Beta:**
    $\beta = \frac{Cov(R_p, R_b)}{Var(R_b)}$
7.  **Tracking Error:**
    $TE = \sqrt{Var(R_p - R_b)} \times \sqrt{252}$
8.  **Calmar Ratio:**
    $\text{Calmar} = \frac{CAGR}{|MDD|}$

## 7. Data Storage & Dashboard Export
*   **DuckDB:** Time-series arrays are converted to Pandas DataFrames and loaded natively into DuckDB tables.
*   **Export:** SQL queries extract aggregated monthly metrics and daily equity curves into CSV files structured specifically for importing into Power BI or Tableau.
