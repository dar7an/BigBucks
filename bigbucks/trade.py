"""Place paper trades at last close. One database transaction per fill."""

from __future__ import annotations

from flask import Blueprint, current_app, flash, g, redirect, render_template, request, url_for

from .auth import login_required
from .ledger import (
    InvalidQuantity,
    InsufficientCash,
    InsufficientShares,
    LedgerError,
    UnknownTicker,
    account_snapshot,
    execute_trade,
)
from .market import MarketDataError, ensure_history, known_tickers

bp = Blueprint("trade", __name__)


@bp.route("/trade", methods=["GET", "POST"])
@login_required
def trade():
    snap = account_snapshot(g.user["id"], float(current_app.config["STARTING_CASH"]))
    tickers = known_tickers()
    form = {
        "ticker": request.args.get("ticker", "").upper(),
        "numShares": "",
        "buyOrSell": "buy",
    }
    if request.method == "POST":
        form["ticker"] = request.form.get("ticker", "").strip().upper()
        form["buyOrSell"] = request.form.get("buyOrSell", "buy").strip().lower()
        raw_qty = request.form.get("numShares", "").strip()
        try:
            quantity = int(raw_qty)
        except ValueError:
            flash("Enter a whole number of shares, at least 1.", "error")
            return render_template("trade.html", snap=snap, tickers=tickers, form=form)
        try:
            ensure_history(form["ticker"])
            result = execute_trade(g.user["id"], form["ticker"], quantity, form["buyOrSell"])
        except InvalidQuantity as exc:
            flash(str(exc), "error")
            return render_template("trade.html", snap=snap, tickers=tickers, form=form)
        except UnknownTicker:
            flash(
                f"No last price for {form['ticker'] or 'that ticker'}. Search a seeded symbol first.",
                "error",
            )
            return render_template("trade.html", snap=snap, tickers=tickers, form=form)
        except (InsufficientCash, InsufficientShares, LedgerError, MarketDataError) as exc:
            flash(str(exc), "error")
            snap = account_snapshot(g.user["id"], float(current_app.config["STARTING_CASH"]))
            return render_template("trade.html", snap=snap, tickers=tickers, form=form)
        verb = "Bought" if result["side"] == "buy" else "Sold"
        flash(
            f"{verb} {result['quantity']:,} {result['ticker']} at ${result['unit_price']:,.2f} "
            f"(${result['total_price']:,.2f}).",
            "success",
        )
        return redirect(url_for("home.dashboard"))
    return render_template("trade.html", snap=snap, tickers=tickers, form=form)
