# Limitations and Weaknesses

An intellectually honest assessment of the platform's limitations. Understanding these weaknesses is crucial for quantitative research and technical interviews.

## 1. Limited Stock Universe
*   **Limitation:** The portfolio universe is restricted to 12 US large-cap stocks.
*   **Impact:** This prevents the demonstration of true large-scale portfolio optimization (e.g., 500 or 3000 stocks) where computational efficiency and matrix conditioning become critical. It also inherently limits the diversification potential compared to broad market indices.

## 2. Survivorship Bias in Stock Selection
*   **Limitation:** The 12 stocks were chosen today based on their current prominence (e.g., AAPL, MSFT).
*   **Impact:** We are testing on companies we already know survived and thrived over the backtest period. If we had picked the top 12 companies in 2000, several might have collapsed (e.g., Enron, Lehman Brothers). This artificially inflates the backtest's CAGR and Sharpe ratio.

## 3. Simplified Transaction Cost Model
*   **Limitation:** A flat 10 basis points (0.1%) is applied to total turnover.
*   **Impact:** Real-world trading involves variable broker commissions, bid-ask spreads, and regulatory fees. A flat rate oversimplifies the friction of trading, potentially making high-turnover strategies look more profitable than they are in reality.

## 4. No Market Impact Model
*   **Limitation:** The backtest assumes we can execute any size trade exactly at the historical closing price.
*   **Impact:** In reality, if a fund tries to buy $100 million of a stock, their own buying pressure pushes the price up before execution is complete. By ignoring market impact, capacity limits of the strategy are not tested.

## 5. No Slippage Model
*   **Limitation:** We assume execution at exactly the recorded closing price.
*   **Impact:** Market volatility often causes orders (especially market-on-close orders) to execute slightly worse than the theoretical close. Zero slippage models slightly overestimate returns. (Though for our 12 highly liquid large-caps, this effect is minimal).

## 6. Historical Data Quality
*   **Limitation:** Relying on Yahoo Finance (`yfinance`) for historical data.
*   **Impact:** Free data sources are prone to errors, missing days, incorrect dividend adjustments, and lack of point-in-time accuracy (they overwrite historical data if an error is found later, introducing subtle look-ahead bias). Professional quants use CRSP, Compustat, or Bloomberg.

## 7. Parameter Sensitivity
*   **Limitation:** The backtest uses fixed parameters (252-day lookback, monthly rebalance, 5% static risk-free rate).
*   **Impact:** The results might be highly sensitive to these specific parameters (overfitting). A robust strategy should show stable performance across 60-day, 120-day, or 252-day lookbacks. Using a static 5% risk-free rate for 2019-2024 is technically inaccurate, as rates were near 0% in 2020-2021 and >5% in 2023.

## 8. Model Assumptions (Standard Finance Theory)
*   **Limitation:** Mean-Variance optimization assumes asset returns are normally distributed and Independent and Identically Distributed (i.i.d.).
*   **Impact:** Financial returns famously have "fat tails" (kurtosis) and volatility clustering. SLSQP optimization on historical variance underestimates the probability of extreme negative events (black swans).

## 9. Covariance Matrix Instability
*   **Limitation:** Using sample covariance from historical returns.
*   **Impact:** The sample covariance matrix contains a lot of estimation error/noise. Optimizers act as "error-maximizers," often overweighting assets with spuriously low estimated variance. Advanced models require shrinkage estimators (Ledoit-Wolf) or risk factor models.

## 10. Single-Period Optimization
*   **Limitation:** The optimizer only looks one period ahead (the next month) without considering multi-period horizons.
*   **Impact:** This can lead to myopic rebalancing, causing unnecessary turnover compared to multi-period stochastic control models.

## 11. No Tax Considerations or Liquidity Constraints
*   **Limitation:** The backtest operates in a tax-free vacuum with infinite liquidity.
*   **Impact:** Real portfolio management must account for short-term vs long-term capital gains taxes and the actual daily trading volume limits of the chosen assets.
