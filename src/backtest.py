"""
backtest.py
===========
Historical backtesting engine for the three portfolio strategies.

BACKTESTING DESIGN PHILOSOPHY
-------------------------------
A backtest simulates how a portfolio strategy would have performed
over a historical period. The key discipline is strict information
segregation: no information from the future is ever used to make
decisions in the past.

HOW WE PREVENT LOOK-AHEAD BIAS
--------------------------------
At each rebalance date T, we:
  1. Use ONLY the log returns from the estimation window [T-W, T-1]
     where T-1 is the last day BEFORE the rebalance date
  2. Compute portfolio weights from that historical window
  3. Apply those weights starting from date T
  4. Evaluate performance over [T, T+rebalance_period-1]

The weights calculated at T can NEVER depend on any price or return
from day T or later.

This is enforced in the code by slicing `log_returns.iloc[:t_idx]`
where t_idx is the integer index of the rebalance date. This strict
slice includes only data strictly before position t_idx.

TIMELINE ILLUSTRATION
----------------------
  |-----estimation window-------|R|---evaluation period---|R|-...
  T-W                          T-1  T                    T+P

  T   = rebalance date (weights computed and applied)
  T-W = start of estimation window (W trading days before T)
  T-1 = last day used for estimation
  T+P = next rebalance date

TRANSACTION COSTS
-----------------
When we rebalance, we pay:
    cost = transaction_cost_pct * sum(|w_new_i - w_current_i|) * portfolio_value

This is a one-sided cost (applied once per rebalance), applied as a
deduction from portfolio value. It represents bid-ask spread and
brokerage commissions in simplified form.

SIMPLIFICATIONS / LIMITATIONS
-------------------------------
- We assume orders execute at the daily closing price on rebalance day
- No market impact model (realistic for small portfolios, not large ones)
- No intraday execution; daily granularity only
- Benchmark uses the same evaluation dates for a fair comparison
"""

import numpy as np
import pandas as pd
from typing import Callable, Dict, List, Optional, Tuple

from src.config import (
    INITIAL_CAPITAL,
    REBALANCE_FREQ,
    TRANSACTION_COST_PCT,
    MIN_ESTIMATION_DAYS,
    TRADING_DAYS_PER_YEAR,
    ALL_STRATEGIES,
)
from src.returns import compute_log_returns, compute_simple_returns
from src.optimization import get_strategy_weights


def get_rebalance_dates(
    date_index: pd.DatetimeIndex,
    freq: str = "monthly",
) -> List[pd.Timestamp]:
    """
    Identify rebalance dates from a trading-day index.

    For "monthly": first trading day of each calendar month
    For "quarterly": first trading day of each calendar quarter

    Parameters
    ----------
    date_index : pd.DatetimeIndex
        All available trading dates in the backtest period
    freq : str
        "monthly" or "quarterly"

    Returns
    -------
    list of pd.Timestamp
        Dates at which the portfolio is rebalanced
    """
    if freq == "monthly":
        # Group by year-month, take the first date in each group
        df = pd.DataFrame({"date": date_index})
        df["ym"] = df["date"].dt.to_period("M")
        rebalance_dates = df.groupby("ym")["date"].first().tolist()

    elif freq == "quarterly":
        df = pd.DataFrame({"date": date_index})
        df["yq"] = df["date"].dt.to_period("Q")
        rebalance_dates = df.groupby("yq")["date"].first().tolist()

    else:
        raise ValueError(f"Unknown rebalance frequency: '{freq}'. Use 'monthly' or 'quarterly'.")

    return rebalance_dates


def run_backtest(
    strategy_name: str,
    prices: pd.DataFrame,
    initial_capital: float = INITIAL_CAPITAL,
    rebalance_freq: str = REBALANCE_FREQ,
    transaction_cost_pct: float = TRANSACTION_COST_PCT,
    min_estimation_days: int = MIN_ESTIMATION_DAYS,
    verbose: bool = False,
) -> Dict:
    """
    Run a single-strategy historical backtest.

    Parameters
    ----------
    strategy_name : str
        Strategy name (must be in config.ALL_STRATEGIES)
    prices : pd.DataFrame
        Clean adjusted close prices, DatetimeIndex, ticker columns
    initial_capital : float
        Starting portfolio value in USD
    rebalance_freq : str
        "monthly" or "quarterly"
    transaction_cost_pct : float
        Cost as fraction of traded value (e.g., 0.001 = 10 bps)
    min_estimation_days : int
        Minimum trading days of history required before first rebalance
    verbose : bool
        If True, print per-rebalance details

    Returns
    -------
    dict with keys:
        "portfolio_values"  : pd.Series -- daily portfolio value in USD
        "daily_returns"     : pd.Series -- daily simple return of portfolio
        "weights_history"   : pd.DataFrame -- weights at each rebalance date
        "turnover_history"  : pd.Series -- portfolio turnover at each rebalance
        "total_costs"       : float -- total transaction costs paid
        "n_rebalances"      : int -- number of rebalances performed
        "strategy"          : str -- strategy name
    """
    tickers = list(prices.columns)
    n_assets = len(tickers)

    # Compute daily simple and log returns for the full period
    simple_returns = compute_simple_returns(prices)
    log_returns = compute_log_returns(prices)

    # Get all trading dates (starting from the first return date)
    all_dates = simple_returns.index
    date_to_idx = {d: i for i, d in enumerate(all_dates)}

    # Identify rebalance dates
    all_rebalance_dates = get_rebalance_dates(all_dates, freq=rebalance_freq)

    # Skip rebalance dates that don't have enough estimation history
    rebalance_dates = [
        d for d in all_rebalance_dates
        if date_to_idx.get(d, 0) >= min_estimation_days
    ]

    if len(rebalance_dates) == 0:
        raise ValueError(
            f"No valid rebalance dates found. Need at least {min_estimation_days} days of history."
        )

    # --- Backtest simulation loop ---------------------------------
    portfolio_value = initial_capital
    current_weights = np.ones(n_assets) / n_assets   # start equal-weight

    portfolio_values = []
    daily_returns_list = []
    weights_history_rows = []
    turnover_history = {}
    total_costs = 0.0

    # Build a set for O(1) lookup of rebalance dates
    rebalance_set = set(rebalance_dates)

    for date in all_dates:
        t_idx = date_to_idx[date]

        # REBALANCE: compute new weights using only PAST data
        if date in rebalance_set:
            # Slice strictly before this date (t_idx is exclusive)
            # This enforces the no-look-ahead-bias rule
            estimation_window = log_returns.iloc[:t_idx]

            new_weights = get_strategy_weights(
                strategy_name=strategy_name,
                log_returns=estimation_window,
                tickers=tickers,
            )

            # Compute turnover = sum of absolute weight changes
            turnover = float(np.sum(np.abs(new_weights - current_weights)))
            turnover_history[date] = turnover

            # Apply transaction costs
            cost = transaction_cost_pct * turnover * portfolio_value
            portfolio_value -= cost
            total_costs += cost

            if verbose:
                print(
                    f"  {date.date()} | {strategy_name} | "
                    f"Turnover: {turnover:.2%} | Cost: ${cost:.2f}"
                )

            current_weights = new_weights

            # Record weights at this rebalance date
            for ticker, weight in zip(tickers, current_weights):
                weights_history_rows.append({
                    "Date": date,
                    "Strategy": strategy_name,
                    "Ticker": ticker,
                    "Weight": round(float(weight), 6),
                })

        # DAILY RETURN: apply today's returns to current weights
        todays_asset_returns = simple_returns.loc[date].values
        portfolio_daily_return = float(np.dot(current_weights, todays_asset_returns))

        # Update portfolio value
        portfolio_value *= (1 + portfolio_daily_return)
        portfolio_values.append(portfolio_value)
        daily_returns_list.append(portfolio_daily_return)

    portfolio_values_series = pd.Series(portfolio_values, index=all_dates, name=strategy_name)
    daily_returns_series = pd.Series(daily_returns_list, index=all_dates, name=strategy_name)
    weights_df = pd.DataFrame(weights_history_rows)
    turnover_series = pd.Series(turnover_history, name=strategy_name)

    return {
        "strategy": strategy_name,
        "portfolio_values": portfolio_values_series,
        "daily_returns": daily_returns_series,
        "weights_history": weights_df,
        "turnover_history": turnover_series,
        "total_costs": total_costs,
        "n_rebalances": len(rebalance_dates),
        "initial_capital": initial_capital,
    }


def run_all_strategies(
    prices: pd.DataFrame,
    strategies: List[str] = None,
    initial_capital: float = INITIAL_CAPITAL,
    rebalance_freq: str = REBALANCE_FREQ,
    transaction_cost_pct: float = TRANSACTION_COST_PCT,
    verbose: bool = False,
) -> Dict[str, Dict]:
    """
    Run the backtest for all strategies and return combined results.

    Parameters
    ----------
    prices : pd.DataFrame
        Clean adjusted close prices
    strategies : list of str, optional
        Strategies to run. Defaults to ALL_STRATEGIES from config.
    initial_capital : float
        Starting capital
    rebalance_freq : str
        Rebalance frequency
    transaction_cost_pct : float
        Transaction cost fraction
    verbose : bool
        Print per-rebalance detail

    Returns
    -------
    dict
        {strategy_name: backtest_result_dict} for each strategy
    """
    if strategies is None:
        strategies = ALL_STRATEGIES

    results = {}
    for strategy in strategies:
        print(f"    Running backtest: {strategy}...")
        result = run_backtest(
            strategy_name=strategy,
            prices=prices,
            initial_capital=initial_capital,
            rebalance_freq=rebalance_freq,
            transaction_cost_pct=transaction_cost_pct,
            verbose=verbose,
        )
        results[strategy] = result
        final_value = result["portfolio_values"].iloc[-1]
        total_return = (final_value / initial_capital - 1) * 100
        print(
            f"    OK {strategy}: Final value ${final_value:,.0f} | "
            f"Total return {total_return:.1f}% | "
            f"Rebalances: {result['n_rebalances']} | "
            f"Costs: ${result['total_costs']:,.0f}"
        )

    return results


def combine_equity_curves(
    backtest_results: Dict[str, Dict],
    normalize: bool = True,
) -> pd.DataFrame:
    """
    Build a DataFrame of equity curves from all strategy backtest results.

    Parameters
    ----------
    backtest_results : dict
        Output of run_all_strategies()
    normalize : bool
        If True, normalize all curves to start at 1.0 for easy comparison

    Returns
    -------
    pd.DataFrame
        Equity curves, one column per strategy
    """
    curves = {}
    for strategy_name, result in backtest_results.items():
        values = result["portfolio_values"]
        if normalize:
            values = values / values.iloc[0]
        curves[strategy_name] = values

    return pd.DataFrame(curves)


def combine_daily_returns(
    backtest_results: Dict[str, Dict],
) -> pd.DataFrame:
    """
    Combine daily return series from all strategies into one DataFrame.

    Parameters
    ----------
    backtest_results : dict
        Output of run_all_strategies()

    Returns
    -------
    pd.DataFrame
        Daily returns, one column per strategy
    """
    return pd.DataFrame({
        name: result["daily_returns"]
        for name, result in backtest_results.items()
    })


def combine_weights_history(
    backtest_results: Dict[str, Dict],
) -> pd.DataFrame:
    """
    Combine weights history from all strategies into one tidy DataFrame.

    Parameters
    ----------
    backtest_results : dict
        Output of run_all_strategies()

    Returns
    -------
    pd.DataFrame
        Tidy DataFrame with columns: Date, Strategy, Ticker, Weight
    """
    all_weights = []
    for name, result in backtest_results.items():
        if not result["weights_history"].empty:
            all_weights.append(result["weights_history"])

    if not all_weights:
        return pd.DataFrame(columns=["Date", "Strategy", "Ticker", "Weight"])

    return pd.concat(all_weights, ignore_index=True)
