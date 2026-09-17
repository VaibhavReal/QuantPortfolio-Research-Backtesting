# Future Improvements Roadmap

## Scale Phases

### Phase 1: Current (10-15 Stocks)
*   **Status:** Functional, modular architecture. Standard optimization (SLSQP), basic sample covariance.
*   **Why:** Perfect for demonstrating core financial concepts, ensuring the mathematical pipelines work, and validating the backtester logic without extreme computational overhead.

### Phase 2: Medium Scale (25-50 Stocks)
*   **Requirement:** As N grows relative to T (time window), the sample covariance matrix degrades.
*   **Upgrades:**
    *   Implement **Ledoit-Wolf Shrinkage** for the covariance matrix.
    *   Transition data pipeline to handle API rate limits gracefully (batching, caching).
    *   Implement basic sector constraints (e.g., max 30% Tech) in the optimizer.

### Phase 3: Institutional Scale (100+ Stocks)
*   **Requirement:** Computational bottlenecks and memory limits.
*   **Upgrades:**
    *   Switch optimizer from `scipy.optimize` (SLSQP) to a dedicated convex solver like **OSQP** or **CVXPY**.
    *   Implement parallel processing (`multiprocessing` or `concurrent.futures`) for backtest loops.
    *   Migrate data storage to **Polars** for faster out-of-core data frame operations before DuckDB ingestion.

---

## Feature-Level Roadmap

### 1. Portfolio Optimization
*   **Black-Litterman Model:** Incorporate investor views rather than relying solely on historical returns.
*   **Efficient Frontier Generation:** Plot the full curve and locate the Maximum Sharpe point.
*   **Constraints:** Add turnover limits (e.g., max 10% change per month) to reduce transaction costs.
*   **Constraints:** Add sector and cardinality constraints (e.g., "hold exactly 20 stocks").

### 2. Risk Management
*   **CVaR Optimization:** Optimize for Conditional Value at Risk (Expected Shortfall) instead of just variance, better accounting for fat-tailed market crashes.
*   **Volatility Targeting:** Dynamically adjust cash vs. equity allocation to maintain a constant 10% portfolio volatility.
*   **Factor Exposure Limits:** Ensure the portfolio isn't accidentally 100% correlated to the Value or Growth factor.

### 3. Factor Models
*   **Fama-French:** Decompose portfolio returns using the Fama-French 3 or 5 factor models.
*   **Alpha Generation:** Implement Momentum, Value, and Quality signals instead of just historical returns.

### 4. Data Pipeline
*   **Alternative Data:** Move away from Yahoo Finance to professional APIs (Tiingo, Alpaca, Polygon).
*   **Point-in-Time Data:** Ensure financial statements and index membership data reflect what was actually known on that exact date, preventing survivorship bias.
*   **Corporate Actions:** Build robust handling for mergers, spin-offs, and special dividends.

### 5. Backtesting Engine
*   **Walk-Forward Optimization:** Continuously train and test parameters dynamically over time to prove robustness.
*   **Monte Carlo Simulation:** Run thousands of randomized price paths to test the strategy under conditions that haven't happened yet.
*   **Regime Detection:** Use Hidden Markov Models (HMM) to detect Bull/Bear/High-Vol regimes and swap strategies dynamically.

### 6. Infrastructure & Engineering
*   **PostgreSQL Migration:** Move from DuckDB to a hosted PostgreSQL instance for concurrent web access.
*   **REST API:** Build a FastAPI layer to serve portfolio weights and risk metrics to a frontend.
*   **Dockerization:** Containerize the entire pipeline for one-click deployment.

### 7. Analytics & ML
*   **Volatility Forecasting:** Replace historical sample variance with GARCH(1,1) models to forecast future volatility.
*   **Return Forecasting:** Experiment with Tree-based ML models (XGBoost/LightGBM) to forecast expected returns.

### 8. Reporting
*   **Automated PDF Generation:** Generate tear-sheets (like Quantopian's pyfolio or Alphalens) automatically at month-end.
*   **Alerting:** Set up email/Slack notifications when portfolio drift exceeds a threshold.
