"""
database.py
===========
DuckDB storage layer for the quantitative portfolio platform.

Optimized for ultra-fast, vectorized bulk ingestion using DuckDB's native
zero-copy pandas DataFrame registration.
"""

from pathlib import Path
from typing import Dict, List, Optional
import duckdb
import pandas as pd
import numpy as np
from datetime import date as date_type

from src.config import (
    DB_PATH,
    TICKERS,
    ASSET_INFO,
    ALL_STRATEGIES,
    BENCHMARK_NAME,
)

STRATEGY_DESCRIPTIONS = {
    "Equal Weight": "Equal allocation across all universe assets (1/N)",
    "Minimum Variance": "Quadratic optimization minimizing total portfolio variance",
    "Risk Parity": "Equal risk contribution allocation across all assets",
}


def get_connection(db_path: Optional[Path] = None) -> duckdb.DuckDBPyConnection:
    """Get or create a DuckDB connection."""
    if db_path is None:
        db_path = DB_PATH
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(db_path))


def init_db(conn: duckdb.DuckDBPyConnection) -> None:
    """
    Initialize the database schema with all required tables and indexes.
    """
    conn.execute("""
        CREATE TABLE IF NOT EXISTS assets (
            asset_id   INTEGER PRIMARY KEY,
            ticker     VARCHAR UNIQUE NOT NULL,
            name       VARCHAR,
            sector     VARCHAR,
            exchange   VARCHAR
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS price_data (
            price_id   INTEGER PRIMARY KEY,
            asset_id   INTEGER NOT NULL REFERENCES assets(asset_id),
            date       DATE NOT NULL,
            adj_close  DOUBLE NOT NULL,
            UNIQUE (asset_id, date)
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS strategies (
            strategy_id  INTEGER PRIMARY KEY,
            name         VARCHAR UNIQUE NOT NULL,
            description  VARCHAR
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS portfolio_weights (
            weight_id    INTEGER PRIMARY KEY,
            strategy_id  INTEGER NOT NULL REFERENCES strategies(strategy_id),
            asset_id     INTEGER NOT NULL REFERENCES assets(asset_id),
            date         DATE NOT NULL,
            weight       DOUBLE NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS backtest_results (
            result_id        INTEGER PRIMARY KEY,
            strategy_id      INTEGER NOT NULL REFERENCES strategies(strategy_id),
            date             DATE NOT NULL,
            portfolio_value  DOUBLE NOT NULL,
            daily_return     DOUBLE,
            UNIQUE (strategy_id, date)
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS risk_metrics (
            metric_id     INTEGER PRIMARY KEY,
            strategy_id   INTEGER NOT NULL REFERENCES strategies(strategy_id),
            metric_name   VARCHAR NOT NULL,
            metric_value  DOUBLE,
            computed_date DATE,
            UNIQUE (strategy_id, metric_name)
        )
    """)

    print("  Database tables initialized.")


def _get_or_create_asset_ids(conn: duckdb.DuckDBPyConnection) -> Dict[str, int]:
    """Insert static assets and return ticker -> asset_id mapping."""
    asset_rows = []
    for i, ticker in enumerate(TICKERS, start=1):
        info = ASSET_INFO.get(ticker, {})
        asset_rows.append({
            "asset_id": i,
            "ticker": ticker,
            "name": info.get("name"),
            "sector": info.get("sector"),
            "exchange": info.get("exchange"),
        })
    
    df_assets = pd.DataFrame(asset_rows)
    conn.register("_temp_asset_meta", df_assets)
    conn.execute("""
        INSERT OR IGNORE INTO assets (asset_id, ticker, name, sector, exchange)
        SELECT asset_id, ticker, name, sector, exchange FROM _temp_asset_meta
    """)
    conn.unregister("_temp_asset_meta")

    rows = conn.execute("SELECT ticker, asset_id FROM assets").fetchall()
    return {ticker: asset_id for ticker, asset_id in rows}


def _get_or_create_strategy_ids(conn: duckdb.DuckDBPyConnection) -> Dict[str, int]:
    """Insert static strategies and return strategy_name -> strategy_id mapping."""
    strat_rows = []
    for i, name in enumerate(ALL_STRATEGIES, start=1):
        strat_rows.append({
            "strategy_id": i,
            "name": name,
            "description": STRATEGY_DESCRIPTIONS.get(name, ""),
        })

    # Benchmark as a strategy
    bm_id = len(ALL_STRATEGIES) + 1
    strat_rows.append({
        "strategy_id": bm_id,
        "name": BENCHMARK_NAME,
        "description": "S&P 500 Index benchmark",
    })

    df_strats = pd.DataFrame(strat_rows)
    conn.register("_temp_strat_meta", df_strats)
    conn.execute("""
        INSERT OR IGNORE INTO strategies (strategy_id, name, description)
        SELECT strategy_id, name, description FROM _temp_strat_meta
    """)
    conn.unregister("_temp_strat_meta")

    rows = conn.execute("SELECT name, strategy_id FROM strategies").fetchall()
    return {name: sid for name, sid in rows}


def insert_price_data(conn: duckdb.DuckDBPyConnection, prices: pd.DataFrame) -> None:
    """Vectorized bulk insert of price data."""
    asset_ids = _get_or_create_asset_ids(conn)

    # Melt DataFrame from wide (Date x Ticker) to long (Date, Ticker, adj_close)
    df_long = prices.reset_index().melt(
        id_vars=["Date"], var_name="ticker", value_name="adj_close"
    ).dropna()

    df_long["asset_id"] = df_long["ticker"].map(asset_ids)
    df_long = df_long.dropna(subset=["asset_id"])
    df_long["asset_id"] = df_long["asset_id"].astype(int)
    df_long["date"] = pd.to_datetime(df_long["Date"]).dt.date
    df_long["price_id"] = np.arange(1, len(df_long) + 1)

    insert_df = df_long[["price_id", "asset_id", "date", "adj_close"]]

    conn.register("_temp_prices", insert_df)
    conn.execute("""
        INSERT OR IGNORE INTO price_data (price_id, asset_id, date, adj_close)
        SELECT price_id, asset_id, date, adj_close FROM _temp_prices
    """)
    conn.unregister("_temp_prices")
    print(f"  Inserted {len(insert_df)} price records into database.")


def insert_strategy_weights(conn: duckdb.DuckDBPyConnection, weights_df: pd.DataFrame) -> None:
    """Vectorized bulk insert of portfolio weights."""
    if weights_df.empty:
        print("  No weights to insert.")
        return

    asset_ids = _get_or_create_asset_ids(conn)
    strategy_ids = _get_or_create_strategy_ids(conn)

    df = weights_df.copy()
    df["asset_id"] = df["Ticker"].map(asset_ids)
    df["strategy_id"] = df["Strategy"].map(strategy_ids)
    df = df.dropna(subset=["asset_id", "strategy_id"])
    
    df["asset_id"] = df["asset_id"].astype(int)
    df["strategy_id"] = df["strategy_id"].astype(int)
    df["date"] = pd.to_datetime(df["Date"]).dt.date
    df["weight_id"] = np.arange(1, len(df) + 1)
    df["weight"] = df["Weight"].astype(float)

    insert_df = df[["weight_id", "strategy_id", "asset_id", "date", "weight"]]

    conn.register("_temp_weights", insert_df)
    conn.execute("""
        INSERT OR IGNORE INTO portfolio_weights (weight_id, strategy_id, asset_id, date, weight)
        SELECT weight_id, strategy_id, asset_id, date, weight FROM _temp_weights
    """)
    conn.unregister("_temp_weights")
    print(f"  Inserted {len(insert_df)} portfolio weight records into database.")


def insert_backtest_results(conn: duckdb.DuckDBPyConnection, backtest_results: Dict[str, Dict]) -> None:
    """Vectorized bulk insert of backtest equity curves."""
    strategy_ids = _get_or_create_strategy_ids(conn)

    dfs = []
    for strategy_name, result in backtest_results.items():
        if strategy_name not in strategy_ids:
            continue
        sid = strategy_ids[strategy_name]
        v = result["portfolio_values"]
        r = result["daily_returns"]
        df_strat = pd.DataFrame({
            "strategy_id": sid,
            "date": pd.to_datetime(v.index).date,
            "portfolio_value": v.values.astype(float),
            "daily_return": r.reindex(v.index).values.astype(float),
        })
        dfs.append(df_strat)

    if not dfs:
        return

    combined = pd.concat(dfs, ignore_index=True)
    combined["result_id"] = np.arange(1, len(combined) + 1)
    insert_df = combined[["result_id", "strategy_id", "date", "portfolio_value", "daily_return"]]

    conn.register("_temp_bt_results", insert_df)
    conn.execute("""
        INSERT OR IGNORE INTO backtest_results (result_id, strategy_id, date, portfolio_value, daily_return)
        SELECT result_id, strategy_id, date, portfolio_value, daily_return FROM _temp_bt_results
    """)
    conn.unregister("_temp_bt_results")
    print(f"  Inserted {len(insert_df)} backtest result records into database.")


def insert_risk_metrics(conn: duckdb.DuckDBPyConnection, all_metrics: Dict[str, Dict]) -> None:
    """Vectorized bulk insert of risk metrics."""
    strategy_ids = _get_or_create_strategy_ids(conn)
    computed_date = date_type.today()

    rows = []
    metric_id = 1
    for strategy_name, metrics in all_metrics.items():
        if strategy_name not in strategy_ids:
            continue
        sid = strategy_ids[strategy_name]
        for metric_name, value in metrics.items():
            if metric_name == "Strategy":
                continue
            rows.append({
                "metric_id": metric_id,
                "strategy_id": sid,
                "metric_name": str(metric_name),
                "metric_value": float(value) if value is not None and not (isinstance(value, float) and np.isnan(value)) else None,
                "computed_date": computed_date,
            })
            metric_id += 1

    if not rows:
        return

    insert_df = pd.DataFrame(rows)
    conn.register("_temp_risk_metrics", insert_df)
    conn.execute("""
        INSERT OR IGNORE INTO risk_metrics (metric_id, strategy_id, metric_name, metric_value, computed_date)
        SELECT metric_id, strategy_id, metric_name, metric_value, computed_date FROM _temp_risk_metrics
    """)
    conn.unregister("_temp_risk_metrics")
    print(f"  Inserted {len(insert_df)} risk metric records into database.")


def store_all_results(
    prices: pd.DataFrame,
    backtest_results: Dict[str, Dict],
    combined_weights: pd.DataFrame,
    all_metrics: Dict[str, Dict],
    db_path: Optional[Path] = None,
) -> None:
    """Store all platform results into DuckDB with fast bulk insertion."""
    print(f"  Connecting to DuckDB at {db_path or DB_PATH}")
    conn = get_connection(db_path)
    try:
        init_db(conn)
        insert_price_data(conn, prices)
        insert_strategy_weights(conn, combined_weights)
        insert_backtest_results(conn, backtest_results)
        insert_risk_metrics(conn, all_metrics)
        print("  All data stored to DuckDB successfully.")
    finally:
        conn.close()
