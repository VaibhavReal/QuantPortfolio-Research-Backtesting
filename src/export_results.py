"""
export_results.py
=================
Export clean CSV datasets for Power BI and Tableau dashboards.
Optimized with fast, vectorized Pandas operations.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Optional

from src.config import EXPORTS_DIR, BENCHMARK_NAME


def export_strategy_performance(
    backtest_results: Dict[str, Dict],
    benchmark_returns: pd.Series,
    path: Optional[Path] = None,
) -> pd.DataFrame:
    """Export daily portfolio equity curves for all strategies + benchmark."""
    if path is None:
        path = EXPORTS_DIR / "strategy_performance.csv"

    dfs = []
    for strategy_name, result in backtest_results.items():
        v = result["portfolio_values"]
        r = result["daily_returns"]
        initial = v.iloc[0]

        df_strat = pd.DataFrame({
            "Date": v.index.strftime("%Y-%m-%d"),
            "Strategy": strategy_name,
            "Portfolio Value": v.round(2).values,
            "Normalized Value": (v / initial).round(6).values,
            "Daily Return": r.reindex(v.index).round(6).values,
        })
        dfs.append(df_strat)

    # Benchmark
    initial_capital = list(backtest_results.values())[0]["initial_capital"]
    bm_equity = initial_capital * (1 + benchmark_returns).cumprod()
    df_bm = pd.DataFrame({
        "Date": benchmark_returns.index.strftime("%Y-%m-%d"),
        "Strategy": BENCHMARK_NAME,
        "Portfolio Value": bm_equity.round(2).values,
        "Normalized Value": (bm_equity / bm_equity.iloc[0]).round(6).values,
        "Daily Return": benchmark_returns.round(6).values,
    })
    dfs.append(df_bm)

    df = pd.concat(dfs, ignore_index=True)
    df.to_csv(path, index=False)
    print(f"  Exported strategy_performance.csv ({len(df)} rows)")
    return df


def export_risk_metrics(
    all_metrics: Dict[str, Dict],
    path: Optional[Path] = None,
) -> pd.DataFrame:
    """Export all risk and performance metrics to CSV."""
    if path is None:
        path = EXPORTS_DIR / "risk_metrics.csv"

    df = pd.DataFrame(list(all_metrics.values()))
    df.to_csv(path, index=False)
    print(f"  Exported risk_metrics.csv ({len(df)} rows)")
    return df


def export_portfolio_weights(
    combined_weights: pd.DataFrame,
    path: Optional[Path] = None,
) -> pd.DataFrame:
    """Export portfolio weights at each rebalance date for all strategies."""
    if path is None:
        path = EXPORTS_DIR / "portfolio_weights.csv"

    df = combined_weights.copy()
    if "Date" in df.columns and not df.empty:
        df["Date"] = pd.to_datetime(df["Date"]).dt.strftime("%Y-%m-%d")

    df.to_csv(path, index=False)
    print(f"  Exported portfolio_weights.csv ({len(df)} rows)")
    return df


def export_benchmark_comparison(
    comparison_df: pd.DataFrame,
    path: Optional[Path] = None,
) -> pd.DataFrame:
    """Export the strategy-vs-benchmark comparison table."""
    if path is None:
        path = EXPORTS_DIR / "benchmark_comparison.csv"

    df = comparison_df.copy()
    df.to_csv(path, index=False)
    print(f"  Exported benchmark_comparison.csv ({len(df)} rows)")
    return df


def export_asset_returns(
    prices: pd.DataFrame,
    path: Optional[Path] = None,
) -> pd.DataFrame:
    """Vectorized export of daily simple returns for each asset."""
    if path is None:
        path = EXPORTS_DIR / "asset_returns.csv"

    from src.returns import compute_simple_returns

    simple_returns = compute_simple_returns(prices)
    cumulative_returns = (1 + simple_returns).cumprod() - 1

    # Melt to long format
    sr_long = simple_returns.reset_index().melt(
        id_vars=["Date"], var_name="Ticker", value_name="Daily Return"
    )
    cr_long = cumulative_returns.reset_index().melt(
        id_vars=["Date"], var_name="Ticker", value_name="Cumulative Return"
    )

    merged = pd.merge(sr_long, cr_long, on=["Date", "Ticker"])
    merged["Date"] = pd.to_datetime(merged["Date"]).dt.strftime("%Y-%m-%d")
    merged["Daily Return"] = merged["Daily Return"].round(6)
    merged["Cumulative Return"] = merged["Cumulative Return"].round(6)

    merged.to_csv(path, index=False)
    print(f"  Exported asset_returns.csv ({len(merged)} rows)")
    return merged


def export_all(
    backtest_results: Dict[str, Dict],
    all_metrics: Dict[str, Dict],
    combined_weights: pd.DataFrame,
    comparison_df: pd.DataFrame,
    benchmark_returns: pd.Series,
    prices: pd.DataFrame,
) -> None:
    """Export all five dashboard-ready CSV files in one call."""
    export_strategy_performance(backtest_results, benchmark_returns)
    export_risk_metrics(all_metrics)
    export_portfolio_weights(combined_weights)
    export_benchmark_comparison(comparison_df)
    export_asset_returns(prices)
    print(f"  All CSV exports written to {EXPORTS_DIR}")
