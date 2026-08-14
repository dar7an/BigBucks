"""Authentication, session, and access control.

Decorators always sit *below* ``@bp.route`` so Flask registers the wrapped view.
"""

from __future__ import annotations

import functools
import re
from typing import Callable

from flask import (
    Blueprint,
    current_app,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.exceptions import abort
from werkzeug.security import check_password_hash, generate_password_hash

from .db import get_db

bp = Blueprint("auth", __name__, url_prefix="/auth")

USERNAME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]{2,31}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def load_logged_in_user() -> None:
    user_id = session.get("user_id")
    if user_id is None:
        g.user = None
        return
    g.user = get_db().execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


def login_required(view: Callable) -> Callable:
    @functools.wraps(view)
    def wrapped(**kwargs):
        if g.user is None:
            return redirect(url_for("auth.login", next=request.path))
        return view(**kwargs)

    return wrapped


def admin_required(view: Callable) -> Callable:
    @functools.wraps(view)
    def wrapped(**kwargs):
        if g.user is None:
            return redirect(url_for("auth.login", next=request.path))
        if g.user["role"] != "admin":
            abort(403)
        return view(**kwargs)

    return wrapped


def _validate_register(username: str, first: str, last: str, email: str, password: str) -> str | None:
    if not all([username, first, last, email, password]):
        return "Fill in every field to create an account."
    if not USERNAME_RE.match(username):
        return "Usernames start with a letter and use 3–32 letters, numbers, or underscores."
    if not EMAIL_RE.match(email):
        return "Enter an email address like name@example.com."
    if len(password) < 8:
        return "Choose a password with at least 8 characters."
    if len(first) > 80 or len(last) > 80:
        return "Names must be shorter than 80 characters."
    return None


@bp.route("/register", methods=["GET", "POST"])
def register():
    if g.user:
        return redirect(url_for("home.dashboard"))
    errors: dict[str, str] = {}
    form = {"username": "", "firstname": "", "lastname": "", "email": ""}
    if request.method == "POST":
        form["username"] = request.form.get("username", "").strip()
        form["firstname"] = request.form.get("firstname", "").strip()
        form["lastname"] = request.form.get("lastname", "").strip()
        form["email"] = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        message = _validate_register(
            form["username"], form["firstname"], form["lastname"], form["email"], password
        )
        if message:
            flash(message, "error")
            return render_template("auth/register.html", form=form, errors=errors)
        db = get_db()
        starting = float(current_app.config["STARTING_CASH"])
        try:
            db.execute(
                """INSERT INTO users
                   (username, first_name, last_name, email, password_hash, cash_balance, role)
                   VALUES (?, ?, ?, ?, ?, ?, 'user')""",
                (
                    form["username"],
                    form["firstname"],
                    form["lastname"],
                    form["email"],
                    generate_password_hash(password),
                    starting,
                ),
            )
            db.commit()
        except db.IntegrityError:
            flash("That username or email is already registered. Log in or pick another.", "error")
            return render_template("auth/register.html", form=form, errors=errors)
        flash("Account created. Log in to start with $1,000,000 virtual cash.", "success")
        return redirect(url_for("auth.login"))
    return render_template("auth/register.html", form=form, errors=errors)


@bp.route("/login", methods=["GET", "POST"])
def login():
    if g.user:
        return redirect(url_for("home.dashboard"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = get_db().execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()
        if user is None or not check_password_hash(user["password_hash"], password):
            flash("That username and password did not match. Try again.", "error")
            return render_template("auth/login.html", username=username)
        session.clear()
        session["user_id"] = user["id"]
        session["role"] = user["role"]
        session.permanent = True
        nxt = request.args.get("next") or request.form.get("next")
        if nxt and nxt.startswith("/") and not nxt.startswith("//"):
            return redirect(nxt)
        if user["role"] == "admin":
            return redirect(url_for("admin.summary"))
        return redirect(url_for("home.dashboard"))
    return render_template("auth/login.html", username="")


@bp.route("/logout", methods=["GET", "POST"])
def logout():
    session.clear()
    flash("You are logged out.", "success")
    return redirect(url_for("auth.login"))
