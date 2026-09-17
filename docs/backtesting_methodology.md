# Backtesting Methodology

## 1. What is Backtesting?
Backtesting is the process of testing a trading strategy or analytical model using historical data to evaluate how it would have performed. In quantitative finance, it is critical for validating mathematical models before risking real capital. A rigorous backtest must simulate reality as closely as possible, including trading costs, market friction, and strict chronological data boundaries.

## 2. Historical Simulation Methodology
Our backtester uses a daily step-forward historical simulation.
1.  **Initialize:** Start with an initial capital base (e.g., $1,000,000) and an initial allocation (e.g., 100% cash).
2.  **Iterate:** Step through every trading day in the backtest period.
3.  **Calculate Return:** For days between rebalance dates, the portfolio's daily return is the weighted average of the constituent stocks' simple returns.
4.  **Rebalance Trigger:** On the last trading day of the month, trigger the rebalancing module.
5.  **Estimate:** Calculate the covariance matrix using only data from the trailing window (e.g., 252 days) ending on the rebalance day.
6.  **Optimize:** Pass the covariance matrix to the strategy optimizer (Min Vol, Risk Parity) to generate new target weights.
7.  **Trade:** Calculate the difference between current drifted weights and target weights.
8.  **Apply Costs:** Subtract transaction costs (10 bps of traded volume) from the portfolio capital.
9.  **Record:** Log daily portfolio value, weights, and turnover into the database.

## 3. Timeline Diagram

```text
Time -------->
|======= Estimation Window (252 days) =======|
                                             | <- Rebalance Day (Calculate weights)
                                             |
                                             |======= Holding Period (1 month) =======|
                                                                                      | <- Next Rebalance Day
```
*At the Rebalance Day, only data from the Estimation Window is visible to the algorithm. The holding period uses those weights to generate returns.*

## 4. Look-Ahead Bias
*   **Definition:** The use of information or data in a study or simulation that would not have been known or available during the period being analyzed.
*   **Common Mistakes:** Calculating standard deviation over the *entire* 5-year dataset and applying it to day 1; using closing prices of Day T to calculate trades executed at the open of Day T.
*   **How We Prevent It:** The covariance matrix at time $t$ is calculated strictly using returns from $t-252$ to $t$. The target weights generated on the close of month $M$ are applied to the returns of month $M+1$.

## 5. Survivorship Bias
*   **Definition:** The logical error of concentrating on the people or things that made it past some selection process and overlooking those that did not.
*   **Common Mistakes:** Testing a strategy on the "Current S&P 500" dating back 10 years, ignoring the companies that went bankrupt or were delisted during that time.
*   **How it Affects Us:** Our universe of 12 stocks (AAPL, MSFT, etc.) inherently contains survivorship bias because we selected them knowing they are successful large-cap companies today. This artificially inflates backtest returns. (See Limitations document).

## 6. Overfitting
*   **Definition:** Creating a model that corresponds too closely to a particular set of data, and may therefore fail to predict future observations reliably.
*   **How it Manifests:** Tweak the rebalance frequency, lookback window, and asset list until the Sharpe ratio is artificially high.
*   **Mitigation:** We use standard, academically accepted parameters (monthly rebalance, 252-day lookback) and do not "tune" them to maximize the output metric.

## 7. Data Leakage
*   **Definition:** When information from outside the training dataset is used to create the model.
*   **Prevention:** Strict separation of data pipelines. The optimization module receives a sliced DataFrame that structurally cannot contain future data.

## 8. Rebalancing Mechanics
*   **Dates:** Rebalancing occurs on the last trading day of the calendar month (using pandas `resample('M')` or business month-end `BME`).
*   **Costs:** Calculated based on gross turnover. If weight of AAPL goes from 10% to 15%, we "buy" 5% of our capital worth of AAPL, paying 10 bps on that 5%.

## 9. Transaction Cost Model
*   **Formula:** Cost = $\text{Total Portfolio Value} \times \sum_{i=1}^N |w_{target, i} - w_{current, i}| \times 0.001$
*   **Assumptions:** Fixed 10 bps per dollar traded. Assumes infinite liquidity.
*   **Limitations:** Real costs include spread, slippage, and market impact, which scale non-linearly with volume.

## 10. Benchmark Alignment
*   **Fair Comparison:** The S&P 500 (^GSPC) is tracked over the exact same date range. If the backtest starts on Jan 2nd, the benchmark return must start from Jan 2nd base 100.
*   **Total Return:** We use Adjusted Close for both stocks and the index to ensure dividends are reinvested for a fair comparison.

## 11. Slippage Assumptions
*   **Model:** This backtest assumes zero slippage (execution happens exactly at the closing price). For highly liquid US large-caps, slippage is minimal, but this is a limitation.

## 12. Key Limitations
*   No market impact (our trades don't move the price).
*   No tax accounting.
*   Static risk-free rate assumption (using a flat 5% instead of a dynamic Treasury yield curve).

## 13. Backtest Validation Checklist
- [x] Returns match expected standard ranges (CAGR ~8-15%, Vol ~15-25%).
- [x] Initial portfolio value matches end value if returns are exactly 0.
- [x] Equal weight portfolio weights never drift more than 1 month before resetting.
- [x] Weights sum strictly to 1.0 at every time step.
- [x] Cash and asset values are conserved during rebalance deductions.
