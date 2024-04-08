import functools
from flask import Blueprint, flash, g, redirect, render_template, request, url_for
from .db import get_db
from .homepage import login_required

bp = Blueprint("metrics", __name__, url_prefix="/metrics")

@bp.route("/metrics", methods=("GET", "POST"))
@login_required
def display_metrics():
    return render_template("metrics/metrics.html", user=g.user)