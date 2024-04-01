import functools
from flask import Blueprint, flash, g, redirect, render_template, request, url_for
from .financialTransactions import hasSufficientBalance, addToBalance
from .homepage import login_required
from .db import get_db

bp = Blueprint("buyStock", __name__)

@bp.route("/buy", methods=("GET", "POST"))
@login_required
def buy():
    if request.method == "POST":
        # deposit = request.form["deposit"]
        # addToBalance(g.user['userID'], deposit)
        return redirect(url_for('homepage.homepage'))

    return render_template("buyStock.html", user=g.user)