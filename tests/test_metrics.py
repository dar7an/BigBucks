"""Hand-computed formula tests. Expected values are derived in comments."""

from __future__ import annotations

from datetime import date, timedelta

import math

import numpy as np
import pandas as pd
import pytest

from bigbucks.analytics import (
    aligned_pair,
    annualized_sharpe,
    compute_metrics,
    cumulative_from_t0,
    daily_returns,
    holding_period_return,
    mark_to_market_weights,
)
from bigbucks.solver import min_variance_weights


def test_daily_returns_simple():
    # 100 → 110 → 99
    got = daily_returns([100.0, 110.0, 99.0])
    assert got[0] == pytest.approx(0.10)
    assert got[1] == pytest.approx(99.0 / 110.0 - 1.0)


def test_cumulative_from_t0_not_latest():
    # Dividing by P_0, not P_last. Last/latest base would pin the end at 0
    # and history near -1 (the old stock.js bug).
    cum = cumulative_from_t0([100.0, 110.0, 90.0])
    assert cum[0] == pytest.approx(0.0)
    assert cum[1] == pytest.approx(0.10)
    assert cum[2] == pytest.approx(-0.10)
    assert cum[-1] != pytest.approx(0.0)


def test_holding_period_is_compounded_not_sum():
    # r = 0.10, 0.10 → sum = 0.20, compounded = 1.1*1.1 - 1 = 0.21
    r = daily_returns([100.0, 110.0, 121.0])
    assert holding_period_return(r) == pytest.approx(0.21)
    assert holding_period_return(r) != pytest.approx(float(np.sum(r)))


def test_sharpe_hand_computed():
    # Prices 100, 110, 99 → r = +0.10, −0.10
    # mean = 0
    # sample std ddof=1 = sqrt(((0.1)^2 + (-0.1)^2) / 1) = sqrt(0.02)
    # rf = 0.04 annual → rf_daily = 0.04/252
    # sharpe = (0 - 0.04/252) / sqrt(0.02) * sqrt(252)
    r = daily_returns([100.0, 110.0, 99.0])
    std = math.sqrt(0.02)
    expected = (0.0 - 0.04 / 252.0) / std * math.sqrt(252.0)
    assert annualized_sharpe(r, 0.04) == pytest.approx(expected)


def test_mark_to_market_weights():
    # 10 × $100 = $1,000; 5 × $200 = $1,000 → 50/50
    # First-fill totalPrice weighting (the old bug) is not used.
    w = mark_to_market_weights({"AAPL": 10, "MSFT": 5}, {"AAPL": 100.0, "MSFT": 200.0})
    assert w["AAPL"] == pytest.approx(0.5)
    assert w["MSFT"] == pytest.approx(0.5)


def test_weights_ignore_other_users_and_zero_qty():
    w = mark_to_market_weights({"AAPL": 2, "MSFT": 0}, {"AAPL": 50.0, "MSFT": 999.0})
    assert list(w.index) == ["AAPL"]
    assert w["AAPL"] == pytest.approx(1.0)


def test_aligned_pair_uses_first_overlap_as_t0():
    a_dates = ["2024-01-02", "2024-01-03", "2024-01-04"]
    b_dates = ["2024-01-03", "2024-01-04", "2024-01-05"]
    # overlap 01-03, 01-04: A 110, 121 and B 200, 220
    out = aligned_pair(a_dates, [100.0, 110.0, 121.0], b_dates, [200.0, 220.0, 240.0])
    assert out["dates"][0] == "2024-01-03"
    assert out["a_cum"][0] == pytest.approx(0.0)
    assert out["b_cum"][0] == pytest.approx(0.0)
    assert out["a_cum"][1] == pytest.approx(121.0 / 110.0 - 1.0)
    assert out["b_cum"][1] == pytest.approx(0.10)


def test_holdings_vol_is_not_solver_vol():
    # Two assets, 100% in A. Holdings σ = σ_A.
    # Solver min-var at the same μ is 50/50 and a different σ.
    end = date.today()
    idx = [(end - timedelta(days=79 - i)).isoformat() for i in range(80)]
    rng = np.random.default_rng(0)
    a = 100 * np.cumprod(1 + rng.normal(0.001, 0.02, size=80))
    b = 100 * np.cumprod(1 + rng.normal(0.001, 0.005, size=80))
    series = {"AAA": pd.Series(a, index=idx), "BBB": pd.Series(b, index=idx)}
    last = {"AAA": float(a[-1]), "BBB": float(b[-1])}
    report = compute_metrics(
        {"AAA": 10, "BBB": 10},
        series,
        last,
        rf_annual=0.04,
        lookback_days=365,
    )
    w = np.array(report.weights)
    cov = np.array(report.covariance_annual)
    holdings_sigma = math.sqrt(float(w @ cov @ w))
    assert report.portfolio_vol_annual == pytest.approx(holdings_sigma)
    opt_w, opt_sigma = min_variance_weights(cov, np.array(report.expected_returns), report.portfolio_return_annual)
    # Unless the book is already efficient, optimizer σ is smaller.
    assert opt_sigma <= holdings_sigma + 1e-9
    assert not np.allclose(opt_w, w) or opt_sigma == pytest.approx(holdings_sigma)


def test_correlation_symmetric_ones_on_diagonal():
    end = date.today()
    idx = [(end - timedelta(days=89 - i)).isoformat() for i in range(90)]
    rng = np.random.default_rng(1)
    shock = rng.normal(0, 0.01, 90)
    prices_a = pd.Series(100 * np.cumprod(1 + 0.001 + shock), index=idx)
    prices_b = pd.Series(100 * np.cumprod(1 + 0.001 - shock), index=idx)
    report = compute_metrics(
        {"AAA": 1, "BBB": 1},
        {"AAA": prices_a, "BBB": prices_b},
        {"AAA": float(prices_a.iloc[-1]), "BBB": float(prices_b.iloc[-1])},
        rf_annual=0.04,
    )
    corr = np.array(report.correlation)
    assert corr.shape == (2, 2)
    assert corr[0, 0] == pytest.approx(1.0)
    assert corr[1, 1] == pytest.approx(1.0)
    assert corr[0, 1] == pytest.approx(corr[1, 0])
    assert corr[0, 1] < -0.5
