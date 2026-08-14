"""User-facing metrics view. All math lives in analytics.py."""

from __future__ import annotations

from flask import Blueprint, current_app, flash, g, redirect, render_template, url_for

from .analytics import compute_metrics, series_from_rows
from .auth import login_required
from .ledger import holdings
from .market import get_last_price, price_series

bp = Blueprint("metrics", __name__, url_prefix="/metrics")


def report_for_holdings(rows: list[dict]):
    quantities = {r["ticker"]: float(r["quantity"]) for r in rows}
    last_prices = {}
    series = {}
    for ticker in quantities:
        px = get_last_price(ticker)
        if px is None:
            continue
        last_prices[ticker] = px
        series[ticker] = series_from_rows(price_series(ticker))
    rf = float(current_app.config["RISK_FREE_RATE"])
    lookback = int(current_app.config.get("METRICS_LOOKBACK_DAYS", 365))
    return compute_metrics(quantities, series, last_prices, rf, lookback_days=lookback)


@bp.route("/")
@login_required
def display_matrices():
    rows = holdings(g.user["id"])
    if len(rows) < 2:
        flash("Hold at least two tickers to view correlation, Sharpe, and the frontier.", "error")
        return redirect(url_for("trade.trade"))
    try:
        report = report_for_holdings(rows)
    except ValueError as exc:
        flash(str(exc), "error")
        return redirect(url_for("home.dashboard"))
    return render_template("metrics/metrics.html", **report.to_template())
