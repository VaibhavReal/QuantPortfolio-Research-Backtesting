"""
benchmark.py
============
Benchmark data handling and strategy comparison.

The benchmark (S&P 500 via ^GSPC) serves as the reference portfolio
against which all three strategies are evaluated. Comparing to a
benchmark is essential because it answers the question:

  "Did my strategy actually add value, or did the market just go up?"

A strategy that returns 15% in a year where the S&P 500 returned 25%
has underperformed despite being nominally profitable.

FAIR COMPARISON REQUIREMENTS
------------------------------
For a benchmark comparison to be fair:
  1. Same date range
  2. Same starting capital
  3. Same return measurement methodology
  4. Same annualization convention
  5. Risk-free rate used consistently

All of these are enforced here.
"""

import numpy as np
import pandas as pd
from typing import Dict

from src.config import (
    BENCHMARK_TICKER,
    BENCHMARK_NAME,
    RISK_FREE_RATE,
    TRADING_DAYS_PER_YEAR,
    INITIAL_CAPITAL,
)
from src.data_loader import get_benchmark_data
from src.returns import compute_simple_returns
from src.risk_metrics import compute_all_metrics


def load_and_prepare_benchmark(
    prices: pd.DataFrame,
    start: str = None,
    end: str = None,
) -> pd.Series:
    """
    Load benchmark prices and align them to the portfolio date index.

    We align the benchmark to the same trading dates as the portfolio.
    This ensures fair comparison: we use identical date ranges.

    Parameters
    ----------
    prices : pd.DataFrame
        Clean portfolio asset prices (used for date alignment)
    start : str
        Start date override (optional)
    end : str
        End date override (optional)

    Returns
    -------
    pd.Series
        Benchmark daily simple returns, aligned to portfolio dates
    """
    # Get benchmark prices
    benchmark_prices = get_benchmark_data()

    # Compute simple returns
    benchmark_returns = benchmark_prices.pct_change().dropna()
    benchmark_returns.name = BENCHMARK_NAME

    # Align to the portfolio's date index
    portfolio_dates = compute_simple_returns(prices).index
    benchmark_returns = benchmark_returns.reindex(portfolio_dates)

    # Fill any remaining gaps with 0 (holiday mismatches between instruments)
    n_filled = benchmark_returns.isna().sum()
    if n_filled > 0:
        print(f"  Benchmark: filled {n_filled} missing dates with 0.")
    benchmark_returns = benchmark_returns.fillna(0)

    return benchmark_returns


def build_benchmark_equity_curve(
    benchmark_returns: pd.Series,
    initial_capital: float = INITIAL_CAPITAL,
) -> pd.Series:
    """
    Build a cumulative equity curve for the benchmark.

    Parameters
    ----------
    benchmark_returns : pd.Series
        Daily benchmark simple returns
    initial_capital : float
        Starting value

    Returns
    -------
    pd.Series
        Benchmark equity curve in dollars, same length as benchmark_returns
    """
    equity = initial_capital * (1 + benchmark_returns).cumprod()
    equity.name = BENCHMARK_NAME
    return equity


def compute_benchmark_metrics(
    benchmark_returns: pd.Series,
    risk_free_rate: float = RISK_FREE_RATE,
    trading_days_per_year: int = TRADING_DAYS_PER_YEAR,
    initial_capital: float = INITIAL_CAPITAL,
) -> Dict[str, float]:
    """
    Compute standard risk/performance metrics for the benchmark.

    Parameters
    ----------
    benchmark_returns : pd.Series
        Daily benchmark simple returns
    risk_free_rate : float
        Annual risk-free rate
    trading_days_per_year : int
        252
    initial_capital : float
        Starting capital (for equity curve)

    Returns
    -------
    dict
        Metrics dict matching the format of compute_all_metrics()
    """
    equity_curve = build_benchmark_equity_curve(benchmark_returns, initial_capital)
    # Benchmark vs itself: beta = 1, tracking error = 0
    metrics = compute_all_metrics(
        equity_curve=equity_curve,
        daily_returns=benchmark_returns,
        benchmark_returns=benchmark_returns,
        strategy_name=BENCHMARK_NAME,
        risk_free_rate=risk_free_rate,
        trading_days_per_year=trading_days_per_year,
    )
    # Override Beta to 1.0 (by definition)
    metrics["Beta"] = 1.0
    # Override Tracking Error to 0.0 (by definition)
    metrics["Tracking Error"] = 0.0

    return metrics


def build_comparison_table(
    all_metrics: Dict[str, Dict],
) -> pd.DataFrame:
    """
    Build a combined performance comparison table.

    Parameters
    ----------
    all_metrics : dict
        {strategy_name: metrics_dict} for each strategy + benchmark

    Returns
    -------
    pd.DataFrame
        Comparison DataFrame with one row per strategy/benchmark
    """
    rows = list(all_metrics.values())
    df = pd.DataFrame(rows)

    # Format as percentages for readability in terminal output
    pct_cols = ["Total Return", "CAGR", "Ann. Volatility", "Max Drawdown", "Tracking Error"]
    display_df = df.copy()
    for col in pct_cols:
        if col in display_df.columns:
            display_df[col] = display_df[col].apply(
                lambda x: f"{x:.2%}" if pd.notna(x) else "N/A"
            )

    ratio_cols = ["Sharpe Ratio", "Sortino Ratio", "Beta", "Calmar Ratio"]
    for col in ratio_cols:
        if col in display_df.columns:
            display_df[col] = display_df[col].apply(
                lambda x: f"{x:.2f}" if pd.notna(x) else "N/A"
            )

    return df, display_df


def run_benchmark_comparison(
    backtest_results: Dict[str, Dict],
    benchmark_returns: pd.Series,
    risk_free_rate: float = RISK_FREE_RATE,
) -> pd.DataFrame:
    """
    Full benchmark comparison: compute metrics for all strategies + benchmark.

    Parameters
    ----------
    backtest_results : dict
        Output of backtest.run_all_strategies()
    benchmark_returns : pd.Series
        Daily benchmark simple returns
    risk_free_rate : float
        Annual risk-free rate

    Returns
    -------
    pd.DataFrame (raw)
        One row per strategy + benchmark, all metrics as floats
    """
    all_metrics = {}

    # Compute metrics for each strategy
    for strategy_name, result in backtest_results.items():
        metrics = compute_all_metrics(
            equity_curve=result["portfolio_values"],
            daily_returns=result["daily_returns"],
            benchmark_returns=benchmark_returns,
            strategy_name=strategy_name,
            risk_free_rate=risk_free_rate,
        )
        all_metrics[strategy_name] = metrics

    # Compute benchmark metrics
    benchmark_equity = build_benchmark_equity_curve(benchmark_returns)
    benchmark_metrics = compute_benchmark_metrics(benchmark_returns)
    all_metrics[BENCHMARK_NAME] = benchmark_metrics

    raw_df, display_df = build_comparison_table(all_metrics)

    # Print the comparison table
    print("\n  --- Strategy vs Benchmark Comparison ---------------------")
    print(display_df.to_string(index=False))
    print("  -----------------------------------------------------------\n")

    return raw_df
