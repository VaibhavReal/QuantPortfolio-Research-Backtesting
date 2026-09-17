"""
portfolio.py
============
Core portfolio construction and mathematical building blocks.

This module provides the fundamental portfolio math that every strategy
in this project relies on. The three strategies differ only in HOW they
choose weights; the math used to evaluate those weights is shared here.

PORTFOLIO MATHEMATICS (RECAP)
-------------------------------
For a portfolio of N assets with weights w = [w_1, ..., w_N]:

  Expected return:  E[R_p] = w^T * mu          (dot product)
  Variance:         Var(R_p) = w^T * Sigma * w  (quadratic form)
  Volatility:       Std(R_p) = sqrt(Var(R_p))

where mu is the vector of expected returns and Sigma is the N?N
covariance matrix.

LONG-ONLY CONSTRAINT
---------------------
All strategies in this project enforce:
  - w_i >= 0  for all i  (no short selling)
  - sum(w_i) = 1          (fully invested)

This is called a "long-only, fully invested" portfolio. It's the standard
starting point for portfolio construction and aligns with realistic constraints
for many investment mandates (mutual funds, pension funds, etc.).
"""

import numpy as np
import pandas as pd
from typing import Union, List


def equal_weight(n_assets: int) -> np.ndarray:
    """
    Compute equal-weight portfolio weights.

    Formula: w_i = 1/N  for all i in {1, ..., N}

    Equal weighting is the simplest possible portfolio rule. It requires:
      - No estimation of expected returns (avoids estimation error)
      - No optimization (no convergence issues)
      - Only one input: the number of assets

    Studies (e.g., DeMiguel et al. 2009) have shown that equal-weight
    portfolios are surprisingly hard to beat out-of-sample, partly because
    they avoid overfitting to estimated parameters.

    Parameters
    ----------
    n_assets : int
        Number of assets in the portfolio

    Returns
    -------
    np.ndarray
        Array of shape (n_assets,) with each element = 1/n_assets
    """
    if n_assets <= 0:
        raise ValueError("n_assets must be a positive integer")
    return np.ones(n_assets) / n_assets


def normalize_weights(weights: np.ndarray) -> np.ndarray:
    """
    Normalize a weight vector so it sums to exactly 1.

    After numerical optimization, weights may not sum to exactly 1
    due to floating-point precision. This function rescales them.
    Also clips any slightly negative weights to 0 before normalizing
    (numerical optimizers sometimes produce tiny negative values like -1e-15).

    Parameters
    ----------
    weights : np.ndarray
        Raw portfolio weights

    Returns
    -------
    np.ndarray
        Normalized weights summing to 1, all non-negative
    """
    weights = np.array(weights, dtype=float)

    # Clip tiny negative values (numerical artifacts from optimizer)
    weights = np.clip(weights, 0, None)

    total = weights.sum()
    if total <= 0:
        raise ValueError("Weight sum is zero or negative -- cannot normalize")

    return weights / total


def compute_portfolio_return(
    weights: np.ndarray,
    asset_returns: Union[np.ndarray, pd.Series],
) -> float:
    """
    Compute the portfolio return for a given set of weights and asset returns.

    Formula: R_p = sum_i w_i * r_i = w^T * r

    Parameters
    ----------
    weights : np.ndarray
        Portfolio weights, shape (n_assets,)
    asset_returns : np.ndarray or pd.Series
        Asset returns for the same period, shape (n_assets,)

    Returns
    -------
    float
        Portfolio return (decimal, e.g., 0.05 = 5%)
    """
    w = np.array(weights)
    r = np.array(asset_returns)
    return float(np.dot(w, r))


def compute_portfolio_variance(
    weights: np.ndarray,
    cov_matrix: np.ndarray,
) -> float:
    """
    Compute portfolio variance using the quadratic form.

    Formula: Var(R_p) = w^T * Sigma * w

    where Sigma is the N?N covariance matrix.

    This is the central formula in mean-variance optimization.
    Minimizing this (subject to constraints) gives the minimum-variance portfolio.

    Parameters
    ----------
    weights : np.ndarray
        Portfolio weights, shape (n_assets,)
    cov_matrix : np.ndarray
        Annualized covariance matrix, shape (n_assets, n_assets)

    Returns
    -------
    float
        Portfolio variance (annualized, in return? units)
    """
    w = np.array(weights)
    return float(w @ cov_matrix @ w)


def compute_portfolio_volatility(
    weights: np.ndarray,
    cov_matrix: np.ndarray,
) -> float:
    """
    Compute annualized portfolio volatility (standard deviation).

    Formula: Std(R_p) = sqrt(w^T * Sigma * w)

    Volatility is the square root of variance and is expressed in
    the same units as returns (e.g., 0.15 = 15% annualized).
    It is the most commonly quoted risk measure for a portfolio.

    Parameters
    ----------
    weights : np.ndarray
        Portfolio weights
    cov_matrix : np.ndarray
        Annualized covariance matrix

    Returns
    -------
    float
        Portfolio volatility (annualized, as a decimal)
    """
    variance = compute_portfolio_variance(weights, cov_matrix)
    return float(np.sqrt(variance))


def compute_expected_portfolio_return(
    weights: np.ndarray,
    expected_returns: Union[np.ndarray, pd.Series],
) -> float:
    """
    Compute the expected (mean) portfolio return.

    Formula: E[R_p] = w^T * mu

    where mu is the vector of expected (mean) asset returns.
    In this project, expected returns are estimated as the historical
    mean of daily log returns, then annualized.

    Parameters
    ----------
    weights : np.ndarray
        Portfolio weights, shape (n_assets,)
    expected_returns : np.ndarray or pd.Series
        Annualized expected returns per asset, shape (n_assets,)

    Returns
    -------
    float
        Expected portfolio return (annualized, as a decimal)
    """
    w = np.array(weights)
    mu = np.array(expected_returns)
    return float(np.dot(w, mu))


def validate_weights(weights: np.ndarray, tol: float = 1e-6) -> bool:
    """
    Check that portfolio weights satisfy basic constraints.

    Checks:
      1. All weights are non-negative (long-only)
      2. Weights sum to approximately 1 (fully invested)

    Parameters
    ----------
    weights : np.ndarray
        Portfolio weights to validate
    tol : float
        Numerical tolerance for the sum-to-one check

    Returns
    -------
    bool
        True if all constraints are satisfied, False otherwise
    """
    w = np.array(weights)

    # Long-only check
    if np.any(w < -tol):
        return False

    # Sum-to-one check
    if abs(w.sum() - 1.0) > tol:
        return False

    return True


def weights_to_dataframe(
    weights: np.ndarray,
    tickers: List[str],
    strategy_name: str,
    date: pd.Timestamp = None,
) -> pd.DataFrame:
    """
    Convert a weights array to a tidy DataFrame.

    Useful for storing weights in SQL and exporting to CSV.

    Parameters
    ----------
    weights : np.ndarray
        Portfolio weights
    tickers : list of str
        Asset ticker symbols (in the same order as weights)
    strategy_name : str
        Name of the portfolio strategy
    date : pd.Timestamp, optional
        The date at which these weights were computed

    Returns
    -------
    pd.DataFrame
        Tidy DataFrame with columns: Date, Strategy, Ticker, Weight
    """
    rows = []
    for ticker, weight in zip(tickers, weights):
        rows.append({
            "Date": date,
            "Strategy": strategy_name,
            "Ticker": ticker,
            "Weight": round(float(weight), 6),
        })
    return pd.DataFrame(rows)
