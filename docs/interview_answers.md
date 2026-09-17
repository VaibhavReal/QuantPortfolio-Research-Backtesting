# Interview Answers

## A. Project Architecture
**1. Walk me through the architecture of your quantitative backtesting platform.**
The platform is built on a 10-module pipeline. It starts with `data_loader` fetching Yahoo Finance data, passes it to `data_cleaning` and `returns` for preprocessing. A daily step-forward loop in `backtest` calls the `optimization` module monthly to generate weights via SLSQP, updates the `portfolio` accounting for transaction costs, calculates analytics in `risk_metrics`, and saves everything to a `database` for BI export.

**2. Why did you choose a modular 10-file architecture instead of a single script or a Jupyter Notebook?**
Notebooks are great for EDA but terrible for production software due to hidden state and non-linear execution. A modular architecture ensures separation of concerns, allows for unit testing individual components (like the optimizer), and makes the codebase scalable and maintainable.

**3. Explain the data flow from raw price download to final risk metric generation.**
Raw prices -> Cleaned Prices -> Log/Simple Returns. The backtest loop feeds trailing log returns to the optimizer to get weights. These weights are applied to simple returns to generate a daily portfolio equity curve. Finally, the total equity curve is compared against the S&P 500 curve to generate Sharpe, MDD, and Beta.

**4. How does your architecture enforce the separation of concerns between strategy logic and the backtesting engine?**
The `backtest.py` engine is completely strategy-agnostic. It simply expects an `optimization` function that takes a covariance matrix and returns a weight array. This means I can add any complex math strategy to `optimization.py` without rewriting the core simulation loop.

**5. If I asked you to add a new Mean-Reversion strategy to this platform, which files would you need to modify?**
I would only need to add the mathematical logic to `optimization.py` as a new function, and then add the strategy string name to `config.py` and the execution loop in `main.py`. The data loading, backtesting, and database layers would require zero changes.

## B. Python Implementation
**6. Why did you choose Python for this project over C++ or R?**
Python is the industry standard for quantitative research due to the rich ecosystem of `pandas`, `numpy`, and `scipy`. While C++ is used for high-frequency execution, Python is unparalleled for fast prototyping, vectorized backtesting, and data manipulation.

**7. Explain how you handled object state or data passing between your modules without creating tight coupling.**
I passed standard Pandas DataFrames and NumPy arrays between functions rather than creating complex custom classes that inherit from one another. This functional programming approach keeps functions pure and easily testable.

**8. What is the role of scipy.optimize in your project, and how does SLSQP work conceptually?**
`scipy.optimize` minimizes a mathematical objective function subject to constraints. SLSQP (Sequential Least SQuares Programming) works by approximating the objective function (like portfolio variance) as a quadratic function and taking iterative steps downhill until it finds the global minimum, ensuring weights sum to 1 and are >= 0.

**9. How did you structure your configuration (config.py), and why is hardcoding parameters in functions a bad practice?**
`config.py` holds global variables like `TICKERS`, `START_DATE`, `RISK_FREE_RATE`, and `DB_PATH`. Hardcoding these inside functions creates technical debt, requiring a developer to hunt through 10 files just to change the transaction cost assumption.

**10. If this code were moving to production, how would you improve the error handling and logging?**
I would replace `print()` statements with Python's built-in `logging` module, writing to rotating log files with timestamped `INFO` and `ERROR` levels. I would also add `try-except` blocks around API calls (like Yahoo Finance) with exponential backoff retries.

## C. Pandas / NumPy
**11. Why use NumPy arrays for the optimization math instead of standard Python lists or Pandas DataFrames?**
NumPy is written in C and handles matrix operations (like dot products and matrix inversion) orders of magnitude faster than Python lists. While Pandas is great for time-series alignment, NumPy is required for the heavy linear algebra in portfolio optimization.

**12. Explain the difference between .loc and .iloc and where you used them in your backtester.**
`.loc` is label-based indexing (e.g., finding data for '2023-01-01'), while `.iloc` is integer-based indexing (e.g., finding row 5). I used `.loc` extensively to slice the historical price DataFrame perfectly up to the rebalance date to prevent look-ahead bias.

**13. How did you handle missing data (NaNs) in your price time-series, and why did you choose that specific method?**
I used `.ffill()` (forward fill) first. If a stock didn't trade on Tuesday, Wednesday's open assumes Tuesday's closing price. I strictly avoid interpolating prices, because interpolating uses future data to guess past data, causing data leakage.

**14. Vectorization is crucial in Pandas. Can you give an example of where you avoided a for loop by using vectorized operations?**
Instead of looping through every day to calculate returns `(price[t] - price[t-1])/price[t-1]`, I used the vectorized Pandas function `df.pct_change()`, which computes the entire time series in C instantly.

## D. SQL and DuckDB
**15. Why did you choose DuckDB over SQLite or PostgreSQL for this specific project?**
DuckDB is an in-process OLAP (analytical) database. It is drastically faster than SQLite for column-heavy aggregations (like querying specific stock returns across millions of rows) and requires zero server configuration, unlike PostgreSQL, making it perfect for desktop quant research.

**16. What is a columnar database, and why is it vastly superior for financial time-series data?**
A row-based DB stores a full day's record (date, AAPL, MSFT, JPM) together. A columnar DB stores all of AAPL's history contiguously in memory. Since quantitative analysis usually involves running math on a whole column (like calculating variance of AAPL), columnar databases avoid loading irrelevant data, yielding massive speedups.

**17. Walk me through the schema design you used to store the portfolio weights and daily returns.**
I used a normalized time-series schema. The `daily_returns` table has `(date, strategy_name, portfolio_return)`. The `weights` table has `(date, strategy_name, ticker, weight)`. This allows easy SQL grouping by strategy or ticker for dashboarding.

**18. If your dataset grew to 100 GB, how would your database interaction strategy change?**
I could no longer load the entire DuckDB query into a Pandas DataFrame in RAM. I would rely on DuckDB's out-of-core execution engine to perform the aggregations directly on disk, and only pull the summarized results (like monthly averages) into Python.

## E. Portfolio Optimization
**19. What is the mathematical objective function of the Minimum Variance portfolio?**
The objective function is `min w^T * Sigma * w`, where `w` is the vector of asset weights and `Sigma` is the covariance matrix. We minimize this subject to `sum(w) = 1` and `w >= 0`.

**20. Explain Risk Parity. How does it differ from Equal Weight and Minimum Variance?**
Equal Weight allocates equal capital ($10 to each). Min Variance minimizes total portfolio volatility. Risk Parity allocates capital so that every asset contributes the exact same amount of *volatility* to the portfolio. It holds more of low-risk assets and less of high-risk assets.

**21. What is a covariance matrix, and how does your code calculate it?**
A covariance matrix measures how asset returns move together. The diagonal is variance, the off-diagonals are covariances. My code calculates it using `pandas.DataFrame.cov()` applied to a trailing 252-day window of log returns.

**22. Why do optimizers often act as "error-maximizers," and how does this affect portfolio weights?**
Sample covariance matrices contain statistical noise. SLSQP blindly trusts this matrix and will heavily overweight assets that randomly showed spuriously low variance or negative correlation in the sample. It maximizes the impact of estimation errors.

**23. In your optimizer, what constraints did you apply? (e.g., long-only, fully invested).**
I applied two constraints: Fully invested (`np.sum(w) == 1`), meaning no leverage and no idle cash; and Long-only (`w_i >= 0`), meaning no short selling.

**24. How would you handle a non-positive definite covariance matrix in your optimization step?**
A non-PD matrix means the optimizer might find a mathematically impossible "negative risk" portfolio and crash. I would fix it using `numpy.linalg.eig` to find negative eigenvalues and set them to a small positive number, or use a shrinkage estimator like Ledoit-Wolf.

## F. Risk Metrics
**25. Define the Sharpe Ratio and the Sortino Ratio. Why might a fund manager prefer Sortino?**
Sharpe is `(Return - RiskFree) / Total Volatility`. Sortino is `(Return - RiskFree) / Downside Volatility`. Managers prefer Sortino because investors do not view upside volatility (massive sudden gains) as risk; they only fear downside drawdowns.

**26. How did you calculate Maximum Drawdown programmatically in Pandas?**
First, calculate the running maximum of the cumulative equity curve using `cummax()`. Then, divide the current equity value by the running max and subtract 1. The minimum value of this resulting series is the Maximum Drawdown.

**27. What is Tracking Error, and why is it important when comparing against the S&P 500?**
Tracking error is the standard deviation of the *difference* between the portfolio returns and the benchmark returns. It measures how much the portfolio deviates from the market. Active managers use it to prove they aren't just "closet indexing."

**28. Explain Beta. If your Min Variance portfolio has a Beta of 0.6, what does that mean practically?**
Beta measures market sensitivity (`Cov(R_p, R_m) / Var(R_m)`). A Beta of 0.6 means that if the S&P 500 drops 10%, the Min Variance portfolio is expected to drop only 6%. It is less volatile than the broader market.

**29. Why must volatility and returns be annualized, and what is the math behind annualizing daily data?**
Metrics must be annualized so they can be compared universally. Daily returns are annualized by multiplying by 252 (trading days). Daily volatility is annualized by multiplying by `sqrt(252)` because variance scales linearly with time, so standard deviation scales with the square root of time.

## G. Backtesting
**30. What is Look-Ahead bias, and exactly how does your architecture prevent it during the estimation phase?**
Look-ahead bias is using future data to make past decisions. I prevent it by strict array slicing: weights applied to Month M's returns are calculated using a covariance matrix generated strictly from data up to the final day of Month M-1.

**31. Explain your transaction cost model. Why is assuming 0 friction dangerous?**
I deduct 10 bps (0.1%) of the gross dollar amount traded during each monthly rebalance. Assuming zero friction makes high-turnover strategies look falsely profitable, as real-world trading bleeds capital through bid-ask spreads and commissions.

**32. What is survivorship bias, and does your backtest suffer from it?**
Survivorship bias is testing only on companies that survived to the present day. Yes, my backtest suffers from it because I selected 12 currently successful large-cap stocks. If I ran this in 2005, I should have included companies that eventually went bankrupt to be perfectly realistic.

**33. Walk me through the mechanics of your monthly rebalancing logic.**
On the last business day of the month, the code calculates new target weights. It calculates the difference between the drifted current weights and target weights, calculates the dollar value traded, deducts 10 bps transaction costs from the capital pool, and sets the portfolio to the new weights for the next month.

**34. How did you align the benchmark (S&P 500) returns with your portfolio returns to ensure a fair comparison?**
I downloaded `^GSPC` data over the exact same date range, forward-filled any missing index days to match the stock calendar, and started the index equity curve at $1.0 on the exact same start date as the backtest.

**35. What is the difference between log returns and simple returns, and where did you use each in the backtest?**
Log returns `ln(P_t / P_t-1)` are time-additive and used for the covariance matrix calculation. Simple returns `(P_t - P_t-1) / P_t-1` are cross-sectionally additive and used to calculate the actual dollar growth of the portfolio daily.

## H. Quantitative Finance
**36. What is the core premise of Modern Portfolio Theory (Markowitz)?**
Investors are rational and risk-averse. Therefore, you shouldn't just pick stocks with high expected returns; you should combine assets with low correlations to maximize expected return for a given level of variance (risk).

**37. Why do we look at correlation when selecting assets for a portfolio?**
Because combining assets with correlation < 1.0 reduces total portfolio variance. The lower the correlation, the greater the diversification benefit. If everything is perfectly correlated (+1.0), there is no diversification.

**38. What is the difference between systematic risk and idiosyncratic risk? Which one does diversification eliminate?**
Systematic risk is market-wide risk (e.g., interest rate hikes, recessions). Idiosyncratic risk is company-specific risk (e.g., a CEO scandal). Diversification entirely eliminates idiosyncratic risk, leaving only systematic risk.

**39. What is the risk-free rate, and what proxy did you use in your metrics?**
The risk-free rate is the theoretical return of an investment with zero risk, usually represented by US Treasury yields. I used a static assumption of 5% (0.05) annualized to calculate the Sharpe and Sortino ratios.

**40. Why are asset returns generally not normally distributed, and why is that a problem for SLSQP optimization?**
Financial returns have "fat tails"—extreme events (like a 10% daily drop) happen far more often than a normal bell curve predicts. SLSQP minimizes variance based on a normal distribution assumption, meaning it severely underestimates the risk of black swan tail events.

## I. Data Quality
**41. What is the difference between Close and Adjusted Close prices, and why must you use Adjusted Close?**
Close is the final traded price. Adjusted Close modifies historical prices downward to account for dividends and stock splits. You must use Adjusted Close to calculate Total Return; otherwise, a stock split looks like a 50% crash in your backtest.

**42. If a stock undergoes a 2-for-1 split, how does that affect historical data pipelines?**
Without adjustment, the price drops by half, generating a false -50% daily return. Data vendors fix this by dividing all historical prices prior to the split by 2, ensuring the calculated daily return on the day of the split is based purely on market movement.

**43. What are the limitations of using Yahoo Finance data for quantitative research?**
It lacks point-in-time accuracy (meaning it silently corrects historical errors, introducing look-ahead bias), it frequently misses dividends, and it suffers from API rate limiting. Professional desks use CRSP or Bloomberg.

## J. Power BI
**44. How did you structure the CSV extracts so they were optimized for Power BI ingestion?**
I exported "long" format (unpivoted) tables. For example, `(Date, Strategy, Metric_Name, Value)`. Power BI handles long, tabular data much better than wide formats, allowing for easy slicing and filtering by Strategy in DAX.

**45. In Power BI, how would you design a dashboard to compare the 3 strategies effectively?**
I would use a primary Line Chart plotting the cumulative equity curves of the 3 strategies + S&P 500 over time. Below it, a Matrix table showing Sharpe, MDD, and CAGR. I would add a Date Slicer to allow users to zoom in on specific market crashes (e.g., March 2020).

## K. Tableau
**46. If visualizing this in Tableau, how would you handle the time-series granularity (daily vs monthly)?**
I would load the daily equity curves but use Tableau's built-in date hierarchy to allow users to drill up to monthly or quarterly aggregation, using a `LOD` (Level of Detail) expression to capture the final closing price of each period.

**47. How would you build an interactive parameter in Tableau to let a user change the risk-free rate dynamically?**
I would create a Float Parameter called `[Risk Free Rate]`, display it as a slider, and write a Calculated Field for Sharpe Ratio: `([CAGR] - [Risk Free Rate]) / [Volatility]`. The dashboard would update in real-time as the user moves the slider.

## L. Limitations and Weaknesses
**48. What is the biggest flaw or limitation in your current backtesting methodology?**
The assumption of perfect execution with zero market impact and zero slippage, combined with the survivorship bias of picking 12 currently successful stocks.

**49. Your model assumes zero market impact. Explain what market impact is and when it becomes a problem.**
Market impact is the price movement caused by your own trading. If I try to buy 1 million shares of a stock, I eat through the order book, driving the price up. My average fill price is worse than the initial quote. It limits the total AUM a strategy can handle.

**50. How would trading real money differ from the results seen in this platform?**
Real money experiences bid-ask spreads, broker commissions, taxes, emotional psychology causing manual intervention, and execution delays. Backtests are always optimistic upper bounds of actual performance.

## M. Scalability and Future Work
**51. If you had to scale this from 12 stocks to 500 stocks, what would break first?**
The sample covariance matrix calculation would become noisy and ill-conditioned, causing the SLSQP optimizer to produce wildly unstable, extreme weights. Also, Yahoo Finance would rate-limit the downloads.

**52. How would you implement a "shrinkage estimator" in Phase 2, and why is it necessary?**
I would use `sklearn.covariance.LedoitWolf`. It blends the noisy sample covariance matrix with a highly structured target matrix (like an identity matrix). It is necessary because as N (stocks) approaches T (time days), sample covariance matrices mathematically break down and become non-invertible.

**53. What alternative data sources or alpha signals would you add to this project next?**
I would integrate the Fama-French factors (Value, Size, Momentum) to see if my strategies are just capturing factor premia. I might also add a volatility-targeting overlay using a GARCH model to dynamically reduce exposure during market crashes.

---

## EXPLAIN THIS PROJECT IN 60 SECONDS
"My project is a quantitative portfolio research and backtesting platform built in Python. I designed a modular engine to simulate how different optimization strategies—specifically Equal Weight, Minimum Variance, and Risk Parity—would have performed on a basket of US large-cap stocks against the S&P 500 over the last 5 years. I built the data pipeline using Pandas, performed the mathematical optimization using SciPy's SLSQP solver, and rigorously modeled real-world constraints like monthly rebalancing and transaction costs. The results are stored in a columnar DuckDB database for fast analytical querying. Ultimately, the project demonstrates how mathematical risk allocation, like minimizing covariance or equalizing risk contribution, can construct portfolios with significantly lower drawdowns and better risk-adjusted returns than a naive benchmark."

## EXPLAIN THIS PROJECT IN 3 MINUTES
"This project is a complete quantitative research and backtesting environment built from scratch in Python. The goal was to programmatically evaluate how mathematical portfolio optimization compares to naive benchmarks like the S&P 500, not just in theory, but in a realistic historical simulation.

I implemented three core strategies: a baseline Equal Weight portfolio, a Minimum Variance portfolio that minimizes total portfolio volatility using quadratic programming, and a Risk Parity portfolio designed so that every asset contributes equally to the total portfolio variance.

The architecture is fully modular. The data pipeline pulls and cleans daily prices using Pandas. At the end of every simulated month, the engine calculates a trailing 252-day covariance matrix. To prevent look-ahead bias, I ensure the optimizer only ever sees data available up to that exact rebalance date. It uses SciPy's SLSQP solver to calculate the new optimal weights. The backtester then applies these weights to the forward month's returns, strictly deducting 10 basis points for transaction costs based on the gross turnover of the rebalance.

The results showed that while the benchmark S&P 500 might have higher absolute returns during massive bull runs, the Minimum Variance and Risk Parity strategies achieved significantly higher Sharpe and Sortino ratios. More importantly, they drastically reduced Maximum Drawdown during market shocks like 2020 and 2022, proving the value of quantitative risk management. 

One of the key technical challenges was matrix instability. When calculating covariance, the optimizer acts as an error-maximizer—it aggressively overweights assets with spuriously low historical variance. I had to ensure the covariance matrix was properly conditioned and strictly enforce fully-invested and long-only constraints so the solver wouldn't fail. I also optimized the data storage by using DuckDB, a columnar database that handles time-series aggregations much faster than SQLite, allowing me to easily export the risk metrics to Power BI.

If I were to take this to Phase 2, I would scale the universe from 12 stocks to 500. To do that, I would need to implement Ledoit-Wolf shrinkage on the covariance matrix to handle the noise, switch from Yahoo Finance to an institutional data provider, and migrate the optimization engine to a dedicated convex solver like OSQP. Ultimately, this project provided me with deep hands-on experience in financial data engineering, linear algebra, and the strict mechanics of realistic backtesting."
