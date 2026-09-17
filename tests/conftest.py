import pytest
import numpy as np
import pandas as pd

@pytest.fixture
def sample_prices():
    """Sample prices for 2 assets over 5 days."""
    dates = pd.date_range("2023-01-01", periods=5)
    data = {
        "AssetA": [100.0, 105.0, 102.0, 108.0, 110.0],
        "AssetB": [50.0, 52.0, 55.0, 54.0, 58.0]
    }
    return pd.DataFrame(data, index=dates)

@pytest.fixture
def sample_cov_matrix_2x2():
    """Sample 2x2 covariance matrix."""
    return np.array([
        [0.04, 0.01],
        [0.01, 0.06]
    ])

@pytest.fixture
def sample_cov_matrix_3x3():
    """Sample 3x3 positive definite covariance matrix."""
    return np.array([
        [0.05, 0.01, 0.02],
        [0.01, 0.06, 0.015],
        [0.02, 0.015, 0.08]
    ])
