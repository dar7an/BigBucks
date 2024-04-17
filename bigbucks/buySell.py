from flask import Blueprint, g, redirect, render_template, request, url_for
from .financialTransactions import get_last_price, hasSufficientBalance, addToBalance, add_transaction, \
    add_portfolio_object, hasSufficientStock, ticker_in_portfolio, remove_portfolio_object
from .homepage import login_required
from .stocksearch import insert_stock_data_db, stock_exists

bp = Blueprint("buySell", __name__)


@bp.route("/buySell", methods=("GET", "POST"))
@login_required
def buySell():
    if request.method == "GET":
        return render_template("buySell.html", user=g.user)

    ticker = request.form["ticker"].upper()
    quantity = int(request.form["numShares"])
    buy_sell = request.form['buyOrSell']
    unit_price = get_last_price(ticker)

    if unit_price is None:
        return render_template("buySell.html", user=g.user, error="Ticker does not exist")

    # Ensure the stock data is in the database
    if not stock_exists(ticker):
        insert_stock_data_db(ticker)

    total_price = unit_price * quantity

    if buy_sell == 'buy':
        return handle_buy(ticker, quantity, unit_price, total_price)
    elif buy_sell == 'sell':
        return handle_sell(ticker, quantity, unit_price, total_price)

    # Fallback for undefined buy or sell operations
    return render_template("buySell.html", user=g.user, error="Invalid operation requested")


def handle_buy(ticker, quantity, unit_price, total_price):
    if not hasSufficientBalance(g.user['userID'], total_price):
        return render_template("buySell.html", user=g.user, error="Insufficient balance")

    addToBalance(g.user['userID'], -total_price)
    add_portfolio_object(g.user['userID'], ticker, quantity)
    add_transaction(g.user['userID'], ticker, quantity, unit_price, total_price, 'buy')

    return redirect(url_for("buySell.buySell"))


def handle_sell(ticker, quantity, unit_price, total_price):
    if not hasSufficientStock(g.user['userID'], ticker, quantity) or not ticker_in_portfolio(g.user['userID'], ticker):
        return render_template("buySell.html", user=g.user, error="Insufficient stock or you do not own this stock")

    remove_portfolio_object(g.user['userID'], ticker, quantity)
    addToBalance(g.user['userID'], total_price)
    add_transaction(g.user['userID'], ticker, quantity, unit_price, total_price, 'sell')

    return redirect(url_for("buySell.buySell"))
