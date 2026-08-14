"""Admin-only tape, aggregate book, and per-user metrics."""

from __future__ import annotations

from datetime import date

from flask import Blueprint, current_app, flash, redirect, render_template, url_for
from werkzeug.exceptions import abort

from .analytics import compute_metrics, series_from_rows
from .auth import admin_required
from .db import get_db
from .ledger import holdings, list_users, system_holdings, tape_for_day, unique_held_tickers
from .market import get_last_price, price_series

bp = Blueprint("admin", __name__, url_prefix="/admin")


@bp.route("/")
@bp.route("/summary")
@admin_required
def summary():
    today = date.today().isoformat()
    return render_template(
        "admin/summary.html",
        summary_data=tape_for_day(today),
        current_date=today,
        users=list_users(),
    )


@bp.route("/holdings")
@admin_required
def history():
    return render_template("admin/holdings.html", history_data=system_holdings())


@bp.route("/analysis")
@admin_required
def risk_return():
    tickers = unique_held_tickers()
    if len(tickers) < 2:
        flash("The system needs at least two distinct held tickers to plot a frontier.", "error")
        return redirect(url_for("admin.summary"))
    rows = [{"ticker": t, "quantity": 1} for t in tickers]
    try:
        report = _report(rows)
    except ValueError as exc:
        flash(str(exc), "error")
        return redirect(url_for("admin.summary"))
    ctx = report.to_template()
    ctx["equal_weight_note"] = (
        "This system view equal-weights unique held tickers. "
        "It is not a market portfolio."
    )
    ctx["active"] = "admin"
    return render_template("admin/analysis.html", **ctx)


@bp.route("/users/<int:user_id>/metrics")
@admin_required
def display_user_matrices(user_id: int):
    user = get_db().execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if user is None:
        abort(404)
    rows = holdings(user_id)
    if len(rows) < 2:
        flash(f"{user['username']} needs at least two holdings for metrics.", "error")
        return redirect(url_for("admin.summary"))
    try:
        report = _report(rows)
    except ValueError as exc:
        flash(str(exc), "error")
        return redirect(url_for("admin.summary"))
    ctx = report.to_template()
    ctx["active"] = "admin"
    ctx["subject"] = user
    return render_template("admin/user_metrics.html", **ctx)


def _report(rows: list[dict]):
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
