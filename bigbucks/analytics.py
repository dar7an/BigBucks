"""Single portfolio-analytics engine used by user and admin views.

Formulas (equity book only; cash is excluded from weights):

Daily simple return
    r_{i,t} = P_{i,t} / P_{i,t-1} − 1
    P is adjusted close, sorted by date ascending, inner-joined across tickers.

Mark-to-market weight
    w_i = q_i P_i / Σ_j q_j P_j
    P_i is the last available adj close for i. Solver weights are never
    substituted for these.

Portfolio daily return (constant current weights)
    r_{p,t} = Σ_i w_i r_{i,t}

Holding-period return
    R_p = Π_t (1 + r_{p,t}) − 1

Expected return (annualized)
    μ_p = mean(r_{p,t}) × 252

Holdings volatility (annualized)
    Σ = Cov(r_d) × 252          # pandas sample covariance, ddof=1
    σ_p = √(w′ Σ w)
    This is the plotted “Your book” point. It is not the min-variance
    mix at μ_p (that mix is on the frontier).

Sharpe ratio (annualized, CFA daily convention)
    sharpe = (mean(r_d) − r_f/252) / std(r_d, ddof=1) × √252
    Equivalent: (μ_p − r_f) / σ_p
    r_f is an annual decimal (default: 10-year Treasury proxy).

Cumulative return series (charts)
    C_t = P_t / P_0 − 1
    Dates sorted ascending; P_0 is the first overlapping observation.

Efficient frontier
    Unconstrained two-fund min-variance (Merton 1972). Shorts allowed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Iterable, Mapping, Sequence

import numpy as np
import pandas as pd

from .solver import frontier_curve

TRADING_DAYS = 252


def _as_float_series(values: Mapping[str, float] | pd.Series) -> pd.Series:
    if isinstance(values, pd.Series):
        return values.astype(float)
    return pd.Series(values, dtype=float)


def daily_returns(prices: Sequence[float] | np.ndarray | pd.Series) -> np.ndarray:
    """Simple returns on a chronological price series."""
    p = np.asarray(prices, dtype=float)
    p = p[np.isfinite(p)]
    if p.size < 2:
        return np.array([], dtype=float)
    return p[1:] / p[:-1] - 1.0


def cumulative_from_t0(prices: Sequence[float] | np.ndarray) -> np.ndarray:
    """C_t = P_t / P_0 − 1. First observation is 0."""
    p = np.asarray(prices, dtype=float)
    if p.size == 0 or p[0] == 0:
        return np.array([], dtype=float)
    return p / p[0] - 1.0


def mark_to_market_weights(
    quantities: Mapping[str, float], last_prices: Mapping[str, float]
) -> pd.Series:
    """w_i = q_i P_i / Σ q_j P_j. Drops names with missing or non-positive value."""
    q = _as_float_series(quantities)
    p = _as_float_series(last_prices)
    aligned = pd.concat([q.rename("q"), p.rename("p")], axis=1).dropna()
    value = aligned["q"] * aligned["p"]
    value = value[value > 0]
    total = float(value.sum())
    if total <= 0:
        return pd.Series(dtype=float)
    return value / total


def annualized_sharpe(
    daily: Sequence[float] | np.ndarray, rf_annual: float, periods: int = TRADING_DAYS
) -> float | None:
    r = np.asarray(daily, dtype=float)
    r = r[np.isfinite(r)]
    if r.size < 2:
        return None
    std = float(r.std(ddof=1))
    if std == 0:
        return None
    return (float(r.mean()) - rf_annual / periods) / std * np.sqrt(periods)


def holding_period_return(daily: Sequence[float] | np.ndarray) -> float | None:
    r = np.asarray(daily, dtype=float)
    r = r[np.isfinite(r)]
    if r.size == 0:
        return None
    return float(np.prod(1.0 + r) - 1.0)


def annualized_mean(daily: Sequence[float] | np.ndarray, periods: int = TRADING_DAYS) -> float | None:
    r = np.asarray(daily, dtype=float)
    r = r[np.isfinite(r)]
    if r.size == 0:
        return None
    return float(r.mean() * periods)


def annualized_vol(daily: Sequence[float] | np.ndarray, periods: int = TRADING_DAYS) -> float | None:
    r = np.asarray(daily, dtype=float)
    r = r[np.isfinite(r)]
    if r.size < 2:
        return None
    return float(r.std(ddof=1) * np.sqrt(periods))


def _iso_day(value) -> str:
    """Normalize a date-like index value to YYYY-MM-DD without pandas.to_datetime."""
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    text = str(value)[:10]
    return date.fromisoformat(text).isoformat()


def price_frame(
    series_by_ticker: Mapping[str, pd.Series],
    lookback_days: int = 365,
    end: date | None = None,
) -> pd.DataFrame:
    """Inner-join adj-close series, chronological, last `lookback_days` calendar days."""
    frames = []
    for ticker, series in series_by_ticker.items():
        s = series.copy()
        s.index = [_iso_day(i) for i in s.index]
        s = s[~s.index.duplicated(keep="last")].sort_index()
        s = pd.to_numeric(s, errors="coerce")
        s.name = ticker
        frames.append(s)
    if not frames:
        return pd.DataFrame()
    df = pd.concat(frames, axis=1, join="inner").dropna(how="any")
    if df.empty:
        return df
    cutoff = ((end or date.today()) - timedelta(days=lookback_days)).isoformat()
    df = df[df.index >= cutoff]
    return df.sort_index()


def returns_frame(prices: pd.DataFrame) -> pd.DataFrame:
    return prices.pct_change(fill_method=None).dropna(how="any")


@dataclass
class MetricsReport:
    tickers: list[str]
    weights: list[float]
    last_prices: list[float]
    quantities: list[float]
    market_values: list[float]
    correlation: list[list[float]]
    covariance_daily: list[list[float]]
    covariance_annual: list[list[float]]
    expected_returns: list[float]
    portfolio_return_annual: float | None
    portfolio_vol_annual: float | None
    holding_period_return: float | None
    sharpe: float | None
    rf_annual: float
    n_obs: int
    lookback_days: int
    frontier: list[tuple[float, float]] = field(default_factory=list)
    has_shorts_on_frontier: bool = True
    notes: str = ""

    def to_template(self) -> dict:
        return {
            "tickers": self.tickers,
            "weight_vector": self.weights,
            "last_prices": self.last_prices,
            "quantities": self.quantities,
            "market_values": self.market_values,
            "correlation_matrix": self.correlation,
            "covariance_matrix": self.covariance_annual,
            "expected_returns": self.expected_returns,
            "portfolio_return": self.portfolio_return_annual,
            "portfolio_volatility": self.portfolio_vol_annual,
            "holding_period_return": self.holding_period_return,
            "sharpe_ratio": self.sharpe,
            "rf_annual": self.rf_annual,
            "n_obs": self.n_obs,
            "lookback_days": self.lookback_days,
            "returns_volatilities": self.frontier,
            "has_shorts_on_frontier": self.has_shorts_on_frontier,
            "notes": self.notes,
        }


def compute_metrics(
    quantities: Mapping[str, float],
    series_by_ticker: Mapping[str, pd.Series],
    last_prices: Mapping[str, float],
    rf_annual: float,
    lookback_days: int = 365,
) -> MetricsReport:
    """Build the full report for a set of holdings. Requires ≥2 names with prices."""
    weights = mark_to_market_weights(quantities, last_prices)
    tickers = [t for t in weights.index if t in series_by_ticker]
    if len(tickers) < 2:
        raise ValueError("Need at least two holdings with prices to compute metrics.")
    weights = weights.loc[tickers]
    weights = weights / weights.sum()
    prices = price_frame({t: series_by_ticker[t] for t in tickers}, lookback_days=lookback_days)
    if prices.shape[0] < 60:
        raise ValueError(
            "Need at least 60 overlapping sessions of history. Add holdings or seed prices."
        )
    rets = returns_frame(prices)
    w = weights.reindex(rets.columns).to_numpy(dtype=float)
    rp = rets.to_numpy(dtype=float) @ w
    corr = rets.corr()
    cov_d = rets.cov()  # ddof=1
    cov_a = cov_d * TRADING_DAYS
    mu_d = rets.mean()
    mu_a = mu_d * TRADING_DAYS
    sigma_p = float(np.sqrt(w @ cov_a.to_numpy(dtype=float) @ w))
    mu_p = float(w @ mu_a.to_numpy(dtype=float))
    frontier = frontier_curve(cov_a.to_numpy(dtype=float), mu_a.to_numpy(dtype=float))
    qty = [float(quantities[t]) for t in tickers]
    last = [float(last_prices[t]) for t in tickers]
    values = [q * p for q, p in zip(qty, last)]
    return MetricsReport(
        tickers=tickers,
        weights=[float(weights[t]) for t in tickers],
        last_prices=last,
        quantities=qty,
        market_values=values,
        correlation=corr.loc[tickers, tickers].values.tolist(),
        covariance_daily=cov_d.loc[tickers, tickers].values.tolist(),
        covariance_annual=cov_a.loc[tickers, tickers].values.tolist(),
        expected_returns=[float(mu_a[t]) for t in tickers],
        portfolio_return_annual=mu_p,
        portfolio_vol_annual=sigma_p,
        holding_period_return=holding_period_return(rp),
        sharpe=annualized_sharpe(rp, rf_annual),
        rf_annual=rf_annual,
        n_obs=int(rets.shape[0]),
        lookback_days=lookback_days,
        frontier=frontier,
        notes=(
            "Sharpe is annualized from daily simple returns "
            f"(mean − r_f/{TRADING_DAYS}) / σ × √{TRADING_DAYS}. "
            "Frontier is unconstrained mean-variance; short sales are allowed. "
            "Your book uses mark-to-market holdings weights, not the optimizer."
        ),
    )


def series_from_rows(rows: Iterable[Mapping]) -> pd.Series:
    """Build a chronological adj-close series from historic_prices rows."""
    dates = []
    prices = []
    for row in rows:
        dates.append(_iso_day(row["closing_date"]))
        prices.append(float(row["adj_close_price"]))
    s = pd.Series(prices, index=dates, dtype=float)
    return s[~s.index.duplicated(keep="last")].sort_index()


def aligned_pair(
    a_dates: Sequence[str],
    a_prices: Sequence[float],
    b_dates: Sequence[str],
    b_prices: Sequence[float],
) -> dict:
    """Inner-join two series and return t0 cumulative plus daily returns."""
    a_map = {_iso_day(d): float(p) for d, p in zip(a_dates, a_prices)}
    b_map = {_iso_day(d): float(p) for d, p in zip(b_dates, b_prices)}
    dates = sorted(set(a_map) & set(b_map))
    if not dates:
        return {"dates": [], "a_cum": [], "b_cum": [], "a_daily": [], "b_daily": [], "daily_dates": []}
    a_p = np.array([a_map[d] for d in dates], dtype=float)
    b_p = np.array([b_map[d] for d in dates], dtype=float)
    a_d = daily_returns(a_p)
    b_d = daily_returns(b_p)
    return {
        "dates": dates,
        "a_cum": cumulative_from_t0(a_p).tolist(),
        "b_cum": cumulative_from_t0(b_p).tolist(),
        "a_daily": a_d.tolist(),
        "b_daily": b_d.tolist(),
        "daily_dates": dates[1:],
    }
