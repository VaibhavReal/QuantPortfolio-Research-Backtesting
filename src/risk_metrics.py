"""
risk_metrics.py
===============
Portfolio risk and performance measurement.

All metrics are implemented from first principles (no black-box library calls).
Formulas are included in docstrings so this file can serve as a reference
during technical interviews.

METRIC OVERVIEW
---------------
1. Sharpe Ratio        -- return per unit of total risk
2. Sortino Ratio       -- return per unit of downside risk
3. Maximum Drawdown    -- worst peak-to-trough decline
4. Annualized Volatility -- standard deviation of returns, annualized
5. Beta                -- sensitivity to market movements
6. CAGR                -- compound annual growth rate
7. Calmar Ratio        -- CAGR divided by max drawdown
8. Downside Deviation  -- volatility of negative returns only
9. Tracking Error      -- volatility of return difference vs benchmark

RISK-FREE RATE
--------------
All Sharpe/Sortino calculations use the risk-free rate from config.py.
This is specified as an annual rate and is converted to a daily rate
for daily return calculations:

    daily_rf = (1 + annual_rf)^(1/252) - 1  ?  annual_rf / 252
"""

import numpy as np
import pandas as pd
from typing import Dict, Optional, Union

from src.config import TRADING_DAYS_PER_YEAR, RISK_FREE_RATE


def annualized_volatility(
    returns: Union[pd.Series, np.ndarray],
    trading_days_per_year: int = TRADING_DAYS_PER_YEAR,
) -> float:
    """
    Compute annualized portfolio volatility.

    Formula: sigma_annual = sigma_daily * sqrt(T)

    where T = 252 trading days per year.

    This relies on the assumption that daily returns are i.i.d.
    (independently and identically distributed). For actual financial
    returns this is an approximation, but it's the industry standard.

    Parameters
    ----------
    returns : pd.Series or np.ndarray
        Daily simple returns
    trading_days_per_year : int
        Annualization factor (252)

    Returns
    -------
    float
        Annualized volatility (standard deviation) as a decimal
    """
    r = np.array(returns, dtype=float)
    r = r[~np.isnan(r)]  # remove NaN
    if len(r) < 2:
        return np.nan

    return float(np.std(r, ddof=1) * np.sqrt(trading_days_per_year))


def sharpe_ratio(
    returns: Union[pd.Series, np.ndarray],
    risk_free_rate: float = RISK_FREE_RATE,
    trading_days_per_year: int = TRADING_DAYS_PER_YEAR,
) -> float:
    """
    Compute the annualized Sharpe ratio.

    Formula: Sharpe = (R_p - R_f) / sigma_p

    where:
      R_p     = annualized portfolio return
      R_f     = annual risk-free rate
      sigma_p = annualized portfolio volatility

    The Sharpe ratio measures how much excess return (above the risk-free rate)
    is earned per unit of total risk. Higher is better. A Sharpe > 1 is
    generally considered good, > 2 is excellent.

    We compute it from daily returns:
      Sharpe = sqrt(252) * mean(r_t - rf_daily) / std(r_t - rf_daily)

    Parameters
    ----------
    returns : pd.Series or np.ndarray
        Daily simple returns
    risk_free_rate : float
        Annual risk-free rate (e.g., 0.05 = 5%)
    trading_days_per_year : int
        Annualization factor

    Returns
    -------
    float
        Annualized Sharpe ratio
    """
    r = np.array(returns, dtype=float)
    r = r[~np.isnan(r)]
    if len(r) < 2:
        return np.nan

    # Convert annual risk-free rate to daily
    daily_rf = risk_free_rate / trading_days_per_year

    excess_returns = r - daily_rf
    mean_excess = np.mean(excess_returns)
    std_excess = np.std(excess_returns, ddof=1)

    if std_excess < 1e-10:
        return np.nan

    # Annualize: multiply by sqrt(252)
    return float(mean_excess / std_excess * np.sqrt(trading_days_per_year))


def downside_deviation(
    returns: Union[pd.Series, np.ndarray],
    risk_free_rate: float = RISK_FREE_RATE,
    trading_days_per_year: int = TRADING_DAYS_PER_YEAR,
) -> float:
    """
    Compute annualized downside deviation (semi-deviation).

    Downside deviation measures only the volatility of negative excess returns.
    It is used in the Sortino ratio and is considered a better measure of
    "bad" risk than total volatility (which penalizes upside volatility equally).

    Formula: DD = sqrt( (1/T) * sum( min(r_t - rf, 0)^2 ) ) * sqrt(252)

    Parameters
    ----------
    returns : pd.Series or np.ndarray
        Daily simple returns
    risk_free_rate : float
        Annual risk-free rate
    trading_days_per_year : int
        Annualization factor

    Returns
    -------
    float
        Annualized downside deviation
    """
    r = np.array(returns, dtype=float)
    r = r[~np.isnan(r)]
    if len(r) < 2:
        return np.nan

    daily_rf = risk_free_rate / trading_days_per_year
    excess = r - daily_rf

    # Only penalize downside (negative excess returns)
    downside = np.minimum(excess, 0)
    dd = np.sqrt(np.mean(downside ** 2))

    return float(dd * np.sqrt(trading_days_per_year))


def sortino_ratio(
    returns: Union[pd.Series, np.ndarray],
    risk_free_rate: float = RISK_FREE_RATE,
    trading_days_per_year: int = TRADING_DAYS_PER_YEAR,
) -> float:
    """
    Compute the annualized Sortino ratio.

    Formula: Sortino = (R_p - R_f) / DD

    where DD is the downside deviation (not total volatility).

    Sortino vs Sharpe:
      - Sharpe penalizes both upside and downside volatility equally
      - Sortino only penalizes downside volatility
      - If a strategy has high volatility mostly from big gains,
        Sortino will be higher than Sharpe -- and rightfully so.

    Parameters
    ----------
    returns : pd.Series or np.ndarray
        Daily simple returns
    risk_free_rate : float
        Annual risk-free rate
    trading_days_per_year : int
        Annualization factor

    Returns
    -------
    float
        Annualized Sortino ratio
    """
    r = np.array(returns, dtype=float)
    r = r[~np.isnan(r)]
    if len(r) < 2:
        return np.nan

    daily_rf = risk_free_rate / trading_days_per_year
    ann_excess_return = (np.mean(r) - daily_rf) * trading_days_per_year
    dd = downside_deviation(r, risk_free_rate, trading_days_per_year)

    if dd < 1e-10:
        return np.nan

    return float(ann_excess_return / dd)


def max_drawdown(
    equity_curve: Union[pd.Series, np.ndarray],
) -> float:
    """
    Compute the maximum drawdown of an equity curve.

    Formula: MDD = min_t ( (Peak_t - Trough_t) / Peak_t )
           = min_t ( Equity_t / max_{s<=t}(Equity_s) - 1 )

    Maximum drawdown is the largest peak-to-trough decline, expressed
    as a fraction of the peak value. It is the most commonly cited
    measure of tail risk / downside scenario for a portfolio.

    A drawdown of -0.30 means the portfolio fell 30% from its prior peak.
    By convention, maximum drawdown is reported as a negative number.

    Parameters
    ----------
    equity_curve : pd.Series or np.ndarray
        Portfolio value over time (in dollars or normalized to 1.0)

    Returns
    -------
    float
        Maximum drawdown as a negative decimal (e.g., -0.30 = -30%)
    """
    eq = np.array(equity_curve, dtype=float)
    eq = eq[~np.isnan(eq)]
    if len(eq) < 2:
        return np.nan

    # Running maximum (peak up to each point in time)
    running_max = np.maximum.accumulate(eq)

    # Drawdown at each point = (current value / peak) - 1
    drawdown = eq / running_max - 1

    return float(np.min(drawdown))


def compute_beta(
    portfolio_returns: Union[pd.Series, np.ndarray],
    benchmark_returns: Union[pd.Series, np.ndarray],
) -> float:
    """
    Compute portfolio beta relative to a benchmark.

    Formula: Beta = Cov(R_p, R_b) / Var(R_b)

    Beta measures the portfolio's sensitivity to benchmark movements:
      Beta = 1.0 ? moves 1:1 with the benchmark
      Beta > 1.0 ? amplifies benchmark moves (more aggressive)
      Beta < 1.0 ? dampens benchmark moves (more defensive)
      Beta < 0   ? moves opposite to benchmark (very rare)

    Parameters
    ----------
    portfolio_returns : pd.Series or np.ndarray
        Daily portfolio returns
    benchmark_returns : pd.Series or np.ndarray
        Daily benchmark returns (aligned with portfolio returns)

    Returns
    -------
    float
        Portfolio beta
    """
    p = np.array(portfolio_returns, dtype=float)
    b = np.array(benchmark_returns, dtype=float)

    # Align lengths (use common non-NaN observations)
    mask = ~(np.isnan(p) | np.isnan(b))
    p, b = p[mask], b[mask]

    if len(p) < 2:
        return np.nan

    benchmark_var = np.var(b, ddof=1)
    if benchmark_var < 1e-12:
        return np.nan

    covariance = np.cov(p, b, ddof=1)[0, 1]
    return float(covariance / benchmark_var)


def calmar_ratio(
    annualized_return: float,
    max_dd: float,
) -> float:
    """
    Compute the Calmar ratio.

    Formula: Calmar = CAGR / |MDD|

    The Calmar ratio compares the annual return to the worst historical
    drawdown. It is useful for strategies that aim to have controlled
    drawdowns (e.g., trend-following, risk-managed portfolios).

    Parameters
    ----------
    annualized_return : float
        CAGR as a decimal (e.g., 0.12 = 12%)
    max_dd : float
        Maximum drawdown as a negative decimal (e.g., -0.30)

    Returns
    -------
    float
        Calmar ratio (positive = good)
    """
    if max_dd >= 0 or abs(max_dd) < 1e-10:
        return np.nan
    return float(annualized_return / abs(max_dd))


def tracking_error(
    portfolio_returns: Union[pd.Series, np.ndarray],
    benchmark_returns: Union[pd.Series, np.ndarray],
    trading_days_per_year: int = TRADING_DAYS_PER_YEAR,
) -> float:
    """
    Compute annualized tracking error.

    Formula: TE = std(R_p - R_b) * sqrt(252)

    Tracking error measures how closely a portfolio follows its benchmark.
    Low TE = portfolio closely tracks the benchmark (good for index funds).
    High TE = portfolio diverges significantly from benchmark (active management).

    Parameters
    ----------
    portfolio_returns : pd.Series or np.ndarray
        Daily portfolio returns
    benchmark_returns : pd.Series or np.ndarray
        Daily benchmark returns
    trading_days_per_year : int
        Annualization factor

    Returns
    -------
    float
        Annualized tracking error
    """
    p = np.array(portfolio_returns, dtype=float)
    b = np.array(benchmark_returns, dtype=float)

    mask = ~(np.isnan(p) | np.isnan(b))
    p, b = p[mask], b[mask]

    if len(p) < 2:
        return np.nan

    active_returns = p - b
    return float(np.std(active_returns, ddof=1) * np.sqrt(trading_days_per_year))


def compute_cagr(
    equity_curve: Union[pd.Series, np.ndarray],
    trading_days_per_year: int = TRADING_DAYS_PER_YEAR,
) -> float:
    """
    Compute CAGR from an equity curve.

    Formula: CAGR = (final_value / initial_value)^(252/n_days) - 1

    Parameters
    ----------
    equity_curve : pd.Series or np.ndarray
        Portfolio value over time (in dollars or normalized)
    trading_days_per_year : int
        Annualization factor

    Returns
    -------
    float
        Annualized return (CAGR) as a decimal
    """
    eq = np.array(equity_curve, dtype=float)
    eq = eq[~np.isnan(eq)]
    if len(eq) < 2:
        return np.nan

    total_return = eq[-1] / eq[0] - 1
    n_days = len(eq)
    years = n_days / trading_days_per_year

    return float((1 + total_return) ** (1 / years) - 1)


def compute_all_metrics(
    equity_curve: pd.Series,
    daily_returns: pd.Series,
    benchmark_returns: pd.Series,
    strategy_name: str,
    risk_free_rate: float = RISK_FREE_RATE,
    trading_days_per_year: int = TRADING_DAYS_PER_YEAR,
) -> Dict[str, float]:
    """
    Compute all risk and performance metrics for a strategy.

    This is the main function called from main.py. It assembles
    every metric into a single dictionary for easy storage and export.

    Parameters
    ----------
    equity_curve : pd.Series
        Portfolio value over time (in dollars)
    daily_returns : pd.Series
        Daily simple returns of the portfolio
    benchmark_returns : pd.Series
        Daily benchmark returns (aligned dates)
    strategy_name : str
        Name of the strategy (for labeling)
    risk_free_rate : float
        Annual risk-free rate
    trading_days_per_year : int
        252

    Returns
    -------
    dict
        All computed metrics, keyed by metric name
    """
    # Align benchmark returns to portfolio return dates
    aligned_benchmark = benchmark_returns.reindex(daily_returns.index).fillna(0)

    total_return = float(equity_curve.iloc[-1] / equity_curve.iloc[0] - 1)

    metrics = {
        "Strategy":           strategy_name,
        "Total Return":       round(total_return, 4),
        "CAGR":               round(compute_cagr(equity_curve, trading_days_per_year), 4),
        "Ann. Volatility":    round(annualized_volatility(daily_returns, trading_days_per_year), 4),
        "Sharpe Ratio":       round(sharpe_ratio(daily_returns, risk_free_rate, trading_days_per_year), 4),
        "Sortino Ratio":      round(sortino_ratio(daily_returns, risk_free_rate, trading_days_per_year), 4),
        "Max Drawdown":       round(max_drawdown(equity_curve), 4),
        "Beta":               round(compute_beta(daily_returns, aligned_benchmark), 4),
        "Calmar Ratio":       round(
                                  calmar_ratio(
                                      compute_cagr(equity_curve, trading_days_per_year),
                                      max_drawdown(equity_curve)
                                  ), 4
                              ),
        "Tracking Error":     round(tracking_error(daily_returns, aligned_benchmark, trading_days_per_year), 4),
    }

    return metrics
