"""
returns.py
==========
Functions for computing asset and portfolio returns from price data.

SIMPLE VS LOG RETURNS
----------------------
This project uses BOTH, for different purposes:

  Simple return:   r_t = (P_t - P_{t-1}) / P_{t-1}  = P_t / P_{t-1} - 1
  Log return:      r_t = ln(P_t / P_{t-1})

Simple returns are used for:
  - Portfolio value calculation (dollar P&L)
  - Cumulative return of an equity curve
  - Reporting to stakeholders ("the portfolio returned 12%")
  - Benchmark comparison

Log returns are used for:
  - Covariance matrix estimation (better statistical properties)
  - Annualization (log returns are time-additive)
  - Portfolio optimization inputs

The choice is documented throughout and consistent. For small returns,
simple ? log (since ln(1+x) ? x for small x), so the difference is
minor at the daily horizon.

ANNUALIZATION
-------------
All annualized figures use TRADING_DAYS_PER_YEAR = 252.
  Annualized return  = (1 + cumulative_return)^(252/n_days) - 1
  Annualized vol     = daily_vol ? sqrt(252)
"""

import numpy as np
import pandas as pd
from typing import Union

from src.config import TRADING_DAYS_PER_YEAR


def compute_simple_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """
    Compute daily simple (arithmetic) percentage returns.

    Formula: r_t = P_t / P_{t-1} - 1

    Parameters
    ----------
    prices : pd.DataFrame
        Adjusted close prices with DatetimeIndex and ticker columns

    Returns
    -------
    pd.DataFrame
        Daily simple returns (same shape as prices, first row is NaN ? dropped)
    """
    returns = prices.pct_change()
    # Drop the first row which is always NaN (no previous price)
    return returns.iloc[1:]


def compute_log_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """
    Compute daily log (continuously compounded) returns.

    Formula: r_t = ln(P_t / P_{t-1})

    Log returns have better statistical properties than simple returns:
      - Approximately normally distributed for short horizons
      - Time-additive: sum of daily log returns = period log return
      - Theoretically bounded below at -inf (no leverage blow-up)
    These properties make them the preferred input for covariance
    estimation and mean-variance optimization.

    Parameters
    ----------
    prices : pd.DataFrame
        Adjusted close prices

    Returns
    -------
    pd.DataFrame
        Daily log returns (first row dropped)
    """
    log_returns = np.log(prices / prices.shift(1))
    return log_returns.iloc[1:]


def compute_cumulative_returns(simple_returns: pd.DataFrame) -> pd.DataFrame:
    """
    Compute cumulative returns from simple returns.

    Formula: CR_t = prod_{s=1}^{t} (1 + r_s) - 1

    This answers: "If I invested $1 at the start, what is the total
    percentage gain/loss up to time t?"

    Parameters
    ----------
    simple_returns : pd.DataFrame
        Daily simple returns (not log returns)

    Returns
    -------
    pd.DataFrame
        Cumulative returns starting from 0 at the first observation
    """
    cumulative = (1 + simple_returns).cumprod() - 1
    return cumulative


def compute_annualized_return(
    cumulative_return: float,
    n_trading_days: int,
    trading_days_per_year: int = TRADING_DAYS_PER_YEAR,
) -> float:
    """
    Compute the Compound Annual Growth Rate (CAGR) from a cumulative return.

    Formula: CAGR = (1 + CR)^(252 / T) - 1

    where CR is the total cumulative return and T is the number of trading
    days in the observation period.

    CAGR tells you the equivalent constant annual growth rate that would
    produce the same total return over the same period.

    Parameters
    ----------
    cumulative_return : float
        Total period return as a decimal (e.g., 0.25 = 25%)
    n_trading_days : int
        Number of trading days in the observation period
    trading_days_per_year : int
        Annualization factor (default 252)

    Returns
    -------
    float
        Annualized (CAGR) return as a decimal
    """
    if n_trading_days <= 0:
        raise ValueError("n_trading_days must be positive")

    years = n_trading_days / trading_days_per_year
    cagr = (1 + cumulative_return) ** (1 / years) - 1
    return cagr


def compute_annualized_return_from_series(
    simple_returns: Union[pd.Series, pd.DataFrame],
    trading_days_per_year: int = TRADING_DAYS_PER_YEAR,
) -> Union[float, pd.Series]:
    """
    Compute annualized return directly from a return series.

    Convenience wrapper around compute_annualized_return that
    handles both Series (single asset) and DataFrame (multiple assets).

    Parameters
    ----------
    simple_returns : pd.Series or pd.DataFrame
        Daily simple returns

    Returns
    -------
    float or pd.Series
        Annualized return(s)
    """
    cumulative = (1 + simple_returns).prod() - 1
    n_days = len(simple_returns)
    years = n_days / trading_days_per_year

    return (1 + cumulative) ** (1 / years) - 1


def compute_rolling_returns(
    prices: pd.DataFrame,
    window: int = 21,
) -> pd.DataFrame:
    """
    Compute rolling n-day simple returns.

    Useful for visualizing momentum or medium-term trends without
    the noise of daily returns.

    Parameters
    ----------
    prices : pd.DataFrame
        Adjusted close prices
    window : int
        Rolling window in trading days (e.g., 21 ? 1 month, 63 ? 1 quarter)

    Returns
    -------
    pd.DataFrame
        Rolling returns; first `window` rows will be NaN
    """
    rolling_returns = prices.pct_change(periods=window)
    return rolling_returns


def compute_portfolio_daily_returns(
    weights: np.ndarray,
    asset_returns: pd.DataFrame,
) -> pd.Series:
    """
    Compute the daily return of a portfolio with fixed weights.

    Formula: R_p,t = sum_i w_i * r_i,t  (dot product of weights and returns)

    Note: This assumes weights are constant (buy-and-hold) over the period.
    The backtest engine handles time-varying weights and rebalancing.

    Parameters
    ----------
    weights : np.ndarray
        Portfolio weights, shape (n_assets,), must sum to 1
    asset_returns : pd.DataFrame
        Daily asset returns, shape (n_days, n_assets)

    Returns
    -------
    pd.Series
        Daily portfolio returns with the same DatetimeIndex
    """
    # Reorder columns to match the order of weights
    weights_array = np.array(weights)

    # Dot product: each day's portfolio return = sum of w_i * r_i
    portfolio_returns = asset_returns.values @ weights_array
    return pd.Series(portfolio_returns, index=asset_returns.index, name="Portfolio")


def build_return_summary(
    prices: pd.DataFrame,
    trading_days_per_year: int = TRADING_DAYS_PER_YEAR,
) -> pd.DataFrame:
    """
    Build a summary table of key return statistics per asset.

    Includes: total return, CAGR, annualized volatility, best/worst day.

    Parameters
    ----------
    prices : pd.DataFrame
        Clean adjusted close prices

    Returns
    -------
    pd.DataFrame
        Summary statistics, one row per ticker
    """
    simple_rets = compute_simple_returns(prices)
    log_rets = compute_log_returns(prices)

    summary_rows = []
    for ticker in prices.columns:
        r = simple_rets[ticker].dropna()
        total_ret = float((1 + r).prod() - 1)
        n_days = len(r)
        cagr = compute_annualized_return(total_ret, n_days, trading_days_per_year)
        ann_vol = float(r.std() * np.sqrt(trading_days_per_year))

        summary_rows.append({
            "Ticker": ticker,
            "Total Return": round(total_ret, 4),
            "CAGR": round(cagr, 4),
            "Ann. Volatility": round(ann_vol, 4),
            "Best Day": round(float(r.max()), 4),
            "Worst Day": round(float(r.min()), 4),
            "N Trading Days": n_days,
        })

    return pd.DataFrame(summary_rows).set_index("Ticker")
