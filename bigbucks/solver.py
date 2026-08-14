"""Unconstrained two-fund mean-variance (Merton 1972).

Solves min w'Σw subject to 1'w = 1 and μ'w = r* via the KKT linear system.
Short sales are allowed; callers must label that on the chart.
"""

from __future__ import annotations

import numpy as np


class FrontierError(Exception):
    pass


def min_variance_weights(
    cov: np.ndarray, mu: np.ndarray, target_return: float
) -> tuple[np.ndarray, float]:
    """Return (weights, sigma) at the unconstrained min-variance mix for r*.

    KKT system:

        [ Σ   1  μ ] [ w ]   [ 0 ]
        [ 1'  0  0 ] [ λ ] = [ 1 ]
        [ μ'  0  0 ] [ γ ]   [ r*]
    """
    cov = np.asarray(cov, dtype=float)
    mu = np.asarray(mu, dtype=float).reshape(-1)
    n = mu.shape[0]
    if cov.shape != (n, n):
        raise FrontierError("Covariance shape does not match expected returns.")
    kkt = np.zeros((n + 2, n + 2), dtype=float)
    kkt[:n, :n] = cov
    kkt[:n, n] = 1.0
    kkt[:n, n + 1] = mu
    kkt[n, :n] = 1.0
    kkt[n + 1, :n] = mu
    rhs = np.zeros(n + 2, dtype=float)
    rhs[n] = 1.0
    rhs[n + 1] = float(target_return)
    try:
        sol = np.linalg.solve(kkt, rhs)
    except np.linalg.LinAlgError as exc:
        raise FrontierError("Mean-variance system is singular at this target.") from exc
    weights = sol[:n]
    variance = float(weights @ cov @ weights)
    if variance < 0 and variance > -1e-12:
        variance = 0.0
    if variance < 0:
        raise FrontierError("Numerical variance was negative.")
    return weights, float(np.sqrt(variance))


def frontier_curve(
    cov: np.ndarray, mu: np.ndarray, points: int = 25
) -> list[tuple[float, float]]:
    """Grid target returns between min(μ) and max(μ). Drops singular points."""
    mu = np.asarray(mu, dtype=float).reshape(-1)
    lo, hi = float(np.min(mu)), float(np.max(mu))
    if not np.isfinite(lo) or hi - lo < 1e-12:
        return []
    targets = np.linspace(lo, hi, points)
    curve = []
    for target in targets:
        try:
            _, sigma = min_variance_weights(cov, mu, float(target))
        except FrontierError:
            continue
        if np.isfinite(sigma):
            curve.append((float(sigma), float(target)))
    return curve
