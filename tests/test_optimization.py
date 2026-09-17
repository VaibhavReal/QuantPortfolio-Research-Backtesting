import pytest
import numpy as np
import pandas as pd
from src.optimization import (
    minimum_variance_weights,
    risk_parity_weights,
    compute_risk_contributions,
    compute_covariance_matrix
)

def test_minimum_variance_weights_sum_to_one(sample_cov_matrix_3x3):
    """Test minimum variance weights sum to 1.0."""
    w = minimum_variance_weights(sample_cov_matrix_3x3)
    assert np.sum(w) == pytest.approx(1.0, abs=1e-6)

def test_minimum_variance_weights_non_negative(sample_cov_matrix_3x3):
    """Test minimum variance weights are non-negative."""
    w = minimum_variance_weights(sample_cov_matrix_3x3)
    assert np.all(w >= -1e-6)

def test_minimum_variance_weights_uncorrelated():
    """Test minimum variance weights favor lower variance assets when uncorrelated."""
    cov = np.array([
        [0.01, 0.0],
        [0.0, 0.09]
    ])
    w = minimum_variance_weights(cov)
    # Inverse variance weighting: 1/0.01=100, 1/0.09=11.11 -> 90%, 10%
    np.testing.assert_allclose(w, [0.9, 0.1], atol=1e-4)

def test_risk_parity_weights_sum_to_one(sample_cov_matrix_3x3):
    """Test risk parity weights sum to 1.0."""
    w = risk_parity_weights(sample_cov_matrix_3x3)
    assert np.sum(w) == pytest.approx(1.0, abs=1e-6)

def test_risk_parity_weights_non_negative(sample_cov_matrix_3x3):
    """Test risk parity weights are all non-negative."""
    w = risk_parity_weights(sample_cov_matrix_3x3)
    assert np.all(w >= -1e-6)

def test_risk_parity_weights_equal_variance():
    """Test risk parity weights are equal for equal-variance uncorrelated assets."""
    cov = np.array([
        [0.04, 0.0],
        [0.0, 0.04]
    ])
    w = risk_parity_weights(cov)
    np.testing.assert_allclose(w, [0.5, 0.5])

def test_compute_risk_contributions(sample_cov_matrix_3x3):
    """
    Test that percentage risk contributions sum to 1.0.

    Our compute_risk_contributions() returns PERCENTAGE risk contributions
    (each RC_i / portfolio_vol), which sum to 1.0 (i.e., 100% of portfolio risk).
    This is the convention used for display and for the risk-parity objective function.
    """
    w = np.array([0.4, 0.3, 0.3])
    rc = compute_risk_contributions(w, sample_cov_matrix_3x3)
    assert np.sum(rc) == pytest.approx(1.0, abs=1e-6)

def test_compute_covariance_matrix_symmetric():
    """Test computed covariance matrix is symmetric."""
    returns = pd.DataFrame({
        "A": [0.01, -0.02, 0.03, 0.01],
        "B": [-0.01, 0.01, 0.02, -0.03]
    })
    cov = compute_covariance_matrix(returns)
    np.testing.assert_allclose(cov, cov.T)

def test_compute_covariance_matrix_psd():
    """Test computed covariance matrix is positive semi-definite."""
    returns = pd.DataFrame({
        "A": [0.01, -0.02, 0.03, 0.01],
        "B": [-0.01, 0.01, 0.02, -0.03],
        "C": [0.0, 0.0, 0.0, 0.0]
    })
    cov = compute_covariance_matrix(returns)
    eigenvalues = np.linalg.eigvalsh(cov)
    assert np.all(eigenvalues >= -1e-8)
