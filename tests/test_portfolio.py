import pytest
import numpy as np
from src.portfolio import (
    equal_weight,
    normalize_weights,
    compute_portfolio_return,
    compute_portfolio_variance,
    compute_portfolio_volatility,
    validate_weights
)

def test_equal_weight_four_assets():
    """Test equal weights for 4 assets."""
    weights = equal_weight(4)
    np.testing.assert_allclose(weights, [0.25, 0.25, 0.25, 0.25])

def test_equal_weight_one_asset():
    """Test equal weights for 1 asset."""
    weights = equal_weight(1)
    np.testing.assert_allclose(weights, [1.0])

def test_normalize_weights_clips_negatives():
    """Test normalize weights clips negatives and renormalizes."""
    weights = np.array([-0.5, 1.0, 0.5])
    normalized = normalize_weights(weights)
    # Clipped to [0, 1.0, 0.5], sum is 1.5, normalized is [0, 1/1.5, 0.5/1.5]
    expected = [0.0, 1.0/1.5, 0.5/1.5]
    np.testing.assert_allclose(normalized, expected)

def test_normalize_weights_equal_positive():
    """Test normalize weights renormalizes [2.0, 2.0] to [0.5, 0.5]."""
    weights = np.array([2.0, 2.0])
    normalized = normalize_weights(weights)
    np.testing.assert_allclose(normalized, [0.5, 0.5])

def test_compute_portfolio_return():
    """Test portfolio return calculation."""
    w = np.array([0.5, 0.5])
    r = np.array([0.10, 0.20])
    port_ret = compute_portfolio_return(w, r)
    assert port_ret == pytest.approx(0.15)

def test_compute_portfolio_variance(sample_cov_matrix_2x2):
    """Test portfolio variance calculation with known covariance matrix."""
    w = np.array([0.5, 0.5])
    # w.T @ cov @ w = 0.5 * 0.5 * 0.04 + 0.5 * 0.5 * 0.06 + 2 * 0.5 * 0.5 * 0.01 = 0.01 + 0.015 + 0.005 = 0.03
    var = compute_portfolio_variance(w, sample_cov_matrix_2x2)
    assert var == pytest.approx(0.03)

def test_compute_portfolio_volatility(sample_cov_matrix_2x2):
    """Test portfolio volatility is the square root of variance."""
    w = np.array([0.5, 0.5])
    vol = compute_portfolio_volatility(w, sample_cov_matrix_2x2)
    assert vol == pytest.approx(np.sqrt(0.03))

def test_validate_weights_valid():
    """Test validation passes for valid weights."""
    assert validate_weights(np.array([0.5, 0.5])) is True

def test_validate_weights_sum_not_one():
    """Test validation fails when sum is not 1."""
    assert validate_weights(np.array([0.6, 0.6])) is False

def test_validate_weights_negative():
    """Test validation fails when weights are negative."""
    assert validate_weights(np.array([-0.1, 1.1])) is False
