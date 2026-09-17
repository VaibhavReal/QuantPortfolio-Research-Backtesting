"""
test_returns.py
===============
Tests for src/returns.py

All tests use deterministic, manually verifiable data.
No external data downloads are required.
"""

import pytest
import numpy as np
import pandas as pd
from src.returns import (
    compute_simple_returns,
    compute_log_returns,
    compute_cumulative_returns,
    compute_annualized_return,
    compute_portfolio_daily_returns,
)


def test_compute_simple_returns_two_prices():
    """Test simple returns: [100, 110] → return of exactly 0.10 (10%)."""
    prices = pd.DataFrame({"A": [100.0, 110.0]})
    returns = compute_simple_returns(prices)
    # Should have 1 row (first row dropped as no previous price)
    assert len(returns) == 1
    np.testing.assert_allclose(returns["A"].values, [0.10], rtol=1e-9)


def test_compute_simple_returns_multiple_assets():
    """Test simple returns with a 2-asset DataFrame."""
    prices = pd.DataFrame({"A": [100.0, 110.0, 99.0], "B": [50.0, 55.0, 55.0]})
    returns = compute_simple_returns(prices)
    # [100→110 = 10%, 110→99 = -10%]
    np.testing.assert_allclose(returns["A"].values, [0.10, -0.10], rtol=1e-6)
    # [50→55 = 10%, 55→55 = 0%]
    np.testing.assert_allclose(returns["B"].values, [0.10, 0.0], rtol=1e-6)


def test_compute_log_returns_known_value():
    """Test log returns: ln(110/100) = ln(1.10) ≈ 0.09531."""
    prices = pd.DataFrame({"A": [100.0, 110.0]})
    log_rets = compute_log_returns(prices)
    expected = np.log(110.0 / 100.0)
    np.testing.assert_allclose(log_rets["A"].values, [expected], rtol=1e-9)


def test_compute_cumulative_returns_two_periods():
    """Test cumulative return: (1+0.10)*(1+0.05) - 1 = 0.155."""
    simple_returns = pd.Series([0.10, 0.05])
    cum_ret = compute_cumulative_returns(simple_returns)
    # cum_ret is a Series; check last value
    np.testing.assert_allclose(float(cum_ret.iloc[-1]), 0.155, rtol=1e-9)


def test_compute_cumulative_returns_all_zeros():
    """Test that all-zero returns produce a cumulative return of 0."""
    zeros = pd.Series([0.0, 0.0, 0.0])
    cum_ret = compute_cumulative_returns(zeros)
    # All values in the cumulative return should be 0
    np.testing.assert_allclose(cum_ret.values, [0.0, 0.0, 0.0], atol=1e-10)


def test_compute_cumulative_returns_empty_series():
    """Test cumulative returns on an empty series returns empty series."""
    empty = pd.Series([], dtype=float)
    cum_ret = compute_cumulative_returns(empty)
    assert len(cum_ret) == 0


def test_compute_annualized_return_cagr():
    """
    Test CAGR: a 25% total return over exactly 252 trading days → CAGR = 25%.

    Formula: CAGR = (1 + cum_return)^(252/n_days) - 1
    When n_days = 252: CAGR = (1.25)^1 - 1 = 0.25.
    """
    cagr = compute_annualized_return(0.25, n_trading_days=252)
    assert cagr == pytest.approx(0.25, rel=1e-9)


def test_simple_and_log_returns_approximately_equal_for_small_changes():
    """
    For small daily price moves (~0.1%), simple return ≈ log return.

    Because ln(1+x) ≈ x for small x. This is a key approximation used
    to justify using either return type for daily data.
    """
    prices = pd.DataFrame({"A": [100.0, 100.1]})  # 0.1% change
    simp_ret = float(compute_simple_returns(prices)["A"].iloc[0])
    log_ret = float(compute_log_returns(prices)["A"].iloc[0])
    np.testing.assert_allclose(simp_ret, log_ret, atol=1e-5)


def test_compute_portfolio_daily_returns_weighted_average():
    """
    Portfolio return = weighted sum of asset returns.

    w = [0.6, 0.4], r = [0.01, 0.02] → Rp = 0.6*0.01 + 0.4*0.02 = 0.014
    """
    weights = np.array([0.6, 0.4])
    returns = pd.DataFrame({"A": [0.01, -0.01], "B": [0.02, 0.01]})
    port_rets = compute_portfolio_daily_returns(weights, returns)
    expected = [0.6 * 0.01 + 0.4 * 0.02, 0.6 * (-0.01) + 0.4 * 0.01]
    np.testing.assert_allclose(port_rets.values, expected, rtol=1e-9)
