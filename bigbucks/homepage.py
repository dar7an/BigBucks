import functools
from flask import Blueprint, flash, g, redirect, render_template, request, url_for
from .financialTransactions import hasSufficientBalance, addToBalance
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
    if request.method == "POST":
        deposit = request.form["deposit"]
        addToBalance(g.user['userID'], deposit)

    return render_template("base.html", user=g.user)
