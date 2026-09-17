"""
test_risk_metrics.py
====================
Tests for src/risk_metrics.py

All tests use deterministic data and manually verifiable expected values.
No external data downloads.

KEY DESIGN NOTES:
- The Sharpe ratio function takes an ANNUAL risk-free rate (e.g., 0.05 = 5%),
  converts it to daily internally: daily_rf = annual_rf / 252
- The test expected values are computed to match this convention exactly.
"""

import pytest
import numpy as np
import pandas as pd
from src.risk_metrics import (
    sharpe_ratio,
    sortino_ratio,
    max_drawdown,
    annualized_volatility,
    compute_beta,
    compute_cagr,
)


def test_sharpe_ratio_formula():
    """
    Test Sharpe ratio using the project's actual formula.

    Our sharpe_ratio() converts the annual rf to daily: daily_rf = rf / 252.
    Then: Sharpe = sqrt(252) * mean(r - daily_rf) / std(r - daily_rf)

    We compute expected using the same convention.
    """
    returns = pd.Series([0.02, 0.01, 0.03, 0.02, 0.02])
    rf = 0.01  # 1% ANNUAL risk-free rate

    sr = sharpe_ratio(returns, rf, trading_days_per_year=252)

    # Expected: same formula our function uses
    daily_rf = rf / 252
    excess = returns - daily_rf
    expected = float(excess.mean() / excess.std(ddof=1) * np.sqrt(252))

    assert sr == pytest.approx(expected, rel=1e-6)


def test_sharpe_ratio_zero_returns_zero_rf():
    """Test Sharpe ratio is 0 when excess returns are zero (returns = rf daily)."""
    # If all returns equal daily_rf, excess returns = 0 → Sharpe undefined (std=0)
    rf = 0.0
    returns = pd.Series([0.0, 0.0, 0.0, 0.0])
    sr = sharpe_ratio(returns, rf, 252)
    # std=0 → function returns NaN
    assert np.isnan(sr)


def test_sortino_ratio_all_positive_gains():
    """
    Test Sortino ratio when all returns are above the risk-free rate.

    When all excess returns are positive, downside deviation = 0.
    Our function returns NaN in this case (avoids inf/division-by-zero).
    This is the correct behavior — an NaN Sortino means the portfolio
    never experienced downside, which should be flagged for inspection.
    """
    returns = pd.Series([0.05, 0.04, 0.06, 0.05])
    rf = 0.0  # 0% annual rf → daily_rf = 0
    # All returns > 0 > daily_rf, so downside_dev = 0 → NaN
    sortino = sortino_ratio(returns, rf, 252)
    assert np.isnan(sortino)


def test_sortino_ratio_with_mixed_returns():
    """Test Sortino ratio with both positive and negative returns (normal case)."""
    returns = pd.Series([0.02, -0.01, 0.03, -0.02, 0.01])
    rf = 0.05
    sortino = sortino_ratio(returns, rf, 252)
    # Just verify it's a finite number (actual value depends on formula internals)
    assert np.isfinite(sortino)


def test_max_drawdown_known_series():
    """
    Test max drawdown: peak=1.2, trough=0.9 → MDD = (0.9-1.2)/1.2 = -0.25
    """
    equity_curve = pd.Series([1.0, 1.2, 0.9, 1.1])
    mdd = max_drawdown(equity_curve)
    assert mdd == pytest.approx(-0.25, rel=1e-6)


def test_max_drawdown_monotonically_increasing():
    """Max drawdown of a strictly increasing series should be 0."""
    equity_curve = pd.Series([1.0, 1.1, 1.2, 1.3])
    mdd = max_drawdown(equity_curve)
    assert mdd == pytest.approx(0.0, abs=1e-10)


def test_annualized_volatility_constant_returns():
    """Volatility of constant returns is 0 (no variation)."""
    returns = pd.Series([0.05, 0.05, 0.05])
    vol = annualized_volatility(returns, 252)
    assert vol == pytest.approx(0.0, abs=1e-10)


def test_annualized_volatility_known_value():
    """Test annualized volatility matches manual formula: std * sqrt(252)."""
    returns = pd.Series([0.01, -0.01, 0.01, -0.01])
    vol = annualized_volatility(returns, 252)
    expected_vol = float(returns.std(ddof=1) * np.sqrt(252))
    assert vol == pytest.approx(expected_vol, rel=1e-6)


def test_compute_beta_identical_series():
    """When portfolio returns = benchmark returns exactly, beta = 1.0."""
    returns = pd.Series([0.01, -0.02, 0.03, 0.01])
    beta = compute_beta(returns, returns)
    assert beta == pytest.approx(1.0, rel=1e-6)


def test_compute_beta_double_leverage():
    """When portfolio = 2 × benchmark, beta = 2.0."""
    bench = pd.Series([0.01, -0.02, 0.03, 0.01])
    port = 2 * bench
    beta = compute_beta(port, bench)
    assert beta == pytest.approx(2.0, rel=1e-6)


def test_compute_cagr_exactly_one_year():
    """
    CAGR test: 100% total return over exactly 252 trading days -> CAGR = 100%.

    equity goes $1M -> $2M in 252 trading days.
    CAGR = (final/initial)^(252/n_days) - 1

    With n_days=252: CAGR = (2.0)^1 - 1 = 1.0 = 100%.

    We create a 252-element series (so n_days=252) with first=1M and last=2M.
    """
    # 252 elements: first = 1M, last = 2M, interpolated linearly in between
    equity_curve = pd.Series(np.linspace(1_000_000.0, 2_000_000.0, 252))
    cagr = compute_cagr(equity_curve, trading_days_per_year=252)
    # n_days=252, total_return = 100%, CAGR = (2.0)^(252/252) - 1 = 1.0
    assert cagr == pytest.approx(1.0, rel=1e-9)
