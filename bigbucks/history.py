"""User transaction history."""

from __future__ import annotations

from flask import Blueprint, g, render_template

from .auth import login_required
from .ledger import transactions_for

bp = Blueprint("history", __name__, url_prefix="/history")


@bp.route("/")
@login_required
def history():
    return render_template("history.html", trades=transactions_for(g.user["id"]))
