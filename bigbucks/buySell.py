import functools
from flask import Blueprint, flash, g, redirect, render_template, request, url_for
from .financialTransactions import hasSufficientBalance, addToBalance, get_last_price, add_transaction, \
    add_portfolio_object, hasSufficientStock, remove_portfolio_object
from .homepage import login_required
from .db import get_db

bp = Blueprint("buySell", __name__)


@bp.route("/buySell", methods=("GET", "POST"))
@login_required
def buySell():
    if request.method == "POST":
        # add error checking!
        ticker = request.form["ticker"].upper()
        quantity = int(request.form["numShares"])
        buySell = request.form['buyOrSell']

        unit_price = get_last_price(ticker)
        if unit_price is None:
            # show error on page!
            return redirect(url_for("buyStock.buy"))

        else:
            total_price = unit_price * quantity
            if buySell == 'buy':
                # check if sufficient balance
                sufficient_bal = hasSufficientBalance(g.user['userID'], total_price)

                # if no, return error!!!

                if sufficient_bal:
                    # deduct cash balance
                    addToBalance(g.user['userID'], 0 - total_price)
                    # add to portfolio objects (check if already there)
                    add_portfolio_object(g.user['userID'], ticker, quantity)
                    # record in transactions
                    add_transaction(g.user['userID'], ticker, quantity, unit_price, total_price, buySell)
            elif buySell == 'sell':
                # check if they have enough quantity of stock
                sufficient_stock = hasSufficientStock(g.user['userID'], ticker, quantity) 
                
                if sufficient_stock:
                    # remove portfolio objects
                    remove_portfolio_object(g.user['userID'], ticker, quantity)
                    # add cash balance
                    addToBalance(g.user['userID'], total_price)
                    # record in transactions
                    add_transaction(g.user['userID'], ticker, quantity, unit_price, total_price, buySell)

        return redirect(url_for("buySell.buySell"))

    return render_template("buySell.html", user=g.user)