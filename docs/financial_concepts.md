# Financial Concepts Glossary

**1. Simple Returns**
*   **Definition:** The percentage change in the price of an asset from one period to the next.
*   **Formula:** $R = (P_t - P_{t-1}) / P_{t-1}$
*   **Intuition:** It represents the actual cash return you would experience in your bank account.
*   **Example:** Stock goes from $100 to $110. Return is 10%.
*   **Usage:** Used to compute the daily portfolio value and equity curve.

**2. Log Returns**
*   **Definition:** The natural logarithm of the ratio of successive prices.
*   **Formula:** $r = \ln(P_t / P_{t-1})$
*   **Intuition:** Useful for statistical modeling because they are time-additive and symmetrically distributed.
*   **Example:** Stock goes $100 -> $110. Log return is ln(1.10) ≈ 9.53%.
*   **Usage:** Used to calculate covariance matrices and historical volatility for the optimizers.

**3. Variance**
*   **Definition:** A statistical measurement of the spread between numbers in a data set.
*   **Formula:** $\sigma^2 = \sum (x_i - \mu)^2 / N$
*   **Intuition:** It shows how far the asset's returns deviate from its average return. Higher variance = higher uncertainty.
*   **Example:** A tech stock has higher return variance than a utility stock.
*   **Usage:** The foundation of risk measurement in the optimization algorithms.

**4. Volatility**
*   **Definition:** The standard deviation of returns, usually annualized.
*   **Formula:** $\sigma = \sqrt{\text{Variance}} \times \sqrt{252}$
*   **Intuition:** The standard measure of market risk. It's variance put back into the original units (percentages).
*   **Example:** "The stock has a 20% annualized volatility."
*   **Usage:** Reported in the final risk metrics dashboard.

**5. Covariance**
*   **Definition:** A measure of the directional relationship between the returns of two assets.
*   **Formula:** $Cov(X,Y) = \frac{\sum (X - \mu_X)(Y - \mu_Y)}{n}$
*   **Intuition:** If two stocks move up together, they have positive covariance. If they move opposite, negative.
*   **Example:** AAPL and MSFT generally have positive covariance.
*   **Usage:** The core input to the Minimum Variance and Risk Parity optimizers.

**6. Correlation**
*   **Definition:** A normalized version of covariance, bounded between -1 and 1.
*   **Formula:** $\rho_{X,Y} = \frac{Cov(X,Y)}{\sigma_X \sigma_Y}$
*   **Intuition:** Tells you the strength and direction of a relationship, independent of volatility magnitude.
*   **Example:** A correlation of 1.0 means perfect unison; 0 means no relationship.
*   **Usage:** Used to understand diversification benefits.

**7. Diversification**
*   **Definition:** A risk management strategy that mixes a wide variety of investments within a portfolio.
*   **Formula:** N/A (Concept)
*   **Intuition:** "Don't put all your eggs in one basket." Combining uncorrelated assets reduces total risk.
*   **Example:** Holding tech stocks and utility stocks together.
*   **Usage:** The underlying reason we build multi-asset portfolios instead of holding a single stock.

**8. Portfolio Variance (Quadratic Form)**
*   **Definition:** The overall variance of a portfolio, accounting for weights and covariances.
*   **Formula:** $\sigma_p^2 = w^T \Sigma w$
*   **Intuition:** The risk of a portfolio is not just the sum of individual risks, but depends heavily on how the assets interact (covary).
*   **Example:** Two highly volatile stocks with negative correlation can create a low-variance portfolio.
*   **Usage:** The objective function minimized in the Minimum Variance strategy.

**9. Sharpe Ratio**
*   **Definition:** The average return earned in excess of the risk-free rate per unit of volatility.
*   **Formula:** $S = (R_p - R_f) / \sigma_p$
*   **Intuition:** Measures "bang for your buck" — how much return you get for the risk you took.
*   **Example:** A Sharpe of 1.5 is excellent; 0.5 is mediocre.
*   **Usage:** The primary metric to compare our 3 strategies.

**10. Sortino Ratio**
*   **Definition:** A variation of the Sharpe ratio that differentiates harmful volatility from total volatility by using the asset's standard deviation of negative portfolio returns.
*   **Formula:** $Sortino = (R_p - R_f) / \sigma_{downside}$
*   **Intuition:** Investors don't mind upside volatility (large gains); they only hate downside volatility. Sortino captures this.
*   **Example:** A strategy with big positive jumps will have a better Sortino than Sharpe.
*   **Usage:** Calculated as an alternative risk-adjusted return metric.

**11. Beta**
*   **Definition:** A measure of the volatility, or systematic risk, of a security or a portfolio in comparison to the market as a whole.
*   **Formula:** $\beta = Cov(R_p, R_m) / Var(R_m)$
*   **Intuition:** A Beta of 1.2 means the portfolio is 20% more volatile than the market.
*   **Example:** The S&P 500 has a beta of 1.0. Our Min Variance portfolio likely has a beta < 1.
*   **Usage:** Evaluates how much of our strategy's return is just driven by the broader market.

**12. Maximum Drawdown (MDD)**
*   **Definition:** The maximum observed loss from a peak to a trough of a portfolio, before a new peak is attained.
*   **Formula:** $MDD = (Trough Value - Peak Value) / Peak Value$
*   **Intuition:** The "worst-case scenario" pain an investor would have felt historically.
*   **Example:** In 2008, the S&P 500 had an MDD of roughly -50%.
*   **Usage:** Crucial for understanding tail risk and investor psychology.

**13. CAGR (Compound Annual Growth Rate)**
*   **Definition:** The mean annual growth rate of an investment over a specified period of time longer than one year.
*   **Formula:** $CAGR = (EV/BV)^{1/n} - 1$
*   **Intuition:** The smoothed annualized return if the portfolio grew at a steady rate.
*   **Example:** A portfolio grows from 100 to 121 in 2 years. CAGR is 10%.
*   **Usage:** Standardizes absolute return over the multi-year backtest.

**14. Risk Parity**
*   **Definition:** A portfolio allocation strategy that focuses on allocation of risk, usually defined as volatility, rather than allocation of capital.
*   **Formula:** Seeks $w_i$ such that $TRC_i = TRC_j$ for all $i,j$.
*   **Intuition:** If equities are 5x riskier than bonds, risk parity holds far more bonds than equities so their risk impacts are equal.
*   **Example:** Ray Dalio's All Weather Portfolio.
*   **Usage:** One of the core strategies tested in this project.

**15. Minimum Variance Portfolio**
*   **Definition:** A portfolio of individually risky assets that, when taken together, result in the lowest possible overall risk level for the rate of expected return.
*   **Formula:** $\min w^T \Sigma w$
*   **Intuition:** The mathematical formulation of finding the safest possible combination of stocks.
*   **Example:** Heavy weighting in low-volatility, low-correlation assets like JNJ or PG.
*   **Usage:** One of the core strategies tested in this project.

**16. Efficient Frontier**
*   **Definition:** The set of optimal portfolios that offer the highest expected return for a defined level of risk.
*   **Formula:** Maximize return for given risk, or minimize risk for given return.
*   **Intuition:** You cannot move above the line. Any portfolio below the line is sub-optimal.
*   **Example:** A curve plotted on a graph of Volatility (x-axis) vs Return (y-axis).
*   **Usage:** Our Minimum Variance portfolio represents the far-left point on this curve.

**17. Benchmark**
*   **Definition:** A standard against which the performance of a security, mutual fund or investment manager can be measured.
*   **Formula:** N/A (Concept)
*   **Intuition:** It answers "Compared to what?" If you made 10% but the market made 20%, you did poorly.
*   **Example:** S&P 500.
*   **Usage:** Used to calculate active return and relative metrics.

**18. Rebalancing**
*   **Definition:** The process of realigning the weightings of a portfolio of assets.
*   **Formula:** $Trade_i = w_{target, i} - w_{current, i}$
*   **Intuition:** As prices move, a 50/50 portfolio drifts to 60/40. Rebalancing forces you to "buy low, sell high" to reset to 50/50.
*   **Example:** Selling tech stocks that rallied and buying consumer staples that fell.
*   **Usage:** Simulated monthly in our backtester.

**19. Transaction Costs**
*   **Definition:** Expenses incurred when buying or selling a good or service.
*   **Formula:** Cost = Trading Volume * bps
*   **Intuition:** Trading isn't free. High turnover destroys returns.
*   **Example:** Paying a broker 0.1% (10 bps) per trade.
*   **Usage:** Deducted from portfolio value at each rebalancing to make the backtest realistic.

**20. Risk Contribution**
*   **Definition:** The amount of the portfolio's total volatility that can be attributed to a specific asset.
*   **Formula:** $TRC_i = w_i \times \frac{(\Sigma w)_i}{\sqrt{w^T \Sigma w}}$
*   **Intuition:** A stock might be 10% of the capital, but if it's highly volatile, it might be 30% of the portfolio's risk.
*   **Example:** TSLA in a portfolio of utilities will dominate the risk contribution.
*   **Usage:** The target metric equalized in the Risk Parity optimizer.
