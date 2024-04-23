from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from sqlite3 import IntegrityError
from .transactions import update_portfolio_data, update_stock_data
from .db import get_db

bp = Blueprint("auth", __name__, url_prefix="/auth")


def load_logged_in_user():
    """Load the logged-in user's details into `g.user` from the session."""
    user_id = session.get("userID")
    g.user = get_db().execute(
        "SELECT * FROM Users WHERE userID = ?", (user_id,)
    ).fetchone() if user_id else None


bp.before_app_request(load_logged_in_user)


def register_user(db, username: str, firstname: str, lastname: str, email: str, password: str) -> None:
    """Attempt to register a new user and handle database insertion."""
    try:
        db.execute(
            "INSERT INTO Users (userID, firstName, lastName, email, password, cashBalance, role) VALUES (?, ?, ?, ?, "
            "?, 1000000, 'user')",
            (username, firstname, lastname, email, generate_password_hash(password))
        )
        db.commit()
    except IntegrityError:
        raise ValueError(f"User {username} is already registered.")


@bp.route("/register", methods=["GET", "POST"])
def register():
    """Handle user registration."""
    if request.method == "POST":
        form_data = {key: request.form[key] for key in ["username", "firstname", "lastname", "email", "password"]}
        if any(not form_data[key] for key in form_data):
            flash("All fields are required.")
            return render_template("auth/register.html")

        db = get_db()
        try:
            register_user(db, **form_data)
            flash("Registration successful. Please log in.")
            return redirect(url_for("auth.login"))
        except ValueError as e:
            flash(str(e))
    return render_template("auth/register.html")


@bp.route("/login", methods=["GET", "POST"])
def login():
    """Handle user login."""
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = get_db().execute(
            "SELECT * FROM Users WHERE userID = ?", (username,)
        ).fetchone()

        if user and check_password_hash(user["password"], password):
            session.clear()
            session.update(userID=user["userID"], role=user["role"])
            update_portfolio_data(user["userID"])
            update_stock_data("SPY")
            redirect_route = "admin.summary" if user["role"] == "admin" else "home.home"
            return redirect(url_for(redirect_route))

        flash("Incorrect username or password.")
    return render_template("auth/login.html")


@bp.route("/logout")
def logout():
    """Log out the current user by clearing the session."""
    session.clear()
    return redirect(url_for("auth.login"))
