"""
data_cleaning.py
================
Data validation and cleaning pipeline for raw price data.

WHY DATA QUALITY MATTERS IN FINANCE
-------------------------------------
Financial data is notoriously messy. Common issues include:
  - Corporate actions (splits, mergers) creating apparent price jumps
  - Exchange holidays causing gaps
  - Survivorship bias if you only keep stocks that "survived"
  - Data vendor errors (stale prices, erroneous zeros)

Poor data quality corrupts every downstream calculation: returns,
covariance matrices, and ultimately portfolio weights. It's always
worth checking the data before trusting any output.

This module runs a sequence of checks and fixes, printing a summary
so the analyst can spot problems immediately.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any

from src.config import TICKERS, CLEAN_PRICES_PATH


def check_missing_values(prices: pd.DataFrame) -> Dict[str, Any]:
    """
    Check for NaN values in the price DataFrame.

    Missing prices can occur because:
      - A stock was not yet listed (IPO after start date)
      - Exchange holiday alignment differences
      - Data vendor errors

    Returns a dict with per-ticker missing counts and a total flag.
    """
    missing_counts = prices.isna().sum()
    total_missing = int(missing_counts.sum())
    has_missing = total_missing > 0

    return {
        "total_missing": total_missing,
        "has_missing": has_missing,
        "per_ticker": missing_counts[missing_counts > 0].to_dict(),
    }


def check_non_positive_prices(prices: pd.DataFrame) -> Dict[str, Any]:
    """
    Check for zero or negative prices.

    A zero or negative adjusted close price is almost always a data error.
    Stock prices can only reach zero at bankruptcy, and those observations
    should be handled explicitly rather than silently polluting returns.
    """
    non_positive = (prices <= 0).sum()
    total_non_positive = int(non_positive.sum())

    return {
        "total_non_positive": total_non_positive,
        "has_non_positive": total_non_positive > 0,
        "per_ticker": non_positive[non_positive > 0].to_dict(),
    }


def check_duplicate_dates(prices: pd.DataFrame) -> Dict[str, Any]:
    """
    Check for duplicate dates in the index.

    Duplicate dates would double-count observations in any
    cumulative calculation and produce incorrect return series.
    """
    duplicates = prices.index.duplicated()
    n_duplicates = int(duplicates.sum())

    return {
        "n_duplicate_dates": n_duplicates,
        "has_duplicates": n_duplicates > 0,
        "duplicate_dates": list(prices.index[duplicates]),
    }


def check_date_order(prices: pd.DataFrame) -> Dict[str, Any]:
    """
    Verify the index is sorted in ascending chronological order.

    Unsorted dates break any calculation that assumes time-order
    (cumulative products, rolling windows, backtest loops).
    """
    is_sorted = prices.index.is_monotonic_increasing

    return {
        "is_sorted": is_sorted,
        "needs_sorting": not is_sorted,
    }


def check_date_gaps(prices: pd.DataFrame, max_gap_days: int = 10) -> Dict[str, Any]:
    """
    Look for unusually large gaps between consecutive trading dates.

    A gap > max_gap_days (excluding weekends/holidays) may indicate
    a data problem. Normal gaps happen around Christmas and New Year.
    A gap > 10 calendar days is worth flagging for investigation.

    Parameters
    ----------
    max_gap_days : int
        Maximum acceptable calendar-day gap between consecutive dates
    """
    if len(prices) < 2:
        return {"max_gap_days": 0, "has_large_gap": False, "large_gaps": []}

    date_diffs = prices.index.to_series().diff().dt.days.dropna()
    large_gaps = date_diffs[date_diffs > max_gap_days]

    return {
        "max_gap_days": int(date_diffs.max()),
        "has_large_gap": len(large_gaps) > 0,
        "large_gaps": [(str(dt.date()), int(gap)) for dt, gap in large_gaps.items()],
    }


def validate_data(prices: pd.DataFrame, verbose: bool = True) -> Dict[str, Any]:
    """
    Run all data quality checks on the raw price DataFrame.

    Parameters
    ----------
    prices : pd.DataFrame
        Raw price DataFrame with DatetimeIndex and ticker columns
    verbose : bool
        If True, print a formatted validation report

    Returns
    -------
    dict
        Nested dict with results of all checks.
        Key "all_passed" is True if no critical issues found.
    """
    results = {
        "missing_values":    check_missing_values(prices),
        "non_positive":      check_non_positive_prices(prices),
        "duplicate_dates":   check_duplicate_dates(prices),
        "date_order":        check_date_order(prices),
        "date_gaps":         check_date_gaps(prices),
    }

    # Overall flag: all critical checks must pass
    results["all_passed"] = (
        not results["missing_values"]["has_missing"]
        and not results["non_positive"]["has_non_positive"]
        and not results["duplicate_dates"]["has_duplicates"]
        and results["date_order"]["is_sorted"]
    )

    if verbose:
        _print_validation_report(prices, results)

    return results


def _print_validation_report(prices: pd.DataFrame, results: Dict[str, Any]) -> None:
    """Print a human-readable validation summary to the console."""
    print("\n  --- Data Validation Report ---------------------------")
    print(f"  Shape          : {prices.shape[0]} rows x {prices.shape[1]} columns")
    print(f"  Date range     : {prices.index.min().date()} -> {prices.index.max().date()}")
    print(f"  Tickers        : {list(prices.columns)}")

    mv = results["missing_values"]
    sym = "PASS" if not mv["has_missing"] else "FAIL"
    print(f"  {sym} Missing values  : {mv['total_missing']}", end="")
    if mv["has_missing"]:
        print(f"  -> {mv['per_ticker']}", end="")
    print()

    np_ = results["non_positive"]
    sym = "PASS" if not np_["has_non_positive"] else "FAIL"
    print(f"  {sym} Non-positive     : {np_['total_non_positive']}", end="")
    if np_["has_non_positive"]:
        print(f"  -> {np_['per_ticker']}", end="")
    print()

    dd = results["duplicate_dates"]
    sym = "PASS" if not dd["has_duplicates"] else "FAIL"
    print(f"  {sym} Duplicate dates  : {dd['n_duplicate_dates']}")

    do_ = results["date_order"]
    sym = "PASS" if do_["is_sorted"] else "FAIL"
    print(f"  {sym} Chronological    : {do_['is_sorted']}")

    dg = results["date_gaps"]
    sym = "PASS" if not dg["has_large_gap"] else "WARN"
    print(f"  {sym} Max date gap     : {dg['max_gap_days']} calendar days", end="")
    if dg["has_large_gap"]:
        print(f"  (> 10 days -- review dates: {dg['large_gaps'][:3]})", end="")
    print()

    status = "PASSED OK" if results["all_passed"] else "ISSUES FOUND X"
    print(f"  Overall        : {status}")
    print("  ---\n")


def clean_data(prices: pd.DataFrame, verbose: bool = True) -> pd.DataFrame:
    """
    Apply data cleaning steps to the raw price DataFrame.

    Cleaning steps (in order):
      1. Remove duplicate dates (keep first occurrence)
      2. Sort index chronologically
      3. Forward-fill missing values (up to 5 consecutive NaNs)
         Rationale: a missing price on a given day usually means the market
         was closed (holiday) or there was a data vendor gap. The last known
         price is the best available estimate. We cap at 5 consecutive fills
         to avoid masking genuine data issues.
      4. Drop any remaining NaN rows (e.g., missing at start of series)
      5. Drop any columns (tickers) with > 10% missing data
      6. Replace non-positive prices with NaN then forward-fill

    Parameters
    ----------
    prices : pd.DataFrame
        Raw adjusted close prices

    Returns
    -------
    pd.DataFrame
        Cleaned prices, ready for return calculations
    """
    df = prices.copy()
    original_shape = df.shape

    # Step 1: Remove duplicate dates
    if df.index.duplicated().any():
        if verbose:
            print("  Removing duplicate dates...")
        df = df[~df.index.duplicated(keep="first")]

    # Step 2: Sort chronologically
    if not df.index.is_monotonic_increasing:
        if verbose:
            print("  Sorting index chronologically...")
        df = df.sort_index()

    # Step 3: Replace non-positive prices with NaN
    n_non_positive = (df <= 0).sum().sum()
    if n_non_positive > 0:
        if verbose:
            print(f"  Replacing {n_non_positive} non-positive prices with NaN...")
        df[df <= 0] = np.nan

    # Step 4: Drop tickers with too many missing values (> 10% threshold)
    missing_pct = df.isna().mean()
    tickers_to_drop = missing_pct[missing_pct > 0.10].index.tolist()
    if tickers_to_drop:
        if verbose:
            print(f"  Dropping tickers with >10% missing data: {tickers_to_drop}")
        df = df.drop(columns=tickers_to_drop)

    # Step 5: Forward-fill missing values (max 5 consecutive)
    n_missing_before = df.isna().sum().sum()
    if n_missing_before > 0:
        if verbose:
            print(f"  Forward-filling {n_missing_before} missing values (limit=5)...")
        df = df.ffill(limit=5)

    # Step 6: Drop any remaining rows with NaN (usually the very first few rows)
    n_remaining_nan = df.isna().sum().sum()
    if n_remaining_nan > 0:
        rows_before = len(df)
        df = df.dropna()
        rows_dropped = rows_before - len(df)
        if verbose:
            print(f"  Dropped {rows_dropped} rows with remaining NaN values.")

    if verbose:
        print(f"  Cleaned: {original_shape} -> {df.shape}")

    return df


def get_clean_prices(
    raw_prices: pd.DataFrame,
    save: bool = True,
    verbose: bool = True,
) -> pd.DataFrame:
    """
    Validate and clean raw prices, then optionally save to disk.

    This is the main function called from main.py. It:
      1. Validates the raw data
      2. Cleans it
      3. Validates again (post-cleaning sanity check)
      4. Saves if requested

    Parameters
    ----------
    raw_prices : pd.DataFrame
        Raw adjusted close prices from data_loader
    save : bool
        If True, save cleaned prices to CLEAN_PRICES_PATH
    verbose : bool
        If True, print progress

    Returns
    -------
    pd.DataFrame
        Cleaned price data ready for return calculations
    """
    if verbose:
        print("  Running pre-clean validation...")
    validate_data(raw_prices, verbose=verbose)

    if verbose:
        print("  Applying cleaning steps...")
    clean_prices = clean_data(raw_prices, verbose=verbose)

    if verbose:
        print("  Running post-clean validation...")
    post_results = validate_data(clean_prices, verbose=verbose)

    if not post_results["all_passed"]:
        print("  WARNING: Data quality issues remain after cleaning. Proceed with caution.")

    if save:
        clean_prices.to_csv(CLEAN_PRICES_PATH)
        if verbose:
            print(f"  Cleaned prices saved to {CLEAN_PRICES_PATH}")

    return clean_prices
