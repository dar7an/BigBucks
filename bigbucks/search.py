"""Ticker search, quote pages, and authenticated chart JSON. No API key leaves the server."""

from __future__ import annotations

from flask import (
    Blueprint,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)

from .analytics import aligned_pair, cumulative_from_t0
from .auth import login_required
from .market import MarketDataError, known_tickers, price_series, quote_bundle

bp = Blueprint("search", __name__)


@bp.route("/search", methods=["GET", "POST"])
@login_required
def search():
    if request.method == "POST":
        ticker = request.form.get("stock_symbol", "").strip().upper()
        action = request.form.get("action", "search")
        if not ticker:
            flash("Enter a ticker such as AAPL.", "error")
            return render_template("search/search.html", tickers=known_tickers())
        if action == "compare":
            return redirect(url_for("search.compare", ticker=ticker))
        return redirect(url_for("search.quote", ticker=ticker))
    return render_template("search/search.html", tickers=known_tickers())


@bp.route("/search/<ticker>")
@login_required
def quote(ticker: str):
    ticker = ticker.upper()
    try:
        bundle = quote_bundle(ticker)
    except MarketDataError as exc:
        flash(str(exc), "error")
        return redirect(url_for("search.search"))
    return render_template("search/quote.html", quote=bundle, spy="SPY")


@bp.route("/search/<ticker>/compare")
@login_required
def compare(ticker: str):
    ticker = ticker.upper()
    try:
        bundle = quote_bundle(ticker)
        quote_bundle("SPY")
    except MarketDataError as exc:
        flash(str(exc), "error")
        return redirect(url_for("search.search"))
    return render_template("search/compare.html", quote=bundle, spy="SPY")


@bp.route("/api/series/<ticker>")
@login_required
def api_series(ticker: str):
    ticker = ticker.upper()
    rows = price_series(ticker)
    if not rows:
        return jsonify({"error": f"No history for {ticker}."}), 404
    dates = [r["closing_date"] for r in rows]
    prices = [float(r["adj_close_price"]) for r in rows]
    return jsonify(
        {
            "ticker": ticker,
            "dates": dates,
            "adj_close": prices,
            "cumulative": cumulative_from_t0(prices).tolist(),
        }
    )


@bp.route("/api/compare/<ticker>")
@login_required
def api_compare(ticker: str):
    ticker = ticker.upper()
    spy = "SPY"
    stock_rows = price_series(ticker)
    spy_rows = price_series(spy)
    if not stock_rows or not spy_rows:
        return jsonify({"error": "Need history for both the ticker and SPY."}), 404
    aligned = aligned_pair(
        [r["closing_date"] for r in stock_rows],
        [float(r["adj_close_price"]) for r in stock_rows],
        [r["closing_date"] for r in spy_rows],
        [float(r["adj_close_price"]) for r in spy_rows],
    )
    aligned["ticker"] = ticker
    aligned["benchmark"] = spy
    return jsonify(aligned)
