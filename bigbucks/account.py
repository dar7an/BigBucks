"""Account settings. Password changes require the current password."""

from __future__ import annotations

import re

from flask import Blueprint, flash, g, redirect, render_template, request, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from .auth import login_required
from .db import get_db

bp = Blueprint("account", __name__, url_prefix="/account")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@bp.route("/", methods=["GET", "POST"])
@login_required
def account():
    if request.method == "POST":
        intent = request.form.get("intent", "")
        db = get_db()
        if intent == "email":
            email = request.form.get("email", "").strip().lower()
            if not EMAIL_RE.match(email):
                flash("Enter an email address like name@example.com.", "error")
                return render_template("account.html")
            try:
                db.execute("UPDATE users SET email = ? WHERE id = ?", (email, g.user["id"]))
                db.commit()
            except db.IntegrityError:
                flash("That email is already in use.", "error")
                return render_template("account.html")
            flash("Email updated.", "success")
            g.user = db.execute("SELECT * FROM users WHERE id = ?", (g.user["id"],)).fetchone()
            return redirect(url_for("account.account"))
        if intent == "password":
            current = request.form.get("current_password", "")
            new = request.form.get("password", "")
            confirm = request.form.get("password_confirm", "")
            if not check_password_hash(g.user["password_hash"], current):
                flash("Current password is incorrect.", "error")
                return render_template("account.html")
            if len(new) < 8:
                flash("Choose a new password with at least 8 characters.", "error")
                return render_template("account.html")
            if new != confirm:
                flash("New password and confirmation do not match.", "error")
                return render_template("account.html")
            db.execute(
                "UPDATE users SET password_hash = ? WHERE id = ?",
                (generate_password_hash(new), g.user["id"]),
            )
            db.commit()
            flash("Password updated.", "success")
            return redirect(url_for("account.account"))
        flash("Nothing to update.", "error")
    return render_template("account.html")
