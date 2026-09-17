"""
config.py
=========
Central configuration for the Quantitative Portfolio Research & Backtesting Platform.

All project-wide settings live here. To change the stock universe, date range, or any
parameter, edit only this file — nothing else needs to change.

WHY A SMALL UNIVERSE (10-15 STOCKS)?
--------------------------------------
We intentionally start with 12 liquid, well-known stocks:
  - Portfolio mathematics is easier to understand and verify
  - Covariance matrix is small (12x12) and well-conditioned
  - Each asset can be individually inspected and reasoned about
  - Optimization is fast and numerically stable
  - Debugging and validation are straightforward
  - The project is easier to explain in a technical interview

SCALABILITY PATH
----------------
This config is the ONLY place tickers are defined. To scale up:
  Phase 2 (25-50 stocks): add tickers to TICKERS list, ensure data quality checks
  Phase 3 (100+ stocks):  consider chunked covariance estimation, parallel downloads,
                          shrinkage estimators (Ledoit-Wolf), and DuckDB partitioning.
  See docs/future_improvements.md for full details.
"""

import os
from pathlib import Path

# ─────────────────────────────────────────────
#  PROJECT ROOT
# ─────────────────────────────────────────────
ROOT_DIR = Path(__file__).resolve().parent.parent

# ─────────────────────────────────────────────
#  STOCK UNIVERSE  ← the only place tickers live
# ─────────────────────────────────────────────
# 12 large-cap, liquid US equities selected for:
#   • Sector diversification (Tech, Finance, Healthcare, Consumer, Energy, etc.)
#   • Long continuous price history (all pre-2010)
#   • High average daily volume → low bid-ask spread → realistic to trade
#   • Well-known companies → easy to discuss in interviews
#
# BRK-B is used instead of BRK-A because it is more liquid and cheaper per share.

TICKERS = [
    "AAPL",   # Apple Inc.               — Technology
    "MSFT",   # Microsoft Corp.          — Technology
    "GOOGL",  # Alphabet Inc. Class A    — Communication Services
    "JPM",    # JPMorgan Chase & Co.     — Financials
    "JNJ",    # Johnson & Johnson        — Healthcare
    "PG",     # Procter & Gamble Co.     — Consumer Staples
    "XOM",    # ExxonMobil Corp.         — Energy
    "CAT",    # Caterpillar Inc.         — Industrials
    "AMZN",   # Amazon.com Inc.          — Consumer Discretionary
    "BRK-B",  # Berkshire Hathaway B     — Financials (diversified)
    "LLY",    # Eli Lilly & Co.          — Healthcare (pharma)
    "NEE",    # NextEra Energy Inc.      — Utilities
]

N_ASSETS = len(TICKERS)

# ─────────────────────────────────────────────
#  BENCHMARK
# ─────────────────────────────────────────────
# S&P 500 Total Return index via Yahoo Finance
BENCHMARK_TICKER = "^GSPC"
BENCHMARK_NAME = "S&P 500"

# ─────────────────────────────────────────────
#  DATE RANGE
# ─────────────────────────────────────────────
# 5 full calendar years (2019–2024):
#   • Pre-COVID bull market (2019)
#   • COVID crash & recovery (2020)
#   • Post-COVID bull run (2021)
#   • Rate-hike bear market (2022)
#   • Soft-landing recovery (2023-2024)
# This gives meaningful stress-test coverage across different market regimes.

START_DATE = "2019-01-01"
END_DATE = "2024-12-31"

# ─────────────────────────────────────────────
#  BACKTESTING PARAMETERS
# ─────────────────────────────────────────────
INITIAL_CAPITAL = 1_000_000      # USD — $1 million starting portfolio

# Rebalance frequency: how often portfolio weights are reset to target
# "monthly"   → rebalance approximately every 21 trading days
# "quarterly" → rebalance approximately every 63 trading days
REBALANCE_FREQ = "monthly"

# Minimum number of trading days required in the estimation window
# before we start computing weights. Ensures the covariance matrix
# is computed on sufficient data.
MIN_ESTIMATION_DAYS = 63         # ~3 months of trading data

# ─────────────────────────────────────────────
#  RISK & COST PARAMETERS
# ─────────────────────────────────────────────
# Annual risk-free rate (used in Sharpe, Sortino, etc.)
# 5% approximates the average US 10-year Treasury yield over 2019-2024.
# This is configurable — changing it affects all ratio calculations.
RISK_FREE_RATE = 0.05

# Transaction cost as a fraction of trade value.
# 10 basis points (0.10%) per transaction.
# This is a simplified research assumption:
#   - Does NOT model bid-ask spread, market impact, or slippage
#   - Applied symmetrically to buys and sells
#   - See docs/limitations.md for the full list of simplifications
TRANSACTION_COST_PCT = 0.001     # 10 bps

# Number of trading days per year (used for annualization)
TRADING_DAYS_PER_YEAR = 252

# ─────────────────────────────────────────────
#  PATHS
# ─────────────────────────────────────────────
DATA_DIR = ROOT_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
EXPORTS_DIR = DATA_DIR / "exports"

# Raw price file downloaded from yfinance
RAW_PRICES_PATH = RAW_DATA_DIR / "prices_raw.csv"

# Cleaned adjusted-close prices (used by all downstream modules)
CLEAN_PRICES_PATH = PROCESSED_DATA_DIR / "prices_clean.csv"

# Benchmark price file
BENCHMARK_PATH = PROCESSED_DATA_DIR / "benchmark_clean.csv"

# DuckDB database file
DB_PATH = ROOT_DIR / "quant_portfolio.duckdb"

# ─────────────────────────────────────────────
#  ASSET METADATA
# ─────────────────────────────────────────────
# Human-readable info for each ticker (used in SQL, dashboards, reports)
ASSET_INFO = {
    "AAPL":  {"name": "Apple Inc.",              "sector": "Technology",               "exchange": "NASDAQ"},
    "MSFT":  {"name": "Microsoft Corp.",          "sector": "Technology",               "exchange": "NASDAQ"},
    "GOOGL": {"name": "Alphabet Inc.",            "sector": "Communication Services",   "exchange": "NASDAQ"},
    "JPM":   {"name": "JPMorgan Chase & Co.",     "sector": "Financials",               "exchange": "NYSE"},
    "JNJ":   {"name": "Johnson & Johnson",        "sector": "Healthcare",               "exchange": "NYSE"},
    "PG":    {"name": "Procter & Gamble Co.",     "sector": "Consumer Staples",         "exchange": "NYSE"},
    "XOM":   {"name": "ExxonMobil Corp.",         "sector": "Energy",                   "exchange": "NYSE"},
    "CAT":   {"name": "Caterpillar Inc.",         "sector": "Industrials",              "exchange": "NYSE"},
    "AMZN":  {"name": "Amazon.com Inc.",          "sector": "Consumer Discretionary",   "exchange": "NASDAQ"},
    "BRK-B": {"name": "Berkshire Hathaway B",     "sector": "Financials",               "exchange": "NYSE"},
    "LLY":   {"name": "Eli Lilly & Co.",          "sector": "Healthcare",               "exchange": "NYSE"},
    "NEE":   {"name": "NextEra Energy Inc.",      "sector": "Utilities",               "exchange": "NYSE"},
}

# ─────────────────────────────────────────────
#  STRATEGY NAMES  (used as keys throughout)
# ─────────────────────────────────────────────
STRATEGY_EQUAL_WEIGHT = "Equal Weight"
STRATEGY_MIN_VARIANCE = "Minimum Variance"
STRATEGY_RISK_PARITY  = "Risk Parity"

ALL_STRATEGIES = [
    STRATEGY_EQUAL_WEIGHT,
    STRATEGY_MIN_VARIANCE,
    STRATEGY_RISK_PARITY,
]

# ─────────────────────────────────────────────
#  CONVENIENCE: ensure output directories exist
# ─────────────────────────────────────────────
for _dir in [RAW_DATA_DIR, PROCESSED_DATA_DIR, EXPORTS_DIR]:
    _dir.mkdir(parents=True, exist_ok=True)
