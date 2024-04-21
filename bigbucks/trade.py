from flask import Blueprint, flash, g, redirect, render_template, request, url_for
from .transactions import (
    get_last_price, has_sufficient_balance, add_to_balance,
    add_transaction, add_portfolio_object, has_sufficient_stock,
    ticker_in_portfolio, remove_portfolio_object
)
from .home import login_required
from .search import insert_stock_data_db, stock_exists

bp = Blueprint("trade", __name__)


@bp.route("/trade", methods=["GET", "POST"])
@login_required
def trade():
    if request.method == "GET":
        return render_template("trade.html", user=g.user)

    ticker = request.form["ticker"].upper()
    try:
        quantity = int(request.form["numShares"])
    except ValueError:
        flash("Invalid number of shares", 'error')
        return render_template("trade.html", user=g.user)

    buy_sell = request.form['buyOrSell'].lower()
    if buy_sell not in ['buy', 'sell']:
        flash("Invalid operation. Please choose 'buy' or 'sell'.", 'error')
        return render_template("trade.html", user=g.user)

    unit_price = get_last_price(ticker)
    if unit_price is None:
        flash("Ticker does not exist", 'error')
        return render_template("trade.html", user=g.user)

    if not stock_exists(ticker):
        insert_stock_data_db(ticker)

    total_price = unit_price * quantity

    if buy_sell == 'buy':
        return handle_buy(ticker, quantity, unit_price, total_price)
    elif buy_sell == 'sell':
        return handle_sell(ticker, quantity, unit_price, total_price)


def handle_buy(ticker, quantity, unit_price, total_price):
    if not has_sufficient_balance(g.user['userID'], total_price):
        flash("Insufficient balance", 'error')
        return redirect(url_for("trade"))

    add_to_balance(g.user['userID'], -total_price)
    add_portfolio_object(g.user['userID'], ticker, quantity)
    add_transaction(g.user['userID'], ticker, quantity, unit_price, total_price, 'buy')
    flash("Purchase successful!", 'info')
    return redirect(url_for("trade"))


def handle_sell(ticker, quantity, unit_price, total_price):
    if not (has_sufficient_stock(g.user['userID'], ticker, quantity) and ticker_in_portfolio(g.user['userID'], ticker)):
        flash("Insufficient stock or you do not own this stock", 'error')
        return redirect(url_for("trade"))

    remove_portfolio_object(g.user['userID'], ticker, quantity)
    add_to_balance(g.user['userID'], total_price)
    add_transaction(g.user['userID'], ticker, quantity, unit_price, total_price, 'sell')
    flash("Sale successful!", 'info')
    return redirect(url_for("trade"))
