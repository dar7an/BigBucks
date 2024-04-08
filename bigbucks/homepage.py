import functools
from flask import Blueprint, flash, g, redirect, render_template, request, url_for
from .financialTransactions import hasSufficientBalance, addToBalance, get_current_portfolio, get_last_price, get_company_name
from .db import get_db

bp = Blueprint("homepage", __name__, url_prefix="/")


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for("auth.login"))

        return view(**kwargs)

    return wrapped_view


@bp.route("/", methods=("GET", "POST"))
@login_required
def homepage():
    portfolio = get_current_portfolio(g.user['userID'])
    portfolio = format_portfolio(portfolio)

    if request.method == "POST":
        deposit = request.form["deposit"]
        addToBalance(g.user['userID'], deposit)
        return redirect(url_for('homepage.homepage'))

    return render_template("base.html", user=g.user, portfolio=portfolio)


def format_portfolio(input):
    portfolio = []
    for item in input:
        toAdd = {}
        toAdd['ticker'] = item['ticker']
        toAdd['quantity'] = item['quantity']
        toAdd['price'] = get_last_price(item['ticker'])
        toAdd['name'] = get_company_name(item['ticker'])
        portfolio.append(toAdd)
    return portfolio
