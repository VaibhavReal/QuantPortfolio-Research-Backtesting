"""
optimization.py
===============
Portfolio optimization: Minimum Variance and Risk Parity strategies.

All optimization is implemented using scipy.optimize (no black-box
financial libraries). This keeps the mathematics visible and defensible.

MINIMUM VARIANCE OPTIMIZATION
-------------------------------
Solve the quadratic program:
    minimize    w^T Sigma w          (portfolio variance)
    subject to  sum(w) = 1           (fully invested)
                w_i >= 0             (long-only)
                w_i <= 1             (no single position > 100%)

We use scipy.optimize.minimize with the SLSQP solver (Sequential Least
Squares Programming), which handles both equality and inequality constraints.

WHY MINIMIZE VARIANCE?
  - "Safe" portfolio: minimizes risk without requiring return forecasts
  - Avoids the parameter sensitivity of mean-variance optimization
    (expected returns are notoriously hard to estimate well)
  - Well-understood and widely used in practice
  - Easy to explain in an interview

RISK PARITY
-----------
Risk parity targets equal risk contribution from each asset.

Risk Contribution of asset i:
    RC_i = w_i * (Sigma * w)_i / sigma_p

where (Sigma * w)_i is the i-th element of the matrix-vector product
and sigma_p = sqrt(w^T Sigma w) is total portfolio volatility.

In risk parity: RC_i = 1/N for all i

We solve this by minimizing the sum of squared differences between
risk contributions:
    minimize   sum_i sum_j (RC_i - RC_j)^2

This is implemented iteratively (the standard "Spinu" or SLSQP approach).

COVARIANCE MATRIX
-----------------
We estimate the covariance matrix from historical log returns and
annualize it (multiply daily cov by 252). The estimation window
depends on the context (full history for final weights, rolling
window in the backtest).

Note on conditioning: A covariance matrix that is not positive
definite can cause optimizer failures. We add a small regularization
term (epsilon * I) to ensure numerical stability. This is a standard
technique called Tikhonov regularization or "shrinkage toward identity".
"""

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from typing import Optional, List

from src.config import TRADING_DAYS_PER_YEAR


def compute_covariance_matrix(
    log_returns: pd.DataFrame,
    annualize: bool = True,
    regularize: bool = True,
    epsilon: float = 1e-8,
) -> np.ndarray:
    """
    Estimate the covariance matrix from historical log returns.

    Parameters
    ----------
    log_returns : pd.DataFrame
        Daily log returns, shape (n_days, n_assets)
    annualize : bool
        If True, multiply by TRADING_DAYS_PER_YEAR (252) to get annualized cov
    regularize : bool
        If True, add epsilon * I to ensure positive definiteness
    epsilon : float
        Regularization strength (small number, default 1e-8)

    Returns
    -------
    np.ndarray
        Covariance matrix, shape (n_assets, n_assets)
    """
    cov = log_returns.cov().values

    if annualize:
        cov = cov * TRADING_DAYS_PER_YEAR

    if regularize:
        # Add tiny diagonal term to prevent singular/ill-conditioned matrices
        # This has negligible effect on well-conditioned matrices
        cov = cov + epsilon * np.eye(len(cov))

    return cov


def compute_expected_returns(
    log_returns: pd.DataFrame,
    annualize: bool = True,
) -> np.ndarray:
    """
    Estimate expected returns as the historical mean of log returns.

    Annualized by multiplying daily mean by 252.
    Note: This is a naive estimator. Expected returns are notoriously
    difficult to estimate; this is why minimum variance is attractive
    (it doesn't require expected return estimates).

    Parameters
    ----------
    log_returns : pd.DataFrame
        Daily log returns
    annualize : bool
        If True, multiply by TRADING_DAYS_PER_YEAR

    Returns
    -------
    np.ndarray
        Expected annualized returns, shape (n_assets,)
    """
    mu = log_returns.mean().values
    if annualize:
        mu = mu * TRADING_DAYS_PER_YEAR
    return mu


def minimum_variance_weights(
    cov_matrix: np.ndarray,
    tol: float = 1e-9,
) -> np.ndarray:
    """
    Find the Minimum Variance Portfolio weights using constrained optimization.

    Solves:
        minimize   w^T * Sigma * w
        subject to sum(w) = 1
                   0 <= w_i <= 1  for all i

    Uses scipy.optimize.minimize with the SLSQP method.

    SLSQP (Sequential Least Squares Programming) is appropriate here because:
      - Handles equality constraints (sum = 1)
      - Handles inequality constraints (w >= 0)
      - Efficient for smooth convex problems (quadratic objective)
      - Widely used for portfolio optimization

    Parameters
    ----------
    cov_matrix : np.ndarray
        Annualized covariance matrix, shape (n_assets, n_assets)
    tol : float
        Optimization tolerance

    Returns
    -------
    np.ndarray
        Optimal weights, shape (n_assets,), all >= 0, sum = 1
    """
    n = cov_matrix.shape[0]

    # Objective: portfolio variance = w^T Sigma w
    def portfolio_variance(w: np.ndarray) -> float:
        return float(w @ cov_matrix @ w)

    # Gradient of portfolio variance w.r.t. w = 2 * Sigma * w
    # Providing the gradient speeds up convergence
    def portfolio_variance_grad(w: np.ndarray) -> np.ndarray:
        return 2 * cov_matrix @ w

    # Initial guess: equal weights (feasible starting point)
    w0 = np.ones(n) / n

    # Constraints
    constraints = [
        {"type": "eq", "fun": lambda w: w.sum() - 1.0}   # sum = 1
    ]

    # Bounds: 0 <= w_i <= 1 for all i (long-only)
    bounds = [(0.0, 1.0)] * n

    result = minimize(
        fun=portfolio_variance,
        jac=portfolio_variance_grad,
        x0=w0,
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
        options={"ftol": tol, "maxiter": 1000},
    )

    if not result.success:
        # Fall back to equal weight if optimizer fails
        # This can happen with very small estimation windows
        print(f"  WARNING: Min variance optimization failed: {result.message}. Using equal weight.")
        return np.ones(n) / n

    weights = result.x

    # Post-process: clip tiny negatives and renormalize
    weights = np.clip(weights, 0, None)
    weights = weights / weights.sum()

    return weights


def _risk_contributions(w: np.ndarray, cov_matrix: np.ndarray) -> np.ndarray:
    """
    Compute the risk contribution of each asset.

    Risk contribution of asset i:
        RC_i = w_i * (Sigma * w)_i / sigma_p

    where sigma_p = sqrt(w^T Sigma w) is portfolio volatility.

    The RC_i sum to sigma_p (total portfolio vol), so RC_i / sigma_p
    gives the fraction of portfolio risk contributed by asset i.

    Parameters
    ----------
    w : np.ndarray
        Portfolio weights
    cov_matrix : np.ndarray
        Covariance matrix

    Returns
    -------
    np.ndarray
        Risk contributions (sum to portfolio volatility)
    """
    portfolio_vol = np.sqrt(w @ cov_matrix @ w)
    if portfolio_vol < 1e-12:
        return np.zeros(len(w))

    # Marginal risk contribution: d?_p / dw_i = (Sigma * w)_i / sigma_p
    marginal_rc = (cov_matrix @ w) / portfolio_vol

    # Risk contribution: RC_i = w_i * marginal_RC_i
    rc = w * marginal_rc
    return rc


def risk_parity_weights(
    cov_matrix: np.ndarray,
    tol: float = 1e-10,
) -> np.ndarray:
    """
    Find Risk Parity portfolio weights.

    Risk parity targets equal risk contribution from each asset:
        RC_i = RC_j  for all i, j

    We implement this by minimizing the sum of squared pairwise
    differences between risk contributions:
        minimize   sum_i sum_j (RC_i/sigma_p - 1/N)^2

    This is equivalent to minimizing:
        sum_i (RC_i - sigma_p/N)^2

    Subject to the long-only, fully-invested constraints.

    WHY RISK PARITY?
      - Diversifies across risk, not capital
      - In equal-weight portfolios, high-volatility assets dominate risk
        despite having the same capital allocation
      - Risk parity counteracts this by underweighting volatile assets
      - Popularized by Ray Dalio's "All Weather" fund

    Parameters
    ----------
    cov_matrix : np.ndarray
        Annualized covariance matrix, shape (n_assets, n_assets)
    tol : float
        Optimization tolerance

    Returns
    -------
    np.ndarray
        Risk parity weights, shape (n_assets,), all >= 0, sum = 1
    """
    n = cov_matrix.shape[0]
    target_rc_fraction = 1.0 / n  # each asset should contribute 1/N of total risk

    def objective(w: np.ndarray) -> float:
        """
        Minimize sum of squared deviations from equal risk contribution.

        We use percentage risk contributions (RC_i / sigma_p) so the
        target is simply 1/N regardless of portfolio volatility.
        """
        portfolio_vol = np.sqrt(w @ cov_matrix @ w)
        if portfolio_vol < 1e-12:
            return 0.0

        rc = _risk_contributions(w, cov_matrix)
        # Percentage risk contributions
        rc_pct = rc / portfolio_vol
        # Sum of squared deviations from target (1/N)
        return float(np.sum((rc_pct - target_rc_fraction) ** 2))

    # Initial guess: equal weights (good starting point, already feasible)
    w0 = np.ones(n) / n

    constraints = [
        {"type": "eq", "fun": lambda w: w.sum() - 1.0}
    ]
    bounds = [(0.0, 1.0)] * n

    result = minimize(
        fun=objective,
        x0=w0,
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
        options={"ftol": tol, "maxiter": 2000},
    )

    if not result.success:
        print(f"  WARNING: Risk parity optimization failed: {result.message}. Using equal weight.")
        return np.ones(n) / n

    weights = result.x
    weights = np.clip(weights, 0, None)
    weights = weights / weights.sum()

    return weights


def compute_risk_contributions(
    weights: np.ndarray,
    cov_matrix: np.ndarray,
) -> pd.Series:
    """
    Compute and return risk contributions as a percentage Series.

    Parameters
    ----------
    weights : np.ndarray
        Portfolio weights
    cov_matrix : np.ndarray
        Annualized covariance matrix

    Returns
    -------
    pd.Series
        Percentage risk contributions (sum ? 1.0)
    """
    portfolio_vol = np.sqrt(weights @ cov_matrix @ weights)
    if portfolio_vol < 1e-12:
        return pd.Series(np.zeros(len(weights)))

    rc = _risk_contributions(weights, cov_matrix)
    rc_pct = rc / portfolio_vol
    return pd.Series(rc_pct)


def get_strategy_weights(
    strategy_name: str,
    log_returns: pd.DataFrame,
    tickers: List[str],
) -> np.ndarray:
    """
    Dispatcher function: compute weights for a named strategy.

    This is the single entry point for the backtesting engine.
    Given a strategy name and a return history, returns the appropriate weights.

    Parameters
    ----------
    strategy_name : str
        One of "Equal Weight", "Minimum Variance", "Risk Parity"
    log_returns : pd.DataFrame
        Historical log returns used for estimation
        (must NOT include any future data -- enforced by backtest engine)
    tickers : list of str
        Asset tickers in the same order as log_returns columns

    Returns
    -------
    np.ndarray
        Portfolio weights, shape (n_assets,)
    """
    from src.config import (
        STRATEGY_EQUAL_WEIGHT,
        STRATEGY_MIN_VARIANCE,
        STRATEGY_RISK_PARITY,
    )
    from src.portfolio import equal_weight

    n = len(tickers)

    if strategy_name == STRATEGY_EQUAL_WEIGHT:
        return equal_weight(n)

    elif strategy_name == STRATEGY_MIN_VARIANCE:
        cov = compute_covariance_matrix(log_returns)
        return minimum_variance_weights(cov)

    elif strategy_name == STRATEGY_RISK_PARITY:
        cov = compute_covariance_matrix(log_returns)
        return risk_parity_weights(cov)

    else:
        raise ValueError(
            f"Unknown strategy: '{strategy_name}'. "
            f"Choose from: Equal Weight, Minimum Variance, Risk Parity"
        )
