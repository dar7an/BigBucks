"""Home: public landing and the logged-in dashboard."""

from __future__ import annotations

from flask import Blueprint, current_app, g, redirect, render_template, url_for

from .auth import login_required
from .ledger import account_snapshot

bp = Blueprint("home", __name__)


@bp.route("/")
def index():
    if g.user:
        return redirect(url_for("home.dashboard"))
    return render_template("landing.html")


@bp.route("/home")
@login_required
def dashboard():
    snap = account_snapshot(g.user["id"], float(current_app.config["STARTING_CASH"]))
    return render_template("home.html", snap=snap)
