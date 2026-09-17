# Interview Questions

## A. Project Architecture
1. Walk me through the architecture of your quantitative backtesting platform.
2. Why did you choose a modular 10-file architecture instead of a single script or a Jupyter Notebook?
3. Explain the data flow from raw price download to final risk metric generation.
4. How does your architecture enforce the separation of concerns between strategy logic and the backtesting engine?
5. If I asked you to add a new Mean-Reversion strategy to this platform, which files would you need to modify?

## B. Python Implementation
6. Why did you choose Python for this project over C++ or R?
7. Explain how you handled object state or data passing between your modules without creating tight coupling.
8. What is the role of `scipy.optimize` in your project, and how does `SLSQP` work conceptually?
9. How did you structure your configuration (`config.py`), and why is hardcoding parameters in functions a bad practice?
10. If this code were moving to production, how would you improve the error handling and logging?

## C. Pandas / NumPy
11. Why use NumPy arrays for the optimization math instead of standard Python lists or Pandas DataFrames?
12. Explain the difference between `.loc` and `.iloc` and where you used them in your backtester.
13. How did you handle missing data (NaNs) in your price time-series, and why did you choose that specific method?
14. Vectorization is crucial in Pandas. Can you give an example of where you avoided a `for` loop by using vectorized operations?

## D. SQL and DuckDB
15. Why did you choose DuckDB over SQLite or PostgreSQL for this specific project?
16. What is a columnar database, and why is it vastly superior for financial time-series data?
17. Walk me through the schema design you used to store the portfolio weights and daily returns.
18. If your dataset grew to 100 GB, how would your database interaction strategy change?

## E. Portfolio Optimization
19. What is the mathematical objective function of the Minimum Variance portfolio?
20. Explain Risk Parity. How does it differ from Equal Weight and Minimum Variance?
21. What is a covariance matrix, and how does your code calculate it?
22. Why do optimizers often act as "error-maximizers," and how does this affect portfolio weights?
23. In your optimizer, what constraints did you apply? (e.g., long-only, fully invested).
24. How would you handle a non-positive definite covariance matrix in your optimization step?

## F. Risk Metrics
25. Define the Sharpe Ratio and the Sortino Ratio. Why might a fund manager prefer Sortino?
26. How did you calculate Maximum Drawdown programmatically in Pandas?
27. What is Tracking Error, and why is it important when comparing against the S&P 500?
28. Explain Beta. If your Min Variance portfolio has a Beta of 0.6, what does that mean practically?
29. Why must volatility and returns be annualized, and what is the math behind annualizing daily data?

## G. Backtesting
30. What is Look-Ahead bias, and exactly how does your architecture prevent it during the estimation phase?
31. Explain your transaction cost model. Why is assuming 0 friction dangerous?
32. What is survivorship bias, and does your backtest suffer from it?
33. Walk me through the mechanics of your monthly rebalancing logic.
34. How did you align the benchmark (S&P 500) returns with your portfolio returns to ensure a fair comparison?
35. What is the difference between log returns and simple returns, and where did you use each in the backtest?

## H. Quantitative Finance
36. What is the core premise of Modern Portfolio Theory (Markowitz)?
37. Why do we look at correlation when selecting assets for a portfolio?
38. What is the difference between systematic risk and idiosyncratic risk? Which one does diversification eliminate?
39. What is the risk-free rate, and what proxy did you use in your metrics?
40. Why are asset returns generally not normally distributed, and why is that a problem for SLSQP optimization?

## I. Data Quality
41. What is the difference between Close and Adjusted Close prices, and why must you use Adjusted Close?
42. If a stock undergoes a 2-for-1 split, how does that affect historical data pipelines?
43. What are the limitations of using Yahoo Finance data for quantitative research?

## J. Power BI
44. How did you structure the CSV extracts so they were optimized for Power BI ingestion?
45. In Power BI, how would you design a dashboard to compare the 3 strategies effectively?

## K. Tableau
46. If visualizing this in Tableau, how would you handle the time-series granularity (daily vs monthly)?
47. How would you build an interactive parameter in Tableau to let a user change the risk-free rate dynamically?

## L. Limitations and Weaknesses
48. What is the biggest flaw or limitation in your current backtesting methodology?
49. Your model assumes zero market impact. Explain what market impact is and when it becomes a problem.
50. How would trading real money differ from the results seen in this platform?

## M. Scalability and Future Work
51. If you had to scale this from 12 stocks to 500 stocks, what would break first?
52. How would you implement a "shrinkage estimator" in Phase 2, and why is it necessary?
53. What alternative data sources or alpha signals would you add to this project next?
