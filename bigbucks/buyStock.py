import functools
from flask import Blueprint, flash, g, redirect, render_template, request, url_for
from .financialTransactions import hasSufficientBalance, addToBalance, get_last_price, add_transaction, add_portfolio_object
from .homepage import login_required
from .db import get_db

bp = Blueprint("buyStock", __name__)

@bp.route("/buy", methods=("GET", "POST"))
@login_required
def buy():
    if request.method == "POST":
        # add error checking!
        ticker = request.form["ticker"].upper()
        quantity = int(request.form["numShares"])
        # get current stock price
        unit_price = get_last_price(ticker)
        # calculate purchase price
        total_price = unit_price * quantity
        # check if sufficient balance
        sufficient_bal = hasSufficientBalance(g.user['userID'], total_price)

        # if no, return error!!!

        # if yes:
        if sufficient_bal:
            # deduct cash balance
            addToBalance(g.user['userID'], 0 - total_price)
            # add to portfolio objects (check if already there)
            add_portfolio_object(g.user['userID'], ticker, quantity)
            # record in transactions
            add_transaction(g.user['userID'], ticker, quantity, unit_price, total_price, "buy")
            

        return render_template("buyStock.html", user=g.user)

    return render_template("buyStock.html", user=g.user)