# Quantitative Portfolio Research & Backtesting Platform
## The Master Student Study & Interview Defense Guide
> **Target Audience**: Mathematics & Computing students with strong coding/analytical foundations and **0 prior background in finance**.  
> **Goal**: Provide a complete, crystal-clear explanation of every concept, equation, line of architecture, and backtesting mechanic used in this project so you can comfortably explain and defend it in technical and quantitative interviews.

---

# Table of Contents
1. [Executive Overview (What Is This Project in Plain English?)](#1-executive-overview)
2. [The "Zero-Finance" Dictionary: Every Term & Metric Explained](#2-the-zero-finance-dictionary)
   - [2.1 Financial Market Data Basics](#21-financial-market-data-basics)
   - [2.2 Returns: Simple vs. Logarithmic](#22-returns-simple-vs-logarithmic)
   - [2.3 Risk, Volatility & The Covariance Matrix](#23-risk-volatility--the-covariance-matrix)
   - [2.4 Portfolio Construction & Modern Portfolio Theory](#24-portfolio-construction--modern-portfolio-theory)
   - [2.5 The 3 Portfolio Strategies](#25-the-3-portfolio-strategies)
   - [2.6 Risk & Performance Evaluation Metrics](#26-risk--performance-evaluation-metrics)
   - [2.7 Backtesting, Frictions & Critical Biases](#27-backtesting-frictions--critical-biases)
3. [Architecture & Code Pipeline Walkthrough (Step-by-Step)](#3-architecture--code-pipeline-walkthrough)
4. [Database & SQL Architecture (Why DuckDB?)](#4-database--sql-architecture)
5. [Business Intelligence (Power BI & Tableau Integration)](#5-business-intelligence)
6. [Empirical Backtest Results & Financial Insights](#6-empirical-backtest-results--financial-insights)
7. [The Interview Playbook: How to Talk About This Project](#7-the-interview-playbook)
   - [7.1 The 60-Second Elevator Pitch (Spoken Script)](#71-the-60-second-elevator-pitch)
   - [7.2 The 3-Minute Deep Dive (Spoken Script)](#72-the-3-minute-deep-dive)
   - [7.3 Top 15 Interview Questions & Bulletproof Answers](#73-top-15-interview-questions--bulletproof-answers)
   - [7.4 Intellectual Honesty: Defending Limitations & Future Scale](#74-intellectual-honesty-defending-limitations--future-scale)

---

# 1. Executive Overview

### What is this project?
Imagine you have \$1,000,000 to invest in the US stock market across 12 major companies (like Apple, Microsoft, ExxonMobil, Johnson & Johnson). 
- How should you divide your money among them? 
- Should you give every stock an equal amount (\$83,333 each)? 
- Should you mathematically calculate a combination that gives the absolute lowest volatility/risk? 
- Or should you ensure that every single stock contributes an equal share of overall risk?

This project is a **quantitative portfolio research and backtesting platform**. It:
1. **Downloads and cleans 6 years of historical daily price data (2019–2024)** for 12 large-cap US stocks and the S&P 500 benchmark.
2. **Implements three mathematical portfolio allocation models**: Equal Weight ($1/N$), Minimum Variance (Quadratic Programming via SLSQP), and Risk Parity (Equal Risk Contribution).
3. **Simulates historical backtesting** over 1,508 trading days with monthly rebalancing and realistic transaction costs (10 basis points), strictly preventing look-ahead bias.
4. **Calculates 10 industry-standard risk and performance metrics** (Sharpe Ratio, Sortino Ratio, Max Drawdown, Beta, CAGR, Calmar, Tracking Error, etc.) from first principles.
5. **Persists all raw data, weights, daily equity curves, and performance metrics in an analytical DuckDB SQL database**.
6. **Exports clean, schema-consistent datasets** ready for executive visual dashboards in **Power BI** and **Tableau**.

---

# 2. The "Zero-Finance" Dictionary

---

### 2.1 Financial Market Data Basics

#### 1. Asset / Stock / Equities
* **Definition**: A financial asset representing fractional ownership in a corporation (e.g., Apple Inc.).
* **Intuition**: Buying 1 share means you own a tiny fraction of that company and its future cash flows.

#### 2. Ticker Symbol
* **Definition**: A short abbreviation used to uniquely identify publicly traded shares (e.g., `AAPL` for Apple, `MSFT` for Microsoft, `^GSPC` for the S&P 500 Index).

#### 3. OHLCV Data (Open, High, Low, Close, Volume)
* **Definition**: The standard five price/activity points recorded for every financial asset in each trading session:
  - **Open**: Price at market open (9:30 AM EST).
  - **High**: Highest price reached during the day.
  - **Low**: Lowest price reached during the day.
  - **Close**: Price at market close (4:00 PM EST).
  - **Volume**: Total number of shares traded that day.

#### 4. Adjusted Close (`Adj Close`) — *Crucial Concept*
* **Definition**: The closing price of a stock that has been mathematically adjusted to account for corporate actions, primarily **stock splits** and **dividend payments**.
* **Intuition / Example**: 
  - *Stock Split*: If Apple stock is \$500 and undergoes a 5-for-1 split, the price suddenly becomes \$100. If you look at raw close prices, it looks like a catastrophic 80% loss in one day! Adjusted Close retroactively scales past prices down so the return is 0%.
  - *Dividends*: When a company pays a cash dividend, the stock price drops by the dividend amount. Adjusted close adds that dividend back into historical prices to reflect **total shareholder return**.
* **Project Usage**: In `src/data_loader.py`, we exclusively extract `Adj Close` for all return and portfolio calculations.

---

### 2.2 Returns: Simple vs. Logarithmic

#### 5. Simple Return ($R_t$) — *Arithmetic Return*
* **Formula**: 
  $$R_t = \frac{P_t - P_{t-1}}{P_{t-1}} = \frac{P_t}{P_{t-1}} - 1$$
* **Intuition**: The actual percentage gain or loss on your money from one day to the next. If you buy at \$100 and it rises to \$110, $R_t = \frac{110-100}{100} = +10\% = 0.10$.
* **Key Property (Cross-Asset Additivity)**: The return of a portfolio is the weighted sum of the simple returns of its constituent assets:
  $$R_{\text{portfolio}} = \sum_{i=1}^N w_i R_i$$
* **Project Usage**: Used in `src/backtest.py` for tracking actual portfolio dollars and equity curves.

#### 6. Logarithmic Return ($r_t$) — *Continuously Compounded Return*
* **Formula**:
  $$r_t = \ln\left(\frac{P_t}{P_{t-1}}\right) = \ln(P_t) - \ln(P_{t-1})$$
* **Intuition**: The rate of continuous compounding. If price goes from \$100 to \$110, $r_t = \ln(1.10) \approx 0.09531$ (or 9.531%).
* **Key Property (Time Additivity)**: Total multi-period return is simply the sum of single-period log returns:
  $$r_{0 \to T} = r_1 + r_2 + \dots + r_T$$
* **Mathematical Normality**: In financial theory, log returns are much closer to being normally (Gaussian) distributed than simple returns, and they prevent prices from ever becoming negative ($e^{r} > 0$).
* **Project Usage**: Used in `src/returns.py` and `src/optimization.py` for estimating the historical covariance matrix $\mathbf{\Sigma}$.

---

### 2.3 Risk, Volatility & The Covariance Matrix

#### 7. Expected Return ($\mu$)
* **Definition**: The mean (average) return of an asset over time. It represents the central tendency of future expected payoffs.

#### 8. Variance ($\sigma^2$) and Standard Deviation ($\sigma$)
* **Definition**: The statistical measure of the dispersion of returns around their mean.
* **Formula**:
  $$\sigma^2 = \frac{1}{T-1} \sum_{t=1}^T (R_t - \bar{R})^2, \quad \sigma = \sqrt{\sigma^2}$$
* **Intuition**: A stock whose price swings wildly between +5% and -5% daily has high variance (high risk). A stock that moves +0.1% steadily has low variance (low risk).

#### 9. Volatility & Annualized Volatility
* **Definition**: In finance, "volatility" is simply the standard deviation of returns ($\sigma$).
* **Annualization Formula**:
  $$\sigma_{\text{annual}} = \sigma_{\text{daily}} \times \sqrt{252}$$
* **Why $\sqrt{252}$?**: There are approximately 252 trading days in a US financial year (excluding weekends and market holidays). Since variance scales linearly with time ($T$), standard deviation (the square root of variance) scales with $\sqrt{T}$:
  $$\text{Var}(\text{Annual}) = 252 \times \text{Var}(\text{Daily}) \implies \sigma_{\text{Annual}} = \sqrt{252} \times \sigma_{\text{Daily}}$$

#### 10. Covariance ($\text{Cov}(X, Y)$ or $\sigma_{ij}$)
* **Definition**: A measure of how two assets move in tandem.
  - Positive covariance: Asset A goes up when Asset B goes up (e.g., Apple and Microsoft).
  - Negative covariance: Asset A goes up when Asset B goes down (e.g., Oil vs. Airlines during an oil spike).
  - Zero covariance: Asset movements are completely independent.

#### 11. Correlation ($\rho_{ij}$)
* **Formula**:
  $$\rho_{ij} = \frac{\text{Cov}(X, Y)}{\sigma_X \sigma_Y} \quad \text{where } -1 \le \rho_{ij} \le 1$$
* **Intuition**: Standardized covariance. $\rho = +1$ means identical co-movement; $\rho = -1$ means perfect inverse movement.

#### 12. Diversification ("The Only Free Lunch in Finance")
* **Intuition**: If you hold two assets that are not perfectly correlated ($\rho < 1$), the combined portfolio volatility is **strictly less than the weighted average of individual volatilities**. You reduce risk without necessarily giving up return.

#### 13. Covariance Matrix ($\mathbf{\Sigma}$) — *Core Mathematical Engine*
* **Definition**: An $N \times N$ symmetric, positive semi-definite matrix where entry $\mathbf{\Sigma}_{ij}$ is the covariance between asset $i$ and asset $j$.
* **Example Structure for 3 Assets**:
  $$\mathbf{\Sigma} = \begin{bmatrix} 
  \sigma_1^2 & \sigma_{12} & \sigma_{13} \\ 
  \sigma_{21} & \sigma_2^2 & \sigma_{23} \\ 
  \sigma_{31} & \sigma_{32} & \sigma_3^2 
  \end{bmatrix}$$
* **Properties**:
  - The diagonal elements ($\mathbf{\Sigma}_{ii}$) are the individual asset variances $\sigma_i^2$.
  - The off-diagonal elements ($\mathbf{\Sigma}_{ij}$) are the pairwise covariances ($\sigma_{ij} = \sigma_{ji}$).
* **Project Usage**: Calculated in `src/optimization.py` using sample covariance of rolling historical log returns.

---

### 2.4 Portfolio Construction & Modern Portfolio Theory

#### 14. Portfolio Weights Vector ($\mathbf{w}$)
* **Definition**: An $N$-dimensional vector $\mathbf{w} = [w_1, w_2, \dots, w_N]^T$ where $w_i$ is the fraction of total capital allocated to asset $i$.

#### 15. Long-Only & Budget Constraints
* **Budget Constraint**: $\sum_{i=1}^N w_i = \mathbf{w}^T \mathbf{1} = 1.0$ (100% of capital is deployed).
* **Long-Only Constraint**: $w_i \ge 0$ for all $i$ (no short selling / borrowing shares).

#### 16. Portfolio Variance ($\sigma_p^2$) — Quadratic Form
* **Formula**:
  $$\sigma_p^2 = \mathbf{w}^T \mathbf{\Sigma} \mathbf{w} = \sum_{i=1}^N \sum_{j=1}^N w_i w_j \sigma_{ij}$$
* **Portfolio Volatility**: $\sigma_p = \sqrt{\mathbf{w}^T \mathbf{\Sigma} \mathbf{w}}$.

---

### 2.5 The 3 Portfolio Strategies

```
┌────────────────────────────────────────────────────────────────────────┐
│                        3 PORTFOLIO STRATEGIES                          │
├──────────────────────┬─────────────────────────┬───────────────────────┤
│ 1. Equal Weight (1/N)│ 2. Minimum Variance     │ 3. Risk Parity (ERC)  │
│ ──────────────────── │ ─────────────────────── │ ───────────────────── │
│ • Simple baseline    │ • Minimize portfolio    │ • Equalize risk       │
│ • w_i = 1 / N        │   variance              │   contribution across │
│ • No estimation error│ • Min w^T Σ w           │   all assets          │
│ • High diversification│ • Defensive allocation │ • Robust in all       │
│                      │   (heavy JNJ, PG)       │   market regimes      │
└──────────────────────┴─────────────────────────┴───────────────────────┘
```

#### Strategy 1: Equal Weight ($1/N$)
* **Concept**: Divide capital evenly among all available stocks. With $N=12$, every stock gets $w_i = \frac{1}{12} \approx 8.33\%$.
* **Pros**: Requires zero parameter estimation (no covariance matrix needed), immune to estimation error, highly robust.
* **Cons**: Ignores asset risk differences (treats high-volatility tech the same as stable utilities).

#### Strategy 2: Minimum Variance Portfolio (Global Minimum Variance - GMV)
* **Concept**: Find the unique portfolio weight combination $\mathbf{w}$ that produces the absolute lowest total portfolio variance.
* **Optimization Problem**:
  $$\min_{\mathbf{w}} \quad \frac{1}{2} \mathbf{w}^T \mathbf{\Sigma} \mathbf{w}$$
  $$\text{subject to} \quad \sum_{i=1}^N w_i = 1, \quad 0 \le w_i \le 1$$
* **Solver**: Solved via Sequential Least Squares Programming (`scipy.optimize.minimize(method='SLSQP')`).
* **Financial Intuition**: Overweights low-volatility, defensive stocks (e.g., Procter & Gamble, Johnson & Johnson) and stocks with low/negative correlations.

#### Strategy 3: Risk Parity / Equal Risk Contribution (ERC)
* **Concept**: In traditional portfolios, 80-90% of total risk is often driven by a few volatile tech stocks. Risk Parity ensures **every single stock contributes an identical amount of risk ($1/N$) to the total portfolio volatility**.
* **Marginal Risk Contribution (MRC)**:
  $$\text{MRC}_i = \frac{\partial \sigma_p}{\partial w_i} = \frac{(\mathbf{\Sigma} \mathbf{w})_i}{\sigma_p}$$
* **Total Risk Contribution ($\text{RC}_i$)**:
  $$\text{RC}_i = w_i \times \text{MRC}_i = \frac{w_i (\mathbf{\Sigma} \mathbf{w})_i}{\sigma_p}$$
* **Mathematical Objective**:
  $$\min_{\mathbf{w}} \sum_{i=1}^N \sum_{j=1}^N \left( \text{RC}_i - \text{RC}_j \right)^2 \quad \text{subject to } \sum w_i = 1, w_i \ge 0$$
* **Financial Intuition**: Highly volatile assets receive smaller weights, while stable assets receive larger weights, creating a truly risk-balanced portfolio.

---

### 2.6 Risk & Performance Evaluation Metrics

#### 17. Total Return
* **Formula**: $\text{Total Return} = \frac{V_{\text{final}} - V_{\text{initial}}}{V_{\text{initial}}}$
* **Intuition**: Overall percentage growth of the portfolio over the full 6-year period.

#### 18. CAGR (Compound Annual Growth Rate)
* **Formula**:
  $$\text{CAGR} = \left(\frac{V_{\text{final}}}{V_{\text{initial}}}\right)^{\frac{252}{T}} - 1$$
* **Intuition**: The smooth annual rate of return that would turn the initial capital into the final capital over $T$ trading days.

#### 19. Risk-Free Rate ($R_f$)
* **Definition**: The theoretical return of an investment with zero default risk (typically US Treasury Bills).
* **Project Value**: We set $R_f = 5.0\%$ annual ($0.05 / 252$ daily) based on prevailing US short-term yields.

#### 20. Sharpe Ratio (The Gold Standard of Risk-Adjusted Return)
* **Formula**:
  $$\text{Sharpe} = \frac{\bar{R}_p - R_f}{\sigma_p} \times \sqrt{252}$$
* **Intuition**: How much extra return are you getting for each unit of total risk?
  - $< 0$: Return is worse than cash in a risk-free bank.
  - $0.5 - 1.0$: Good.
  - $> 1.0$: Excellent institutional performance.

#### 21. Downside Deviation & Sortino Ratio
* **Downside Deviation ($\sigma_d$)**: Standard deviation calculated **only on negative returns** (returns below $R_f$).
* **Sortino Ratio Formula**:
  $$\text{Sortino} = \frac{\bar{R}_p - R_f}{\sigma_d} \times \sqrt{252}$$
* **Why Sortino?**: The Sharpe ratio penalizes both upside volatility (huge positive spikes) and downside volatility equally. But investors love upside volatility! Sortino only penalizes downside drops.

#### 22. Maximum Drawdown (MDD)
* **Formula**:
  $$\text{Drawdown}_t = \frac{V_t - \max_{\tau \le t}(V_\tau)}{\max_{\tau \le t}(V_\tau)}, \quad \text{MDD} = \min_{t}(\text{Drawdown}_t)$$
* **Intuition**: The largest percentage peak-to-trough drop in your portfolio value before a new peak is achieved. If your account grows to \$1,200,000 and crashes to \$900,000, $\text{MDD} = \frac{900,000 - 1,200,000}{1,200,000} = -25.0\%$.

#### 23. Calmar Ratio
* **Formula**: $\text{Calmar Ratio} = \frac{\text{CAGR}}{|\text{Max Drawdown}|}$
* **Intuition**: Annual return earned per unit of worst-case historical loss.

#### 24. Beta ($\beta$) — Market Risk Sensitivity
* **Formula**:
  $$\beta = \frac{\text{Cov}(R_{\text{portfolio}}, R_{\text{benchmark}})}{\text{Var}(R_{\text{benchmark}})}$$
* **Intuition**: How sensitive is the portfolio to broader market (S&P 500) swings?
  - $\beta = 1.0$: Moves in lockstep with the market.
  - $\beta = 0.7$: 30% less volatile than the market (defensive).
  - $\beta = 1.3$: 30% more volatile than the market (aggressive).

#### 25. Tracking Error
* **Formula**: $\text{TE} = \text{StdDev}(R_{\text{portfolio}} - R_{\text{benchmark}}) \times \sqrt{252}$
* **Intuition**: How closely the strategy mirrors the benchmark index.

---

### 2.7 Backtesting, Frictions & Critical Biases

#### 26. Historical Backtesting
* **Definition**: Simulating an algorithmic investment strategy over past historical market data to see how it would have performed.

#### 27. Look-Ahead Bias (The Cardinal Sin in Quant Finance)
* **Definition**: Accidentally using information from the future that was not available at the moment a historical investment decision was made.
* **Example**: If calculating portfolio weights on January 1, 2021, and you include price data from March 2021 in your covariance matrix estimation, your backtest is fraudulent.
* **How Our Code Strictly Prevents Look-Ahead Bias**:
  In `src/backtest.py`:
  ```python
  # When rebalancing at trading day index t_idx:
  # We slice historical data strictly UP TO t_idx - 1
  historical_data_slice = log_returns.iloc[:t_idx]
  # The optimizer ONLY sees past data [0 : t_idx-1]
  weights = optimizer_func(historical_data_slice)
  # These weights are then applied to forward returns from t_idx to next rebalance
  ```

#### 28. Survivorship Bias
* **Definition**: Testing a strategy on a universe of companies that are successful today (e.g., AAPL, NVDA, MSFT), ignoring companies that went bankrupt, were delisted, or acquired over the past 10 years (e.g., Enron, Lehman Brothers).
* **Project Transparency**: We explicitly document this limitation in `docs/limitations.md`.

#### 29. Basis Points (bps)
* **Definition**: A standard unit of measure in finance. $1 \text{ basis point} = 0.01\% = 0.0001$.
* **Example**: $10 \text{ bps} = 0.10\% = 0.0010$.

#### 30. Turnover & Transaction Cost Model
* **Turnover**: The total volume of assets bought and sold during a rebalance:
  $$\text{Turnover}_t = \sum_{i=1}^N |w_{i, t} - w_{i, t^{-}}|$$
* **Cost Deduction**: We deduct 10 bps (0.10%) of the dollar amount traded at each rebalance date:
  $$\text{Cost}_t = \text{Turnover}_t \times V_t \times 0.0010$$
* **Result**: `Equal Weight` incurred \$0 in rebalance costs (since fixed drift was minimal relative to monthly target), while `Minimum Variance` incurred \$7,139 in costs due to active covariance shifts.

---

# 3. Architecture & Code Pipeline Walkthrough

```
                              DATA FLOW PIPELINE
┌─────────────────┐
│  Yahoo Finance  │ (yfinance API)
└────────┬────────┘
         ▼
┌─────────────────┐
│ data_loader.py  │ Downloads & caches 12 tickers + S&P 500 (^GSPC) [2019-2024]
└────────┬────────┘
         ▼
┌──────────────────┐
│data_cleaning.py  │ 5-Stage validation: missing values, positivity, order, gaps
└────────┬─────────┘
         ▼
┌──────────────────┐
│   returns.py     │ Simple returns (cash) & Log returns (covariance estimation)
└────────┬─────────┘
         ▼
┌──────────────────┐
│ optimization.py  │ SLSQP solvers for Minimum Variance & Risk Parity (ERC)
└────────┬─────────┘
         ▼
┌──────────────────┐
│   backtest.py    │ 1,508 trading days simulation, monthly rebalance, 10 bps cost
└────────┬─────────┘
         ▼
┌──────────────────┐
│ risk_metrics.py  │ 10 Metrics: Sharpe, Sortino, Drawdown, Beta, CAGR, Calmar, TE
└────────┬─────────┘
         ▼
┌──────────────────┐
│  database.py     │ Ingests 6 structured tables into DuckDB (quant_portfolio.duckdb)
└────────┬─────────┘
         ▼
┌──────────────────┐
│export_results.py │ Exports 5 CSV files for Power BI & Tableau dashboards
└──────────────────┘
```

### Module Breakdown:
1. **`src/config.py`**: Centralized configuration file. Contains universe tickers, benchmark symbol, date ranges, initial capital (\$1,000,000), rebalance frequency (Monthly), transaction cost rate (10 bps), risk-free rate (5.0%), and directory paths.
2. **`src/data_loader.py`**: Downloads daily historical price data from Yahoo Finance and caches it to disk (`data/raw/`) to guarantee offline reproducibility and prevent redundant network calls.
3. **`src/data_cleaning.py`**: Runs a 5-step automated audit: validates non-empty data, verifies strictly positive prices, checks for duplicate dates, confirms ascending chronological order, and audits date gaps.
4. **`src/returns.py`**: Computes daily simple arithmetic returns $R_t$, daily continuously compounded log returns $r_t$, cumulative total growth curves, and rolling metrics.
5. **`src/portfolio.py`**: Portfolio allocation utilities: equal weighting vector generation, weight normalization ($\sum w_i = 1, w_i \ge 0$), portfolio return calculation, and portfolio variance quadratic form ($\mathbf{w}^T \mathbf{\Sigma} \mathbf{w}$).
6. **`src/optimization.py`**: Mathematical optimization engines: computes historical covariance matrix $\mathbf{\Sigma}$, solves the Minimum Variance constrained quadratic program via SLSQP, and solves the Risk Parity equal risk contribution objective function.
7. **`src/backtest.py`**: Historical simulation backtester. Traverses 1,508 trading days, executes monthly rebalancing at strict boundaries, applies the 10 bps transaction cost model, and records daily portfolio values and cash returns.
8. **`src/risk_metrics.py`**: Pure mathematical implementations of all 10 financial metrics with annualized scaling.
9. **`src/benchmark.py`**: Downloads and aligns the S&P 500 benchmark (^GSPC) to identical calendar trading days and computes comparative metrics.
10. **`src/database.py`**: Initializes DuckDB tables and uses bulk registration to insert 18,108 price records, 2,448 weight entries, 4,524 daily backtest states, and 36 risk metrics.
11. **`src/export_results.py`**: Generates 5 clean, human-readable CSV files in `data/exports/` for business intelligence tooling.
12. **`main.py`**: The master orchestration script running all 10 steps in sequence with progress reporting and console analytics.

---

# 4. Database & SQL Architecture

### Why DuckDB?
| Feature | DuckDB | Traditional SQLite | PostgreSQL Server |
| :--- | :--- | :--- | :--- |
| **Architecture** | In-Process Columnar OLAP | In-Process Row-oriented OLTP | Client-Server RDBMS |
| **Setup Overhead** | **Zero (single file)** | Zero (single file) | High (requires local daemon & port) |
| **Analytical Query Speed** | **Extremely Fast (Vectorized C++)** | Slow on aggregates/scans | Fast, but heavier infrastructure |
| **Data Science Interop** | **Direct zero-copy Pandas integration** | Requires row-by-row iteration | Requires network serialization |
| **SQL Dialect** | **PostgreSQL compatible** | Limited SQL dialect | Full standard SQL |

### Schema Structure (`quant_portfolio.duckdb`):
- `assets`: Metadata on the 12 stocks (Ticker, Company Name, Sector, Exchange).
- `price_data`: 18,108 daily adjusted close price records indexed by asset and date.
- `strategies`: Catalog of the 3 strategies plus benchmark.
- `portfolio_weights`: 2,448 historical weight allocations across each monthly rebalance date.
- `backtest_results`: 4,524 daily portfolio values and daily returns across the 5-year simulation.
- `risk_metrics`: 36 computed performance metrics (9 metrics $\times$ 4 strategies).

---

# 5. Business Intelligence

Exported files in `data/exports/`:
1. `strategy_performance.csv`: Daily dates, strategy names, portfolio values, normalized values (starting at 1.0), and daily returns.
2. `risk_metrics.csv`: Final risk and return metrics formatted for KPI cards.
3. `portfolio_weights.csv`: Rebalance date, strategy, ticker, and asset weight.
4. `benchmark_comparison.csv`: Summary metrics table comparing strategies to S&P 500.
5. `asset_returns.csv`: Individual asset daily and cumulative returns for correlation heatmaps.

### Dashboard Implementations:
- **Power BI (`dashboards/powerbi/README.md`)**: Contains exact steps for a 3-page executive report (Portfolio Overview, Strategy Comparison, Risk & Allocation) with custom DAX measures for KPI cards and drawdown area charts.
- **Tableau (`dashboards/tableau/README.md`)**: Contains step-by-step instructions for building 5 interactive worksheets and combining them into an interactive executive dashboard.

---

# 6. Empirical Backtest Results & Financial Insights

### Performance Summary Table (2019 – 2024)

| Strategy | Total Return | CAGR | Ann. Volatility | Sharpe Ratio | Sortino Ratio | Max Drawdown | Beta | Calmar Ratio | Tracking Error |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Equal Weight ($1/N$)** | **256.05%** | **23.64%** | 18.90% | **0.93** | **1.32** | **-29.44%** | 0.90 | **0.80** | 5.81% |
| **Risk Parity (ERC)** | **242.16%** | **22.82%** | 18.32% | **0.91** | **1.31** | **-29.48%** | 0.86 | **0.77** | 6.60% |
| **Minimum Variance** | 127.19% | 14.70% | **17.41%** | 0.56 | 0.80 | -31.86% | **0.71** | 0.46 | 11.50% |
| **S&P 500 (^GSPC)** | 141.31% | 15.86% | 20.14% | 0.56 | 0.78 | -33.92% | 1.00 | 0.47 | 0.00% |

### Key Takeaways to Share with Your Interviewer:
1. **Why did Equal Weight and Risk Parity beat the S&P 500?**  
   The S&P 500 is market-cap weighted, meaning mega-cap stocks dominate the index. In our 12-stock universe, Equal Weight and Risk Parity gave equal exposure to high-performing growth stocks (like Eli Lilly `+634%` and Apple `+568%`) rather than letting a few names dominate, producing higher compound annual growth (~23% vs 15.8%).
2. **Why was Minimum Variance's return lower?**  
   Minimum Variance solely minimizes volatility ($\mathbf{w}^T \mathbf{\Sigma} \mathbf{w}$) without regard to expected returns. It allocated over 64% of capital to defensive consumer staples and healthcare (Johnson & Johnson and Procter & Gamble). While this successfully reduced annualized volatility to **17.41%** (the lowest of all strategies), it sacrificed participation in mega-cap tech rallies.

---

# 7. The Interview Playbook

---

### 7.1 The 60-Second Elevator Pitch

> *"I built a Quantitative Portfolio Research and Backtesting Platform in Python and DuckDB that models, backtests, and evaluates multi-asset portfolio strategies. I took 6 years of daily market data across 12 US equities and evaluated three distinct allocation strategies: Equal Weight ($1/N$), Minimum Variance using SciPy's SLSQP quadratic optimizer, and Risk Parity based on Equal Risk Contribution. I built a look-ahead-bias-free backtesting engine with monthly rebalancing and a 10 basis points transaction cost model, calculating 10 key risk metrics from first principles. Over the 2019 to 2024 test period, Equal Weight and Risk Parity delivered Sharpe ratios above 0.91, outperforming the S&P 500's 0.56 Sharpe, while Minimum Variance successfully reduced market beta to 0.71. All results are stored in an analytical DuckDB SQL database and exported for Power BI and Tableau visualization."*

---

### 7.2 The 3-Minute Deep Dive

> *"The objective of this project was to design an end-to-end quantitative investment research platform demonstrating portfolio construction, mathematical optimization, risk analysis, and analytical data engineering.*
>
> *First, for the data pipeline, I used Yahoo Finance to pull adjusted closing prices across a diversified 12-stock universe representing 7 economic sectors. I built a 5-stage validation engine in Python to audit missing values, zero/negative prices, and non-trading date gaps.*
>
> *Second, for portfolio construction, I implemented three allocation methodologies. The baseline is Equal Weight ($1/N$). The second is Global Minimum Variance, which uses quadratic programming via SciPy's SLSQP optimizer to minimize portfolio variance $\mathbf{w}^T \mathbf{\Sigma} \mathbf{w}$ subject to long-only budget constraints. The third is Risk Parity, which numerically equalizes the marginal risk contribution of each asset so that no single stock dominates portfolio risk.*
>
> *Third, the backtesting engine traverses 1,508 trading days from 2019 through 2024 with monthly rebalancing. To strictly prevent look-ahead bias, weights computed on any rebalance date are estimated using historical data up to date $T-1$ only. I also incorporated a realistic transaction cost model of 10 basis points per one-way turnover.*
>
> *Fourth, I evaluated the strategies against the S&P 500 benchmark using 10 metrics implemented from first principles, including annualized Sharpe, Sortino, Maximum Drawdown, Beta, and Tracking Error. Equal Weight and Risk Parity achieved annual returns of ~23% with Sharpe ratios above 0.91, compared to the S&P 500's 15.86% return and 0.56 Sharpe. Minimum Variance achieved the lowest annualized volatility at 17.41% and a market beta of 0.71.*
>
> *Finally, from a data engineering perspective, all historical prices, weights, daily equity curves, and metrics are stored in a columnar DuckDB database using a normalized schema with secondary indexing. I also exported clean, schema-aligned CSVs and designed dashboard blueprints for Power BI and Tableau. The codebase is thoroughly tested with 39 automated unit tests verifying mathematical correctness across all modules."*

---

### 7.3 Top 15 Interview Questions & Bulletproof Answers

#### Q1: Why did you use Adjusted Close instead of standard Close prices?
> **Answer**: "Standard closing prices do not account for stock splits and cash dividends. If a stock undergoes a 2-for-1 split, its closing price drops by 50% overnight, creating a false -50% loss. Adjusted Close retroactively normalizes for splits and reinvests dividends, accurately reflecting the true total shareholder return."

#### Q2: What is the difference between simple and log returns, and where did you use each?
> **Answer**: "Simple returns are arithmetically additive across assets in a portfolio ($R_p = \sum w_i R_i$), so I used simple returns for portfolio accounting and equity curves in the backtest engine. Log returns are additive over time ($\sum \ln(P_t/P_{t-1}) = \ln(P_T/P_0)$) and follow a distribution closer to normal, so I used log returns for historical covariance matrix estimation."

#### Q3: Why is the risk-free rate subtracted in the Sharpe Ratio numerator, and what value did you use?
> **Answer**: "The Sharpe ratio measures excess return per unit of risk. The risk-free rate represents the guaranteed return an investor could earn by holding risk-free US Treasury bills. We must deduct it to isolate the true risk premium generated by equities. I used an annualized risk-free rate of 5.0%, converting it to a daily rate ($0.05 / 252$) before computing daily excess returns."

#### Q4: How does your backtesting engine prevent look-ahead bias?
> **Answer**: "Look-ahead bias occurs when an algorithm uses data from after the rebalancing date to make decisions. In my backtest engine (`src/backtest.py`), whenever the simulation reaches a rebalance date at index $T$, the covariance matrix and weights are calculated using a strict historical slice `log_returns.iloc[:T]`. The optimizer never sees data from index $T$ onward."

#### Q5: What is the mathematical objective of the Risk Parity strategy?
> **Answer**: "Risk Parity aims to equalize the risk contribution of each asset. The risk contribution of asset $i$ is $w_i \times \frac{(\mathbf{\Sigma} \mathbf{w})_i}{\sigma_p}$. The optimizer minimizes the sum of squared differences between all pairwise risk contributions $\sum \sum (\text{RC}_i - \text{RC}_j)^2$ subject to $\sum w_i = 1$ and $w_i \ge 0$."

#### Q6: Why did you choose DuckDB instead of SQLite or a full PostgreSQL server?
> **Answer**: "DuckDB is an in-process, columnar OLAP database optimized for vectorized analytical queries on financial time-series. Unlike SQLite, which is row-oriented and slow on large aggregations, DuckDB executes analytical queries in parallel and integrates with Pandas DataFrames. Unlike PostgreSQL, it requires zero server setup while remaining PostgreSQL-SQL dialect compatible."

#### Q7: Why is Sortino Ratio often preferred over Sharpe Ratio by portfolio managers?
> **Answer**: "The Sharpe Ratio uses total standard deviation in the denominator, penalizing upside volatility (large positive gains) identically to downside crashes. The Sortino Ratio only penalizes downside deviation—returns falling below the risk-free rate—giving a more accurate measure of harmful risk."

#### Q8: How did you model transaction costs, and why are they important?
> **Answer**: "I modeled transaction costs at 10 basis points (0.10%) applied to the total portfolio turnover ($\sum |w_{i, t} - w_{i, t^{-}}|$) on each monthly rebalance. Without transaction costs, a backtest significantly overstates profitability, especially for high-turnover optimization strategies."

#### Q9: What is Maximum Drawdown, and how did your strategies perform during market downturns?
> **Answer**: "Maximum Drawdown is the peak-to-trough percentage decline before a new high is reached. During the 2020 COVID crash and 2022 rate-hike selloff, the S&P 500 experienced an MDD of -33.92%. Equal Weight and Risk Parity limited their maximum drawdowns to -29.44% and -29.48%, recovering faster due to broad sector diversification."

#### Q10: Why did you use SciPy's SLSQP optimizer rather than an unconstrained closed-form solution?
> **Answer**: "The classical unconstrained Markowitz solution ($\mathbf{w} = \frac{\mathbf{\Sigma}^{-1} \mathbf{1}}{\mathbf{1}^T \mathbf{\Sigma}^{-1} \mathbf{1}}$) frequently results in extreme negative weights (short selling) and extreme leverage. Real institutional long-only portfolios must enforce bound constraints ($0 \le w_i \le 1$) and budget constraints ($\sum w_i = 1$). SLSQP (Sequential Least Squares Programming) handles both equality and inequality constraints efficiently."

#### Q11: What is Beta ($\beta$), and what does a Beta of 0.71 for Minimum Variance tell you?
> **Answer**: "Beta measures systematic risk relative to the benchmark. A Beta of 0.71 means that for every 10% move in the S&P 500, the Minimum Variance portfolio is expected to move by only 7.1%. This confirms that the optimization successfully constructed a defensive portfolio with 29% less systematic market risk."

#### Q12: What is the significance of the $\sqrt{252}$ factor when annualizing volatility?
> **Answer**: "Under the assumption of independent and identically distributed (i.i.d.) daily returns, variance scales linearly with time $T$ ($\sigma^2_{\text{annual}} = 252 \times \sigma^2_{\text{daily}}$). Because volatility is the standard deviation (square root of variance), we take the square root of time: $\sigma_{\text{annual}} = \sqrt{252} \times \sigma_{\text{daily}}$."

#### Q13: What happens to covariance matrix estimation as the stock universe grows to 100+ stocks?
> **Answer**: "When $N$ is large relative to the time window $T$, sample covariance matrices suffer from estimation noise and become ill-conditioned or singular. To scale to 100+ stocks, we would implement Ledoit-Wolf shrinkage estimators or factor risk models (like PCA or Fama-French) to regularize the covariance matrix."

#### Q14: How are weights passed to the Power BI and Tableau dashboards?
> **Answer**: "The `src/export_results.py` module transforms internal backtest states into 5 normalized, long-format CSV datasets with human-readable headers and dates. Both Power BI and Tableau connect directly to these CSVs, using relationship models linked on `Strategy` and `Date` dimensions."

#### Q15: What is the primary limitation of this project, and how would you improve it?
> **Answer**: "The primary limitation is survivorship bias in the 12-stock universe (selecting current large-cap leaders) and single-regime static covariance estimation. In future work, I would implement point-in-time constituent universes, Ledoit-Wolf covariance shrinkage, and walk-forward parameter optimization."

---

### 7.4 Intellectual Honesty: Defending Limitations & Future Scale

In quantitative interviews, **interviewers test whether you understand the weaknesses of your models**. Never claim your backtest is perfect. Instead, demonstrate senior-level maturity by proactively stating the limitations and how you would address them in production:

1. **Universe Survivorship Bias**:
   - *Honest Defense*: "The 12 stocks selected were all large, liquid US companies surviving through 2024. In an institutional system, I would use point-in-time historical S&P 500 index constituent snapshots to include companies that were subsequently delisted or acquired."
2. **Simplified Execution & Slippage**:
   - *Honest Defense*: "Our 10 bps transaction cost model captures standard broker commissions and basic bid-ask spread, but does not model nonlinear price impact or market slippage for massive order sizes."
3. **Static Window Covariance vs. Regime Changes**:
   - *Honest Defense*: "Sample covariance gives equal weight to all historical days in the lookback window. In Phase 2, I would incorporate exponentially weighted moving average (EWMA) covariance or GARCH volatility forecasting to respond faster to sudden market volatility spikes."
