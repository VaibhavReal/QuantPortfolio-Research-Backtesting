"""
data_loader.py
==============
Handles downloading, caching, and loading of historical market price data.

Data source: Yahoo Finance via the yfinance library.
Downloaded field: Adjusted Close price (accounts for dividends and stock splits).

WHY ADJUSTED CLOSE?
-------------------
Raw closing prices are discontinuous at dividend ex-dates and split dates.
Adjusted close prices are restated so that the entire history reflects
what an investor who reinvested all dividends would have received.
This is the correct price series for return calculations.

CACHING STRATEGY
----------------
If a raw CSV already exists on disk, we load from disk instead of
downloading again. This speeds up repeated runs and avoids hitting
Yahoo Finance rate limits. Delete data/raw/prices_raw.csv to force
a fresh download.
"""

import os
import time
import pandas as pd
import yfinance as yf
from typing import List

from src.config import (
    TICKERS,
    BENCHMARK_TICKER,
    START_DATE,
    END_DATE,
    RAW_PRICES_PATH,
    BENCHMARK_PATH,
)


def download_price_data(
    tickers: List[str],
    start: str,
    end: str,
    progress: bool = True,
) -> pd.DataFrame:
    """
    Download adjusted close prices for a list of tickers from Yahoo Finance.

    Parameters
    ----------
    tickers : list of str
        Ticker symbols, e.g. ["AAPL", "MSFT", "GOOGL"]
    start : str
        Start date in "YYYY-MM-DD" format (inclusive)
    end : str
        End date in "YYYY-MM-DD" format (inclusive)
    progress : bool
        If True, print download progress per ticker

    Returns
    -------
    pd.DataFrame
        DataFrame with DatetimeIndex and one column per ticker containing
        adjusted close prices. Columns are ordered to match `tickers`.
    """
    if progress:
        print(f"  Downloading data for {len(tickers)} tickers from {start} to {end}...")

    # Download all tickers in one batch call -- much faster than one-by-one
    raw = yf.download(
        tickers=tickers,
        start=start,
        end=end,
        auto_adjust=True,   # returns adjusted prices directly
        progress=False,     # suppress yfinance's own progress bar
        threads=True,       # parallel downloads
    )

    # yfinance returns a MultiIndex DataFrame; we want just the "Close" column
    # When auto_adjust=True, "Close" is the adjusted close price
    if isinstance(raw.columns, pd.MultiIndex):
        prices = raw["Close"]
    else:
        # Single ticker case (shouldn't happen here, but be safe)
        prices = raw[["Close"]]
        prices.columns = tickers

    # Ensure column order matches the requested ticker list
    available_tickers = [t for t in tickers if t in prices.columns]
    missing_tickers = [t for t in tickers if t not in prices.columns]

    if missing_tickers:
        print(f"  WARNING: Could not download data for: {missing_tickers}")

    prices = prices[available_tickers]
    prices.index.name = "Date"

    if progress:
        print(f"  Downloaded {len(prices)} trading days for {len(available_tickers)} tickers.")

    return prices


def download_benchmark(
    ticker: str = BENCHMARK_TICKER,
    start: str = START_DATE,
    end: str = END_DATE,
) -> pd.Series:
    """
    Download adjusted close prices for the benchmark index.

    Parameters
    ----------
    ticker : str
        Benchmark ticker symbol, e.g. "^GSPC" for S&P 500
    start : str
        Start date "YYYY-MM-DD"
    end : str
        End date "YYYY-MM-DD"

    Returns
    -------
    pd.Series
        Named Series with DatetimeIndex containing benchmark adjusted close prices.
    """
    print(f"  Downloading benchmark ({ticker}) from {start} to {end}...")

    raw = yf.download(
        tickers=ticker,
        start=start,
        end=end,
        auto_adjust=True,
        progress=False,
    )

    if isinstance(raw.columns, pd.MultiIndex):
        prices = raw["Close"].iloc[:, 0]
    else:
        prices = raw["Close"]

    prices.name = ticker
    prices.index.name = "Date"

    print(f"  Downloaded {len(prices)} trading days for benchmark.")
    return prices


def load_prices_from_disk(path) -> pd.DataFrame:
    """
    Load previously saved price data from a CSV file.

    Parameters
    ----------
    path : str or Path
        Path to the CSV file

    Returns
    -------
    pd.DataFrame
        DataFrame with DatetimeIndex and ticker columns
    """
    df = pd.read_csv(path, index_col="Date", parse_dates=True)
    df.index = pd.to_datetime(df.index)
    df.index.name = "Date"
    return df


def save_prices_to_disk(prices: pd.DataFrame, path) -> None:
    """
    Save price data to CSV for caching.

    Parameters
    ----------
    prices : pd.DataFrame
        Price DataFrame to save
    path : str or Path
        Destination file path
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    prices.to_csv(path)


def get_price_data(
    tickers: list[str] = TICKERS,
    start: str = START_DATE,
    end: str = END_DATE,
    force_download: bool = False,
) -> pd.DataFrame:
    """
    Main entry point: get price data from cache or download fresh.

    Checks if the raw CSV already exists on disk. If it does, loads from disk.
    If not (or if force_download=True), downloads from Yahoo Finance and saves.

    Parameters
    ----------
    tickers : list of str
        Ticker symbols
    start : str
        Start date "YYYY-MM-DD"
    end : str
        End date "YYYY-MM-DD"
    force_download : bool
        If True, download fresh data even if cache exists

    Returns
    -------
    pd.DataFrame
        Raw (uncleaned) adjusted close prices
    """
    if not force_download and RAW_PRICES_PATH.exists():
        print(f"  Loading cached raw data from {RAW_PRICES_PATH}")
        prices = load_prices_from_disk(RAW_PRICES_PATH)

        # Check if cached data matches requested tickers
        cached_tickers = set(prices.columns)
        requested_tickers = set(tickers)
        if not requested_tickers.issubset(cached_tickers):
            missing = requested_tickers - cached_tickers
            print(f"  Cached data missing tickers {missing}. Re-downloading...")
            force_download = True

    if force_download or not RAW_PRICES_PATH.exists():
        prices = download_price_data(tickers, start, end)
        save_prices_to_disk(prices, RAW_PRICES_PATH)
        print(f"  Raw data saved to {RAW_PRICES_PATH}")

    return prices


def get_benchmark_data(
    ticker: str = BENCHMARK_TICKER,
    start: str = START_DATE,
    end: str = END_DATE,
    force_download: bool = False,
) -> pd.Series:
    """
    Get benchmark price data from cache or download fresh.

    Parameters
    ----------
    ticker : str
        Benchmark ticker
    start, end : str
        Date range
    force_download : bool
        Force fresh download

    Returns
    -------
    pd.Series
        Benchmark adjusted close prices
    """
    if not force_download and BENCHMARK_PATH.exists():
        print(f"  Loading cached benchmark from {BENCHMARK_PATH}")
        df = load_prices_from_disk(BENCHMARK_PATH)
        return df.iloc[:, 0]

    benchmark = download_benchmark(ticker, start, end)
    save_prices_to_disk(benchmark.to_frame(), BENCHMARK_PATH)
    print(f"  Benchmark data saved to {BENCHMARK_PATH}")
    return benchmark
