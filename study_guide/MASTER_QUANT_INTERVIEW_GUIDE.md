# Master Quantitative Portfolio Research & Tech Stack Interview Guide
================================================================================
> **Target Audience:** Quantitative Analyst, Quantitative Researcher, Quant Developer, Data Analyst, Portfolio Risk Analyst.
> **Scope:** 70+ In-Depth Questions & Answers covering Financial Metrics, Portfolio Theory, Backtesting Mechanics, Data Engineering, Python/NumPy, DuckDB/SQL, and Power BI BI Architecture.

---

# Table of Contents
1. [Module 1: Deep Dive into Financial Metrics & Math (Q1 - Q15)](#module-1-deep-dive-into-financial-metrics--math)
2. [Module 2: Portfolio Optimization & Mathematical Solvers (Q16 - Q27)](#module-2-portfolio-optimization--mathematical-solvers)
3. [Module 3: Backtesting Realities, Biases & Execution Pitfalls (Q28 - Q37)](#module-3-backtesting-realities-biases--execution-pitfalls)
4. [Module 4: Market Data Pipeline & Time Series Integrity (Q38 - Q45)](#module-4-market-data-pipeline--time-series-integrity)
5. [Module 5: Python, NumPy & High-Performance Vectorization (Q46 - Q53)](#module-5-python-numpy--high-performance-vectorization)
6. [Module 6: DuckDB, Analytical SQL & Storage Internals (Q54 - Q61)](#module-6-duckdb-analytical-sql--storage-internals)
7. [Module 7: Power BI, DAX & Data Modeling Architecture (Q62 - Q67)](#module-7-power-bi-dax--data-modeling-architecture)
8. [Module 8: Scalability, Production Architecture & Edge Cases (Q68 - Q74)](#module-8-scalability-production-architecture--edge-cases)

---

# Module 1: Deep Dive into Financial Metrics & Math

### Q1: What is the Sharpe Ratio, what does it truly measure, and what are its hidden weaknesses?
* **How to Tackle:**
  1. **Definition & Formula:** $\text{Sharpe} = \frac{R_p - R_f}{\sigma_p}$. It measures excess return per unit of *total risk* (annualized volatility).
  2. **Intuition:** Tells you whether high returns came from smart asset allocation or simply taking reckless volatility.
  3. **Industry Weaknesses:**
     * **Penalizes Upside Volatility:** A stock that jumps $+15\%$ every month is penalized identically to a stock that drops $-15\%$.
     * **Assumes Normal (Gaussian) Distribution:** Financial returns have fat tails (leptokurtic) and skewness. Sharpe underestimates risk during tail crashes.
     * **Time Aggregation Drift:** Annualizing with $\sqrt{252}$ assumes returns are independent and identically distributed (i.i.d.), which ignores auto-correlation and volatility clustering.
  4. **The Fix:** Use Sortino Ratio for asymmetric downside or Omega Ratio for complete distribution evaluation.

---

### Q2: What is the Sortino Ratio and how is "Downside Deviation" mathematically derived?
* **How to Tackle:**
  1. **Formula:** $\text{Sortino} = \frac{R_p - R_f}{\sigma_d}$, where Downside Deviation is $\sigma_d = \sqrt{\frac{1}{N}\sum_{t=1}^N \min(0, R_t - \text{Target})^2}$.
  2. **Intuition:** It only counts volatility when returns fall below a specified threshold (e.g., $R_f$ or $0\%$). Upside rallies do not decrease the score.
  3. **Why our project has Sortino (1.32) > Sharpe (0.93):** Because large positive market days inflate total standard deviation $\sigma_p$ (lowering Sharpe), but are completely ignored by downside deviation $\sigma_d$.

---

### Q3: What is Maximum Drawdown (MDD) and how is the algorithm implemented in Python?
* **How to Tackle:**
  1. **Definition:** The maximum peak-to-trough percentage drop in portfolio equity before a new peak is achieved.
  2. **Algorithm:**
     $$\text{Peak}_t = \max_{s \le t}(\text{Equity}_s), \quad \text{Drawdown}_t = \frac{\text{Equity}_t - \text{Peak}_t}{\text{Peak}_t}$$
     $$\text{MDD} = \min_{t}(\text{Drawdown}_t)$$
  3. **Vectorized Implementation in Pandas:**
     ```python
     rolling_peak = equity_series.cummax()
     drawdown = (equity_series - rolling_peak) / rolling_peak
     max_dd = drawdown.min()
     ```
  4. **Why it matters:** Behavioral finance dictates that fund investors redeem capital during drawdowns. If a fund's MDD exceeds 25-30%, clients withdraw money, causing fund closure regardless of long-term average return.

---

### Q4: What is the Calmar Ratio and when is it preferred over the Sharpe Ratio?
* **How to Tackle:**
  1. **Formula:** $\text{Calmar Ratio} = \frac{\text{CAGR}}{|\text{Max Drawdown}|}$.
  2. **Intuition:** Compares the compound annual growth rate directly to the worst-case historical loss.
  3. **Use Case:** Extensively used by Commodity Trading Advisors (CTAs) and Hedge Funds. An investor looking at a 5-year lockup period cares more about the worst single loss they could suffer than day-to-day Gaussian fluctuations.
  4. **Benchmark:** A Calmar $> 0.5$ is acceptable, $> 1.0$ is good, $> 2.0$ is exceptional.

---

### Q5: What is CAGR and why is it superior to the Arithmetic Mean Annual Return?
* **How to Tackle:**
  1. **Formula:** $\text{CAGR} = \left(\frac{V_{\text{end}}}{V_{\text{start}}}\right)^{\frac{252}{N_{\text{trading\_days}}}} - 1$.
  2. **The Arithmetic Fallacy:** If an asset starts at $\$100$, drops $-50\%$ to $\$50$ in Year 1, and rises $+50\%$ to $\$75$ in Year 2:
     * Arithmetic Mean Return $= \frac{-50\% + 50\%}{2} = 0\%$.
     * Actual Wealth Change $= -\$25$ (a $-25\%$ total loss!).
     * True CAGR $= \sqrt{75/100} - 1 = -13.4\%$.
  3. **Rule:** Arithmetic return overstates multi-period compounded growth. CAGR correctly reflects real geometric compounding.

---

### Q6: What is Beta ($\beta$) and how is it derived via Ordinary Least Squares (OLS)?
* **How to Tackle:**
  1. **Definition:** A measure of a portfolio's systematic risk (sensitivity) relative to the market benchmark ($S\&P\ 500$).
  2. **Mathematical Formulation:**
     $$\beta = \frac{\text{Cov}(R_p, R_m)}{\text{Var}(R_m)}$$
  3. **Interpretation:**
     * $\beta = 1.0$: Portfolio moves identically in tandem with the market.
     * $\beta < 1.0$ (e.g. Minimum Variance $= 0.71$): Defensive portfolio; drops less during crashes but lags during strong bull runs.
     * $\beta > 1.0$: Aggressive, leveraged, or high-beta cyclical portfolio.

---

### Q7: What is Tracking Error and what does a Tracking Error of 5.8% mean?
* **How to Tackle:**
  1. **Formula:** $\text{TE} = \text{StdDev}(R_p - R_m) \times \sqrt{252}$.
  2. **Intuition:** Measures the consistency with which a portfolio follows or deviates from its benchmark index.
  3. **Interpretation:** 
     * An index ETF tracking the S&P 500 should have a TE $< 0.1\%$.
     * In our project, Equal Weight has a TE of $5.81\%$, meaning it actively deviates from the market-cap-weighted S&P 500 to capture the small/equal-weight size premium.

---

### Q8: What is the Information Ratio (IR) and how does it relate to Alpha and Tracking Error?
* **How to Tackle:**
  1. **Formula:** $\text{IR} = \frac{R_p - R_m}{\text{Tracking Error}} = \frac{\alpha}{\text{TE}}$.
  2. **Intuition:** The "Sharpe Ratio of Active Management". It measures how much excess return (alpha) a portfolio manager generated for each unit of risk taken relative to the benchmark.
  3. **Hedge Fund Rule of Thumb:** IR $> 0.5$ is considered good, $> 1.0$ is exceptional.

---

### Q9: What is the Treynor Ratio and how does it differ from the Sharpe Ratio?
* **How to Tackle:**
  1. **Formula:** $\text{Treynor Ratio} = \frac{R_p - R_f}{\beta_p}$.
  2. **Difference:** Sharpe uses **total risk** ($\sigma_p$, systematic + unsystematic), whereas Treynor uses **systematic risk** ($\beta_p$).
  3. **When to use Treynor:** When evaluating a sub-portfolio that is part of a larger, well-diversified fund where idiosyncratic risk has already been diversified away.

---

### Q10: What is Value at Risk (VaR) and what is the difference between Parametric, Historical, and Monte Carlo VaR?
* **How to Tackle:**
  1. **Definition:** The maximum expected loss over a specific time horizon $T$ at a given confidence level $1-\alpha$ (e.g., $95\%$ 1-day VaR of $\$10,000$ means there is only a $5\%$ chance of losing more than $\$10,000$ tomorrow).
  2. **The 3 Methods:**
     * **Parametric (Variance-Covariance):** $\text{VaR} = -(\mu - Z_{\alpha}\sigma)$. Assumes normal distribution. Ultra-fast, but ignores fat tails.
     * **Historical Simulation:** Takes the 5th percentile of historical actual daily returns. Non-parametric, captures empirical fat tails, but assumes the future mirrors past regimes.
     * **Monte Carlo:** Simulates 10,000+ stochastic price paths using Geometric Brownian Motion or GARCH. Flexible, handles nonlinear derivatives, but computationally heavy.

---

### Q11: What is Conditional Value at Risk (CVaR / Expected Shortfall) and why is it Coherent while VaR is not?
* **How to Tackle:**
  1. **Definition:** $\text{CVaR}_{\alpha} = \mathbb{E}[L \mid L > \text{VaR}_{\alpha}]$. The expected average loss *given* that the loss has exceeded the VaR cutoff threshold.
  2. **Coherence Property (Subadditivity):** For a risk measure $\rho$ to be coherent, $\rho(A + B) \le \rho(A) + \rho(B)$ (combining portfolios must reduce or equal risk).
  3. **Why VaR fails:** In non-normal or skewed distributions, VaR can violate subadditivity (a diversified portfolio can show a higher VaR than individual assets). CVaR is strictly subadditive and convex, making it mathematically superior for portfolio optimization.

---

### Q12: Why do log returns compound across time while simple returns compound across assets?
* **How to Tackle:**
  1. **Time Additivity:** $P_t = P_0 \cdot \frac{P_1}{P_0} \cdot \frac{P_2}{P_1} \dots \frac{P_t}{P_{t-1}}$. Taking the natural log gives:
     $$\ln\left(\frac{P_t}{P_0}\right) = \sum_{k=1}^t r_k^{\text{log}}$$
  2. **Cross-Sectional Additivity:** The portfolio dollar value at time $t$ is $V_t = \sum w_i P_{i,t}$. The portfolio simple return is:
     $$R_p = \sum_{i=1}^N w_i R_i$$
     This linear combination does **not** hold for log returns: $\ln(1 + \sum w_i R_i) \neq \sum w_i \ln(1 + R_i)$.
  3. **Engineering Standard:** Use log returns for time-series modeling (covariance estimation, GARCH) and simple returns for accounting and equity curves.

---

### Q13: What is the difference between Idiosyncratic Risk and Systematic Risk?
* **How to Tackle:**
  1. **Systematic Risk (Market Risk):** Unavoidable macro risk affecting all assets (interest rate hikes, inflation, wars, recessions). Measured by Beta ($\beta$). Cannot be diversified away.
  2. **Idiosyncratic Risk (Specific Risk):** Firm-specific risk (CEO fraud, product recall, FDA rejection).
  3. **Markowitz Proof:** As portfolio size $N \to \infty$, the total portfolio variance approaches the average covariance $\bar{\sigma}_{ij}$. Idiosyncratic variance $\frac{1}{N}\bar{\sigma}_i^2 \to 0$.

---

### Q14: What is the "1/N Puzzle" in academic quantitative finance?
* **How to Tackle:**
  1. **The DeMiguel, Garlappi, and Uppal (2009) Study:** Tested 14 optimization models across 7 empirical datasets. Found that naive $1/N$ (Equal Weight) consistently matched or beat complex mean-variance optimizers out-of-sample.
  2. **Why:** Optimizers suffer from **estimation error maximization** (they place massive bets on assets whose historical returns or low variances were statistical anomalies).
  3. **Our Backtest Finding:** Equal Weight produced a $256\%$ total return vs Minimum Variance's $127\%$, perfectly proving this empirical quantitative phenomenon.

---

### Q15: What is Jensen's Alpha ($\alpha$) and how is it computed from CAPM?
* **How to Tackle:**
  1. **CAPM Expected Return:** $\mathbb{E}[R_p] = R_f + \beta_p (\mathbb{E}[R_m] - R_f)$.
  2. **Jensen's Alpha:** $\alpha = R_p - [R_f + \beta_p (R_m - R_f)]$.
  3. **Meaning:** The excess return generated by the portfolio above what is expected given its exposure to systematic market risk ($\beta$). An $\alpha > 0$ indicates true managerial value-add.

---

# Module 2: Portfolio Optimization & Mathematical Solvers

### Q16: Walk through the mathematical formulation of Markowitz Minimum Variance.
* **How to Tackle:**
  1. **Objective Function:** Minimize quadratic portfolio variance:
     $$\min_{\mathbf{w}} \frac{1}{2} \mathbf{w}^T \mathbf{\Sigma} \mathbf{w}$$
  2. **Subject to Constraints:**
     $$\sum_{i=1}^N w_i = 1 \quad (\text{Fully invested})$$
     $$0 \le w_i \le 1 \quad \forall i \in \{1, \dots, N\} \quad (\text{Long-only / No short selling})$$
  3. **Analytical Solution (Unconstrained):** $\mathbf{w}^* = \frac{\mathbf{\Sigma}^{-1}\mathbf{1}}{\mathbf{1}^T \mathbf{\Sigma}^{-1}\mathbf{1}}$.
  4. **Constrained Solution:** Solved using Sequential Least Squares Programming (SLSQP) or Interior Point algorithms.

---

### Q17: What is Risk Parity (Equal Risk Contribution) and why does it not require expected return forecasts?
* **How to Tackle:**
  1. **The Flaw of Mean-Variance:** Mean-variance optimization requires expected return forecasts ($\boldsymbol{\mu}$), which are notoriously noisy and error-prone (forecasting returns is $10\times$ harder than forecasting volatility).
  2. **Risk Parity Premise:** Ignore return forecasts entirely. Allocate weights such that every single asset contributes the exact same dollar amount of volatility to the portfolio:
     $$\text{RC}_i = w_i \frac{(\mathbf{\Sigma}\mathbf{w})_i}{\sigma_p} = \frac{\sigma_p}{N} \quad \forall i$$
  3. **Result:** Produces all-weather portfolios that perform well across inflation, deflation, growth, and recession regimes (the basis of Bridgewater's All Weather Fund).

---

### Q18: How do you prove Euler's Decomposition of Portfolio Risk?
* **How to Tackle:**
  1. **Portfolio Volatility:** $\sigma_p(\mathbf{w}) = \sqrt{\mathbf{w}^T \mathbf{\Sigma} \mathbf{w}}$ is a mathematically homogeneous function of degree 1 (i.e., $\sigma_p(c\mathbf{w}) = c\sigma_p(\mathbf{w})$).
  2. **Euler's Theorem:** For any homogeneous function of degree 1:
     $$\sigma_p(\mathbf{w}) = \sum_{i=1}^N w_i \frac{\partial \sigma_p}{\partial w_i}$$
  3. **Marginal Risk Contribution:** $\frac{\partial \sigma_p}{\partial w_i} = \frac{(\mathbf{\Sigma}\mathbf{w})_i}{\sigma_p}$.
  4. **Total Risk Contribution:** $\text{RC}_i = w_i \frac{(\mathbf{\Sigma}\mathbf{w})_i}{\sigma_p}$. Summing all $\text{RC}_i$ equals exactly $\sigma_p$.

---

### Q19: What is the SLSQP algorithm and how does it solve constrained optimization?
* **How to Tackle:**
  1. **SLSQP:** Sequential Least Squares Programming (developed by Dieter Kraft in 1988).
  2. **Mechanism:** At each iteration, it approximates the nonlinear objective function with a quadratic Taylor expansion and linearizes the constraints, solving a Quadratic Programming (QP) sub-problem.
  3. **Hessian Updates:** Uses the BFGS (Broyden–Fletcher–Goldfarb–Shanno) quasi-Newton formula to approximate the Hessian matrix of the Lagrangian without computing expensive second derivatives analytically.

---

### Q20: What is a Positive Semi-Definite (PSD) matrix and why must a Covariance Matrix be PSD?
* **How to Tackle:**
  1. **Definition:** A symmetric matrix $\mathbf{\Sigma}$ is PSD if and only if for all non-zero vectors $\mathbf{w}$, $\mathbf{w}^T \mathbf{\Sigma} \mathbf{w} \ge 0$.
  2. **Financial Meaning:** $\mathbf{w}^T \mathbf{\Sigma} \mathbf{w}$ represents portfolio variance. Variance is squared standard deviation, which physically cannot be negative ($\sigma_p^2 \ge 0$).
  3. **Check:** All eigenvalues $\lambda_i \ge 0$. If an estimated matrix has negative eigenvalues (due to missing data or non-synchronous trading), optimizers fail.

---

### Q21: What is Matrix Ill-Conditioning and what is the Condition Number?
* **How to Tackle:**
  1. **Condition Number:** $\kappa(\mathbf{\Sigma}) = \frac{\lambda_{\max}}{\lambda_{\min}}$ (ratio of largest to smallest eigenvalue).
  2. **The Problem:** If two assets are nearly collinear (correlation $\approx 0.999$), $\lambda_{\min} \to 0$ and $\kappa \to \infty$. Inverting $\mathbf{\Sigma}$ amplifies machine floating-point rounding errors by a factor of $\kappa$, causing wild, unstable portfolio weight swings.
  3. **Our Code Solution:** We applied Tikhonov regularization (shrinkage towards identity): $\mathbf{\Sigma}_{\text{reg}} = \mathbf{\Sigma} + \epsilon \mathbf{I}$ with $\epsilon = 10^{-8}$.

---

### Q22: What is Ledoit-Wolf Covariance Shrinkage and when should you use it?
* **How to Tackle:**
  1. **The Formula:** $\mathbf{\Sigma}_{\text{shrunk}} = \delta \mathbf{F} + (1 - \delta) \mathbf{S}$, where $\mathbf{S}$ is the sample covariance matrix, $\mathbf{F}$ is a structured target (e.g., identity or single-index model), and $\delta \in [0, 1]$ is the analytically optimal shrinkage intensity.
  2. **Why it works:** When $N$ (number of assets) is large relative to $T$ (sample days), sample covariance overfits noise. Shrinkage pulls extreme sample covariances back toward the mean, drastically improving out-of-sample portfolio stability.

---

### Q23: What is the Black-Litterman Model and what problem does it solve?
* **How to Tackle:**
  1. **Problem:** Standard Markowitz mean-variance generates highly concentrated, unintuitive weights sensitive to minor return forecast changes.
  2. **Solution:** Black-Litterman starts with the **Market Equilibrium Portfolio** (reverse-engineered from market-cap weights via CAPM: $\boldsymbol{\Pi} = \gamma \mathbf{\Sigma} \mathbf{w}_{\text{mkt}}$) as a Bayesian prior.
  3. **Views Integration:** It allows managers to express specific absolute or relative views with explicit confidence levels (e.g., "AAPL will beat MSFT by 2% with 80% confidence"), blending prior equilibrium with views using Gaussian Bayesian updating.

---

### Q24: What is the Efficient Frontier and how is it constructed?
* **How to Tackle:**
  1. **Definition:** The set of optimal portfolios in the Expected Return vs. Volatility plane that offer the highest expected return for a given level of risk, or the lowest risk for a given expected return.
  2. **Construction:** Solve a sequence of quadratic optimization problems parameterized by target returns $R_{\text{target}}$:
     $$\min_{\mathbf{w}} \mathbf{w}^T \mathbf{\Sigma} \mathbf{w} \quad \text{s.t.} \quad \mathbf{w}^T \boldsymbol{\mu} = R_{\text{target}}, \quad \sum w_i = 1, \quad w_i \ge 0$$
  3. **Visualized in Project:** In `notebooks/02_portfolio_analysis.ipynb`, we simulated 5,000 random portfolios to map the feasible set and plotted our exact Minimum Variance and Risk Parity coordinates on the envelope.

---

### Q25: What is the Tangency Portfolio (Maximum Sharpe Portfolio)?
* **How to Tackle:**
  1. **Definition:** The point on the Efficient Frontier where a straight line drawn from the risk-free rate $R_f$ on the y-axis (the Capital Allocation Line, CAL) is exactly tangent to the curve.
  2. **Mathematical Property:** It is the unique long-only portfolio that maximizes the Sharpe Ratio:
     $$\max_{\mathbf{w}} \frac{\mathbf{w}^T \boldsymbol{\mu} - R_f}{\sqrt{\mathbf{w}^T \mathbf{\Sigma} \mathbf{w}}}$$
  3. **Separation Theorem (Tobin's Separation):** Any investor can achieve their optimal risk profile by simply holding a combination of the Tangency Portfolio and the Risk-Free asset.

---

### Q26: What happens to Minimum Variance weights if all asset correlations are exactly zero?
* **How to Tackle:**
  1. **Diagonal Covariance Matrix:** $\mathbf{\Sigma} = \text{diag}(\sigma_1^2, \sigma_2^2, \dots, \sigma_N^2)$.
  2. **Analytical Weight Formula:**
     $$w_i^* = \frac{1/\sigma_i^2}{\sum_{j=1}^N 1/\sigma_j^2}$$
  3. **Intuition:** Each asset's weight is strictly proportional to its **inverse variance**. An asset with twice the standard deviation gets one-fourth the weight.

---

### Q27: How does Risk Parity allocate weights under zero correlation?
* **How to Tackle:**
  1. **Risk Contribution under 0 correlation:** $\text{RC}_i = w_i \sigma_i$.
  2. **Equalizing Risk Contributions:** $w_1 \sigma_1 = w_2 \sigma_2 = \dots = w_N \sigma_N = C$.
  3. **Analytical Weight Formula:**
     $$w_i^* = \frac{1/\sigma_i}{\sum_{j=1}^N 1/\sigma_j}$$
  4. **Key Difference from MinVar:** Risk Parity scales with **inverse volatility** ($1/\sigma$), whereas Minimum Variance scales with **inverse variance** ($1/\sigma^2$). This makes Risk Parity much less prone to over-concentration!

---

# Module 3: Backtesting Realities, Biases & Execution Pitfalls

### Q28: What is Look-Ahead Bias and how did you prevent it in your codebase?
* **How to Tackle:**
  1. **Definition:** Using information at time $T$ that would not have been known until $T + k$.
  2. **Classic Mistake:** Calculating mean returns and covariance across the full 2019–2024 dataset, and then using those static parameters to simulate trading starting in 2019.
  3. **Our Implementation:** In `src/backtest.py`, at rebalance index $T$, the historical data slice is strictly bounded: `log_returns.iloc[:T]`. Covariance is estimated *only* on past data. Future prices are strictly invisible.

---

### Q29: What is Survivorship Bias and how does it affect our 12-stock universe?
* **How to Tackle:**
  1. **Definition:** Selecting assets based on their success at the end of the sample period, while ignoring assets that went bankrupt, merged, or were delisted during the period.
  2. **Our Project's Limitation:** We selected 12 mega-cap winners (e.g. AAPL, LLY, MSFT) that survived and thrived through 2024. Companies like Silicon Valley Bank or Bed Bath & Beyond that failed during this window were not included.
  3. **Institutional Fix:** Use a **Point-in-Time** universe (e.g., select the top 500 stocks as of January 1, 2019, including those that later delisted, using databases like CRSP or Compustat).

---

### Q30: What is Data Snooping (p-hacking / Overfitting) in Quant Research?
* **How to Tackle:**
  1. **Definition:** Testing hundreds of parameter combinations (e.g., trying 5-day, 10-day, 21-day, 60-day rebalances, 50 different indicators) and only reporting the one combination that happened to perform well by pure random chance on historical noise.
  2. **The Problem:** The strategy fails immediately in live forward trading.
  3. **Prevention:** Out-of-Sample (OOS) validation, Walk-Forward Analysis, K-Fold cross-validation with Purging & Embargoing (Marcos López de Prado), and White's Reality Check / Deflated Sharpe Ratio.

---

### Q31: How did you model Transaction Costs and what is Turnover?
* **How to Tackle:**
  1. **Turnover Formula at Rebalance Date $t$:**
     $$\text{Turnover}_t = \sum_{i=1}^N |w_{i, t} - w_{i, t^-}|$$
     where $w_{i, t^-}$ is the drifted weight immediately before rebalancing.
  2. **Cost Calculation:** $\text{Cost}_t = \text{Turnover}_t \times \text{Transaction Cost Rate} \times V_t$.
  3. **Our Model:** Applied 10 basis points ($0.10\%$) friction on every trade. Over 68 rebalances, Minimum Variance paid $\$7,139$ in costs due to dynamic shifts, whereas Equal Weight paid minimal friction.

---

### Q32: What is Slippage and Market Impact, and how do institutional models represent them?
* **How to Tackle:**
  1. **Slippage:** The difference between the decision price (signal generation) and the execution price (order fill), caused by execution latency.
  2. **Market Impact:** The price movement caused by your own order hitting the order book (pushing ask prices higher when buying).
  3. **Almgren-Chriss Square-Root Impact Model:**
     $$\Delta P \propto \sigma \sqrt{\frac{V_{\text{order}}}{\text{ADV}}}$$
     where $\text{ADV}$ is the Average Daily Volume and $\sigma$ is daily volatility. Large orders incur non-linear square-root price penalty.

---

### Q33: What is "Weight Drift" between rebalancing dates?
* **How to Tackle:**
  1. **Mechanism:** If you buy Equal Weight ($8.33\%$ each) on Day 1, and Asset A doubles while Asset B drops by half, by Day 20 Asset A represents $15\%$ of the portfolio and Asset B represents $4\%$.
  2. **Accounting:** Portfolio value evolves daily based on individual stock price multiples:
     $$V_t = V_{t-1} \sum_{i=1}^N w_{i, t-1} (1 + R_{i, t})$$
  3. **Rebalancing Role:** Monthly rebalancing restores weights back to the model target, acting as a disciplined systematic "buy-low, sell-high" rebalancing engine.

---

### Q34: What is the tradeoff between Monthly, Weekly, and Daily Rebalancing?
* **How to Tackle:**
  1. **Daily Rebalancing:** Keeps weights perfectly aligned with the theoretical model, but incurs severe transaction cost drag and bid-ask spread erosion.
  2. **Monthly Rebalancing:** Optimal middle ground for equity portfolios. Captures intermediate momentum and allows rebalancing premium while keeping annual transaction costs below $0.15\%$.
  3. **Annual Rebalancing:** Lowest cost, but allows massive weight drift, increasing portfolio risk beyond model parameters.

---

### Q35: What is "Cash Drag" in portfolio backtesting?
* **How to Tackle:**
  1. **Definition:** The performance penalty caused by holding uninvested cash in a rising market.
  2. **Our Model:** Assumes $100\%$ full investment ($\sum w_i = 1$).
  3. **Real-world Hedge Fund Reality:** Portfolios maintain $1-5\%$ cash buffers for margin requirements and redemptions. In a bull market, this uninvested cash reduces CAGR; in a bear market, cash acts as a stabilizer.

---

### Q36: What is Walk-Forward Optimization (WFO)?
* **How to Tackle:**
  1. **Mechanism:** Uses a rolling in-sample window (e.g., 252 days) to estimate parameters and optimize weights, applies those weights out-of-sample for the next period (e.g., 21 days), and then rolls the window forward.
  2. **Why it mimics reality:** Exactly simulates how a quantitative portfolio manager operates in real life — recalibrating models periodically using recent market regimes without peeking into the future.

---

### Q37: How do you handle non-synchronous trading and holiday calendar alignment?
* **How to Tackle:**
  1. **The Issue:** Different exchanges have different holidays (e.g., US NYSE vs UK LSE vs Japan TSE). Merging time series creates artificial missing values.
  2. **Our Solution:** Standardized on the US NYSE trading calendar ($S\&P\ 500$ benchmark dates). Any stock with a missing holiday tick was validated and forward-filled using previous close to prevent artificial price jumps.

---

# Module 4: Market Data Pipeline & Time Series Integrity

### Q38: What is the difference between "Close" and "Adjusted Close" prices?
* **How to Tackle:**
  1. **Raw Close:** The actual traded price at the $4:00\text{ PM}$ market closing bell.
  2. **Adjusted Close:** Backwards-adjusted for **stock splits**, **reverse splits**, and **cash dividends**.
  3. **Why Adjusted Close is mandatory:** If Apple executes a 4-for-1 stock split, the raw price drops from $\$400$ to $\$100$. Using raw Close calculates an artificial $-75\%$ single-day return crash! Adjusted Close scales past prices by $0.25$, preserving the true $0\%$ economic return.

---

### Q39: What are the 5 stages of your data cleaning pipeline in `src/data_cleaning.py`?
* **How to Tackle:**
  1. **Stage 1: Missing Value Validation:** Check for `NaN`/`Null` records.
  2. **Stage 2: Non-Positive Price Detection:** Ensure all prices $> 0$ (negative prices are corrupted data).
  3. **Stage 3: Duplicate Date Elimination:** Ensure strict single pricing record per ticker per date.
  4. **Stage 4: Chronological Ordering:** Enforce monotonic ascending date sort.
  5. **Stage 5: Date Gap Audit:** Flag abnormal gaps ($> 4$ calendar days) to ensure market data continuity.

---

### Q40: Why should you never use Linear Interpolation for backtesting missing prices?
* **How to Tackle:**
  1. **Look-Ahead Leakage:** Linear interpolation calculates $P_t = \frac{P_{t-1} + P_{t+1}}{2}$. This uses the future price $P_{t+1}$ to fill day $t$!
  2. **The Correct Fix:** **Forward Fill (`ffill`)**: Carries forward the last known traded price $P_{t-1}$, exactly matching what a trader would know in real-time.

---

### Q41: How did you implement disk caching to prevent API rate-limiting in `src/data_loader.py`?
* **How to Tackle:**
  1. **Mechanism:** Checks if `data/raw/prices_raw.csv` exists locally.
  2. **Condition:** If cached file exists and `force_download=False`, it reads from disk instantly in $< 5\text{ ms}$.
  3. **Benefit:** Enables instant offline reproduction, shields against Yahoo Finance API rate limits, and prevents test suite timeouts.

---

### Q42: What is Dividend Reinvestment Assumption (DRIP) in Adjusted Close?
* **How to Tackle:**
  1. **Mechanism:** When a company pays a dividend of $\$2.00$ on a $\$100$ stock, the stock price drops to $\$98$ ex-dividend.
  2. **Adjusted Close Adjustment:** Multiplies all historical prices prior to the dividend by $\frac{98}{100} = 0.98$.
  3. **Economic Meaning:** Simulates a total return index where all cash dividends are immediately reinvested tax-free into the underlying stock.

---

### Q43: How do you detect and handle stock split anomalies in raw market feeds?
* **How to Tackle:**
  1. **Detection:** Scan for overnight return spikes $|R_t| > 30\%$ where volume surges by $2\times - 10\times$.
  2. **Verification:** Cross-reference corporate action feeds (SEC Form 8-K filings or stock split tables).
  3. **Adjustment:** Divide historical price series by the split ratio $S$ and multiply historical volume by $S$.

---

### Q44: What is Stationarity and why must return series be stationary for modeling?
* **How to Tackle:**
  1. **Definition:** A time series whose statistical properties (mean, variance, auto-correlation) are constant over time.
  2. **Price vs Return:** Stock prices are non-stationary (they exhibit upward drift and wandering variance — random walk $I(1)$).
  3. **Why Returns are used:** First-differencing price via log returns produces a stationary $I(0)$ series, allowing covariance estimation and statistical inference without spurious regression.

---

### Q45: What is Volatility Clustering and the ARCH/GARCH effect?
* **How to Tackle:**
  1. **Mandelbrot's Dictum (1963):** *"Large changes tend to be followed by large changes, of either sign, and small changes tend to be followed by small changes."*
  2. **Implication:** Volatility is not constant across time. High-volatility regimes (e.g. 2020 COVID) cluster together.
  3. **Rebalancing Implication:** Static 5-year covariance matrices miss local volatility bursts. Rolling estimation windows or Risk Parity dynamically adapt to volatility clustering.

---

# Module 5: Python, NumPy & High-Performance Vectorization

### Q46: What is Vectorization and why is it $50\times - 100\times$ faster than Python `for` loops?
* **How to Tackle:**
  1. **Python Overhead:** Python is dynamically typed and interpreted. A Python `for` loop over a list performs type-checking, pointer dereferencing, and garbage collection on every single iteration.
  2. **NumPy / C Execution:** NumPy allocates contiguous blocks of C memory. Operations execute in compiled C loops utilizing CPU **SIMD (Single Instruction, Multiple Data)** registers, processing 4 to 8 floating-point numbers per CPU clock cycle.

---

### Q47: Explain the optimization in `src/database.py` that dropped ingestion time from 16s to 0.08s.
* **How to Tackle:**
  1. **The Bottleneck:** `df.iterrows()` iterates row-by-row in Python, packaging each row as a Python tuple and executing SQL `INSERT` statements individually ($25,000\times$).
  2. **The Vectorized Solution:** Registered the in-memory Pandas DataFrame directly into DuckDB's C++ engine via `conn.register("_temp", df)` followed by vectorized C++ query execution: `INSERT OR IGNORE INTO table SELECT * FROM _temp`.
  3. **Result:** Achieved **$200\times$ speedup** by operating entirely in C++ memory buffers.

---

### Q48: What is NumPy C-Contiguous vs Fortran-Contiguous memory layout?
* **How to Tackle:**
  1. **C-Contiguous (Row-Major):** Elements in the same row are stored adjacent in physical RAM. Traversal across rows (`matrix[i, :]`) leverages CPU L1/L2 cache locality.
  2. **Fortran-Contiguous (Column-Major):** Elements in the same column are stored adjacent.
  3. **Quant Impact:** Covariance calculation $\mathbf{w}^T \mathbf{\Sigma} \mathbf{w}$ performs matrix-vector dot products. Ensuring C-contiguous float64 memory layout maximizes memory bus throughput.

---

### Q49: What is the Python Global Interpreter Lock (GIL) and how does NumPy bypass it?
* **How to Tackle:**
  1. **The GIL:** A mutex in CPython that prevents multiple native OS threads from executing Python bytecodes simultaneously to ensure thread-safe reference counting.
  2. **NumPy Bypass:** When NumPy executes heavy linear algebra operations (`np.dot`, matrix inversions, BLAS/LAPACK routines), it **releases the GIL**. Multi-threaded C libraries (OpenBLAS/MKL) run concurrently across all physical CPU cores.

---

### Q50: What is the difference between Pandas `.loc` and `.iloc`?
* **How to Tackle:**
  1. **`.loc`:** Label-based indexing (uses index names / dates: `df.loc['2020-03-15', 'AAPL']`). Inclusive of end boundary.
  2. **`.iloc`:** Integer-position based indexing (uses memory offsets: `df.iloc[0:50, 0:3]`). Exclusive of end boundary (standard Python slice).
  3. **Best Practice in Backtesting:** Use `.iloc[:T]` for look-ahead-safe historical integer slices to avoid timestamp formatting bugs.

---

### Q51: How does NumPy Broadcasting work and what are the broadcasting rules?
* **How to Tackle:**
  1. **Definition:** How NumPy treats arrays with different shapes during arithmetic operations without making unneeded copies of data in memory.
  2. **The 2 Rules:**
     * Dimensions are compared element-wise starting from trailing (rightmost) dimensions.
     * Two dimensions are compatible if they are equal, or if one of them is 1.
  3. **Example in Returns:** Multiplying a matrix of asset returns shape `(1508, 12)` by a weight vector shape `(12,)` automatically broadcasts the weights across all 1,508 days in C memory.

---

### Q52: What is the Pandas `BlockManager` and why can `SettingWithCopyWarning` occur?
* **How to Tackle:**
  1. **`BlockManager`:** Internal Pandas engine that groups columns of identical dtype (e.g. all float64 columns) into consolidated 2D NumPy arrays.
  2. **`SettingWithCopyWarning`:** Occurs when chained indexing (`df['col'][mask] = val`) makes it ambiguous whether you are modifying a copy or the original underlying array in memory.
  3. **Fix:** Always use explicit `.loc[mask, 'col'] = val`.

---

### Q53: What is the role of Python Type Hints (`typing`) in quantitative codebases?
* **How to Tackle:**
  1. **Production Reliability:** Quant pipelines handle massive multidimensional numerical transformations. Using `Tuple[np.ndarray, float]`, `pd.DataFrame`, and `Optional[str]` ensures strict static code analysis with tools like `mypy`.
  2. **Compatibility Note:** In Python 3.9, we explicitly import `List, Dict, Optional, Tuple` from `typing` to maintain backward compatibility with legacy institutional execution environments.

---

# Module 6: DuckDB, Analytical SQL & Storage Internals

### Q54: Why was DuckDB chosen over SQLite and PostgreSQL for this platform?
* **How to Tackle:**
  1. **OLAP vs OLTP:** SQLite and PostgreSQL are row-oriented OLTP databases designed for individual transactional inserts (`INSERT INTO users`). DuckDB is an **in-process columnar OLAP database** designed for massive analytical aggregation queries (`AVG`, `STDDEV`, `LAG`, window functions) over time-series data.
  2. **Zero-Setup Embedded Engine:** Runs directly inside the Python process like SQLite without requiring Docker containers, database servers, or port configuration.
  3. **Vectorized Query Execution (Morsel-Driven Parallelism):** Processes data in chunks of 2,048 tuples using CPU vector instructions, outperforming SQLite by $10\times - 50\times$ on analytical queries.

---

### Q55: Explain how SQL Window Functions (`LAG`, `OVER`, `PARTITION BY`) calculate daily log returns.
* **How to Tackle:**
  1. **The SQL Query:**
     ```sql
     SELECT 
         ticker, date, adj_close,
         LN(adj_close / LAG(adj_close) OVER (PARTITION BY asset_id ORDER BY date)) AS log_return
     FROM price_data;
     ```
  2. **Execution:** `PARTITION BY asset_id` creates an isolated window for each stock. `ORDER BY date` sorts rows chronologically. `LAG(adj_close, 1)` pulls the previous day's price without expensive self-joins.

---

### Q56: How does DuckDB achieve Zero-Copy Data Sharing with Pandas and Apache Arrow?
* **How to Tackle:**
  1. **Arrow Integration:** DuckDB can read and query Apache Arrow record batches and Pandas memory pointers directly in RAM.
  2. **Zero-Copy:** No data serialization, string parsing, or disk writes occur. DuckDB executes SQL directly against the C memory addresses where Pandas loaded the CSV arrays.

---

### Q57: What is the difference between a Clustered Index and a Non-Clustered B-Tree Index?
* **How to Tackle:**
  1. **Clustered Index:** Dictates the physical sort order of the data on disk (only one per table).
  2. **Non-Clustered Index:** Creates a separate B-Tree index structure containing keys and row pointers back to the raw data table.
  3. **Our DuckDB Schema:** Created secondary indexes on `price_data(date)`, `price_data(asset_id)`, and `portfolio_weights(strategy_id)` to ensure instantaneous $O(\log N)$ joins.

---

### Q58: How do you write a Pivot View in SQL to compare Strategy Risk Metrics side-by-side?
* **How to Tackle:**
  1. **The SQL Query:**
     ```sql
     SELECT 
         s.name AS strategy_name,
         MAX(CASE WHEN rm.metric_name = 'CAGR' THEN rm.metric_value END) AS cagr,
         MAX(CASE WHEN rm.metric_name = 'Sharpe Ratio' THEN rm.metric_value END) AS sharpe,
         MAX(CASE WHEN rm.metric_name = 'Max Drawdown' THEN rm.metric_value END) AS max_dd
     FROM strategies s
     LEFT JOIN risk_metrics rm ON s.strategy_id = rm.strategy_id
     GROUP BY s.name;
     ```
  2. **Mechanics:** Conditional aggregation (`MAX(CASE WHEN...)`) converts key-value row storage into a tidy analytical tabular report.

---

### Q59: What are Common Table Expressions (CTEs) and why are they preferred over Nested Subqueries?
* **How to Tackle:**
  1. **Readability & Modularity:** CTEs (`WITH TableName AS (...)`) break complex multi-stage financial calculations into sequential, readable logical steps.
  2. **Query Optimizer Reuse:** Database query planners can evaluate CTEs once or inline them efficiently, unlike correlated subqueries which can trigger expensive nested loops.

---

### Q60: How does ACID compliance work in DuckDB?
* **How to Tackle:**
  1. **ACID:** Atomicity, Consistency, Isolation, Durability.
  2. **MVCC (Multi-Version Concurrency Control):** DuckDB uses MVCC with optimistic concurrency. Reads and writes do not block each other, and all batch pipeline insertions execute inside an atomic transaction block (`BEGIN TRANSACTION ... COMMIT`).

---

### Q61: What is the exact migration path from DuckDB to PostgreSQL for production?
* **How to Tackle:**
  1. **SQL Compatibility:** The DDL schema (`sql/schema.sql`) uses standard ANSI SQL data types (`INTEGER`, `VARCHAR`, `DOUBLE PRECISION`, `DATE`, `FOREIGN KEY`).
  2. **Code Change:** In `src/database.py`, replace `duckdb.connect(DB_PATH)` with `psycopg2.connect(host, dbname, user, password)`. Zero SQL queries need to be rewritten.

---

# Module 7: Power BI, DAX & Data Modeling Architecture

### Q62: What is the difference between Row Context and Filter Context in DAX?
* **How to Tackle:**
  1. **Row Context:** Exists when iterating over a table row-by-row (e.g. in a Calculated Column: `[Price] * [Units]`). It only knows the values of the current single row.
  2. **Filter Context:** The set of active filters applied to the data model by Slicers, Visuals, Rows/Columns in a Matrix, and cross-highlighting. It determines which subset of rows are aggregated by a measure.

---

### Q63: Why did clicking the Line Chart cause summary KPI cards to show `--` (Blank)?
* **How to Tackle:**
  1. **The Bug:** A Line Chart point contains two filter coordinates: `Strategy` AND `Date` (e.g., `March 14, 2021`).
  2. **The Reason:** `risk_metrics` contains overall 5-year summary statistics, with NO daily records for March 14, 2021. The date filter propagated to `risk_metrics`, resulting in 0 matching rows (`BLANK()`).
  3. **The Architectural Fix:** Use a **Strategy Bar Chart** or **Strategy Slicer** for filtering, because they filter purely on the `Strategy` dimension without transmitting a daily date filter.

---

### Q64: What is the Power BI VertiPaq Engine and how does it compress columnar data?
* **How to Tackle:**
  1. **In-Memory Columnar Database:** VertiPaq loads data into memory organized by column.
  2. **3 Compression Techniques:**
     * **Value Encoding:** Subtracts minimum value (e.g., storing dates 2019–2024 as small integers $0 \dots 1508$).
     * **Dictionary Encoding:** Replaces text strings (`'Equal Weight'`) with small integer IDs ($0, 1, 2$).
     * **Run-Length Encoding (RLE):** Compresses consecutive identical values (`10, 10, 10, 10` $\to$ `4x10`), achieving $10\times - 20\times$ data compression.

---

### Q65: What is the risk of Bi-Directional Cross-Filtering in complex Data Models?
* **How to Tackle:**
  1. **Ambiguous Filter Paths:** In schemas with multiple fact tables, bidirectional relationships can create circular filter loops, causing unexpected calculation results and severe performance degradation.
  2. **Best Practice:** Keep relationships **Single Direction** from dimension tables (1) to fact tables (*), and use explicit DAX `CALCULATE(..., CROSSFILTER(...))` only when specific reverse filtering is required.

---

### Q66: What is the difference between a Calculated Column and a DAX Measure?
* **How to Tackle:**
  1. **Calculated Column:** Evaluated at data refresh time, computed row-by-row, and stored permanently in RAM. Consumes file size and memory.
  2. **DAX Measure:** Evaluated dynamically at query time based on user slicer selections on the screen. Consumes zero RAM storage.
  3. **Rule:** Always use Measures for financial aggregations (`Sharpe Ratio`, `CAGR %`).

---

### Q67: What is Star Schema vs Snowflake Schema and why is Star Schema preferred in BI?
* **How to Tackle:**
  1. **Star Schema:** A central Fact table (`strategy_performance`) directly connected to denormalized Dimension tables (`strategies`, `assets`).
  2. **Snowflake Schema:** Dimension tables are further normalized into sub-tables (e.g. `assets` $\to$ `sectors` $\to$ `industries`).
  3. **Why Star Schema Wins:** Eliminates multi-hop table joins, enabling VertiPaq to scan columns at maximum memory bandwidth.

---

# Module 8: Scalability, Production Architecture & Edge Cases

### Q68: What happens to Covariance Matrix Estimation when scaling from 12 stocks to 500 stocks?
* **How to Tackle:**
  1. **The $N > T$ Problem:** If you have $N = 500$ stocks and only $T = 252$ trading days of history, the sample covariance matrix has rank at most $T < N$. It is strictly **singular (non-invertible)** with $500 - 252 = 248$ zero eigenvalues!
  2. **Random Matrix Theory (Marchenko-Pastur Law):** Most empirical eigenvalues represent pure random noise rather than true market correlation.
  3. **The Fix:** Apply **Factor Models** (e.g., Barra / Fama-French 5-Factor Model) where $\mathbf{\Sigma} = \mathbf{B}\mathbf{\Sigma}_F\mathbf{B}^T + \mathbf{D}$, reducing 125,000 covariance parameters down to a small factor matrix.

---

### Q69: What is the difference between a Vectorized Backtester and an Event-Driven Backtester?
* **How to Tackle:**
  1. **Vectorized (Our Platform):** Uses Pandas/NumPy array operations across full time-series matrices simultaneously. Extremely fast ($< 2\text{ seconds}$ for 5 years), ideal for rapid strategy research, but cannot easily model intraday order books, partial fills, or queue position.
  2. **Event-Driven:** Uses an event loop (`OnBar()`, `OnOrderEvent()`, `OnTrade()`) processing one tick at a time. Slower, but perfectly simulates real-world order routing, limit order matching, and broker API socket communication.

---

### Q70: How would you scale data ingestion to 5,000 stocks using `asyncio` and parallel workers?
* **How to Tackle:**
  1. **Async I/O:** Network requests are I/O-bound. Using Python's `aiohttp` or `asyncio.gather()` allows fetching 5,000 stock tickers concurrently across non-blocking sockets.
  2. **Worker Pool:** Use `multiprocessing.Pool` for CPU-bound data cleaning and validation, partitioning tickers across all physical CPU cores.

---

### Q71: How do you handle extreme market regimes (e.g., March 2020 COVID Crash) in risk models?
* **How to Tackle:**
  1. **Correlation Breakdown:** During market crashes, correlations between equities spike toward $+1.0$ ("in a crisis, all correlations go to 1"), destroying traditional diversification.
  2. **Defensive Strategies:** Minimum Variance and Risk Parity protect capital by having pre-allocated higher weights to low-beta defensive assets (Utilities, Consumer Staples, Healthcare).
  3. **Advanced Fix:** Implement Regime-Switching Models (Markov Switching) or Volatility Targeting (scaling cash exposure inversely to rolling VIX).

---

### Q72: What is the Capital Asset Pricing Model (CAPM) and its fundamental assumptions?
* **How to Tackle:**
  1. **Formula:** $\mathbb{E}[R_i] = R_f + \beta_i (\mathbb{E}[R_m] - R_f)$.
  2. **Key Assumptions:**
     * Investors are rational, risk-averse mean-variance optimizers.
     * Homogeneous expectations (all investors agree on expected returns and covariances).
     * Frictionless markets (no transaction costs, no taxes, borrow/lend at risk-free rate).
     * Single-period investment horizon.
  3. **Why it matters:** Even with theoretical flaws, CAPM provides the foundational benchmark for systematic risk ($\beta$) and manager skill ($\alpha$).

---

### Q73: How do you prevent division by zero in financial risk metric calculations?
* **How to Tackle:**
  1. **Sortino Ratio with 0 downside:** If a portfolio has only positive returns, downside deviation $\sigma_d = 0$. In `src/risk_metrics.py`, we add an epsilon check: `if downside_dev < 1e-12: return np.nan` or return a high bounded score.
  2. **Beta with flat benchmark:** If benchmark variance $\sigma_m^2 = 0$, beta is mathematically undefined; return $0.0$ to ensure pipeline continuity.

---

### Q74: If an interviewer asks: "What would you build next if given 2 more weeks?", how do you answer?
* **How to Tackle:**
  1. **Phase 1: Factor Model Integration:** Implement Fama-French 3-Factor (Size, Value) and Carhart Momentum factor decompositions.
  2. **Phase 2: Dynamic Covariance:** Replace static sample covariance with Exponentially Weighted Moving Average (EWMA) or GARCH(1,1) volatility forecasting.
  3. **Phase 3: Automated PDF Factsheets:** Add automated QuantStats/ReportLab tear-sheet PDF generation for institutional client reporting.
