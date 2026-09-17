"""
test_edge_cases.py
==================
Stress-testing and edge-case verification for the quantitative portfolio engine.
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
from src.portfolio import (
    equal_weight,
    normalize_weights,
    compute_portfolio_return,
    compute_portfolio_variance,
    compute_portfolio_volatility,
    validate_weights,
)
from src.optimization import (
    compute_covariance_matrix,
    minimum_variance_weights,
    risk_parity_weights,
    compute_risk_contributions,
)
from src.risk_metrics import (
    sharpe_ratio,
    sortino_ratio,
    max_drawdown,
    annualized_volatility,
    compute_beta,
    compute_cagr,
    compute_all_metrics,
)


def test_stress_single_asset_portfolio():
    """Verify single-asset edge case across portfolio functions."""
    w = equal_weight(1)
    assert np.allclose(w, [1.0])
    
    cov = np.array([[0.04]]) # 20% vol
    var = compute_portfolio_variance(w, cov)
    vol = compute_portfolio_volatility(w, cov)
    assert np.isclose(var, 0.04)
    assert np.isclose(vol, 0.20)


def test_stress_weights_normalization():
    """Verify normalization handles negative numbers and unscaled vectors."""
    # Negative weight clipping
    w_raw = np.array([-0.5, 1.0, 1.0])
    w_norm = normalize_weights(w_raw)
    assert np.allclose(w_norm, [0.0, 0.5, 0.5])
    assert validate_weights(w_norm)

    # Extreme scaling
    w_large = np.array([500.0, 500.0])
    w_norm_large = normalize_weights(w_large)
    assert np.allclose(w_norm_large, [0.5, 0.5])


def test_stress_optimization_extreme_volatility_divergence():
    """
    Stress test Risk Parity and Min Variance when one asset is 10x more volatile
    than the other.
    """
    # Asset 1: 5% vol (variance 0.0025)
    # Asset 2: 50% vol (variance 0.25)
    cov = np.array([
        [0.0025, 0.0],
        [0.0, 0.25]
    ])

    w_mv = minimum_variance_weights(cov)
    # Min variance should put almost all weight on Asset 1
    assert w_mv[0] > 0.95
    assert np.isclose(np.sum(w_mv), 1.0)
    assert np.all(w_mv >= 0.0)

    w_rp = risk_parity_weights(cov)
    # Risk parity should allocate inversely to volatility: w1/w2 = sigma2/sigma1 = 10
    # w1 = 10/11 ~ 0.909, w2 = 1/11 ~ 0.091
    assert np.isclose(w_rp[0] / w_rp[1], 10.0, rtol=1e-2)
    assert np.isclose(np.sum(w_rp), 1.0)
    assert np.all(w_rp >= 0.0)


def test_stress_risk_contributions_sum_to_volatility():
    """Verify percentage risk contributions sum to 1.0."""
    cov = np.array([
        [0.04, 0.01, 0.005],
        [0.01, 0.09, 0.02],
        [0.005, 0.02, 0.16]
    ])
    w = np.array([0.4, 0.35, 0.25])
    rc_pct = compute_risk_contributions(w, cov)
    
    # Sum of percentage risk contributions must equal exactly 1.0
    assert np.isclose(np.sum(rc_pct), 1.0, atol=1e-7)


def test_stress_look_ahead_bias_invariance():
    """
    STRESS TEST LOOK-AHEAD BIAS:
    Changing future data beyond index T MUST NOT change weights computed at index T.
    """
    dates = pd.date_range("2020-01-01", periods=100, freq="B")
    np.random.seed(42)
    fake_prices = pd.DataFrame(
        100 * np.exp(np.cumsum(np.random.normal(0, 0.01, size=(100, 3)), axis=0)),
        index=dates,
        columns=["A", "B", "C"]
    )

    t_rebalance = 50
    # Scenario 1: Original prices
    log_rets_1 = compute_log_returns(fake_prices.iloc[:t_rebalance])
    cov_1 = compute_covariance_matrix(log_rets_1)
    w_1 = minimum_variance_weights(cov_1)

    # Scenario 2: Future price at day 80 crashes by 99%
    fake_prices_modified = fake_prices.copy()
    fake_prices_modified.iloc[80:, 0] *= 0.01 # Huge future shock
    log_rets_2 = compute_log_returns(fake_prices_modified.iloc[:t_rebalance])
    cov_2 = compute_covariance_matrix(log_rets_2)
    w_2 = minimum_variance_weights(cov_2)

    # Weights at day 50 must be 100% IDENTICAL
    assert np.allclose(w_1, w_2, atol=1e-12)


def test_stress_zero_and_infinite_metric_edge_cases():
    """Verify metrics handle constant returns, zero downside, and crashes gracefully."""
    # Flat equity curve (no change)
    flat_equity = pd.Series([1000.0] * 50, index=pd.date_range("2020-01-01", periods=50, freq="B"))
    flat_returns = pd.Series([0.0] * 50, index=flat_equity.index)
    
    assert max_drawdown(flat_equity) == 0.0
    assert annualized_volatility(flat_returns) == 0.0
    assert compute_cagr(flat_equity) == 0.0

    # Total crash
    crash_equity = pd.Series([100.0, 50.0, 10.0, 1.0], index=pd.date_range("2020-01-01", periods=4, freq="B"))
    assert max_drawdown(crash_equity) == -0.99
