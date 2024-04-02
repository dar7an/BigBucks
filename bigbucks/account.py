from flask import Blueprint, flash, g, redirect, render_template, request, url_for
from werkzeug.security import generate_password_hash
from .db import get_db

bp = Blueprint("account", __name__, url_prefix="/account")

@bp.route("/", methods=["GET", "POST"])
def account():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        new_password = request.form["new_password"]
        db = get_db()
        error = None
        
        if not username:
            error = "Username is required."
        elif not email:
            error = "Email is required."
        elif new_password and len(new_password) < 8:
            error = "Password must be at least 8 characters long."
        
        if error is None:
            try:
                if new_password:
                    db.execute(
                        "UPDATE Users SET username = ?, email = ?, password = ? WHERE userID = ?",
                        (username, email, generate_password_hash(new_password), g.user['userID']),
                    )
                else:
                    db.execute(
                        "UPDATE Users SET username = ?, email = ? WHERE userID = ?",
                        (username, email, g.user['userID']),
                    )
                db.commit()
                flash("Your account has been updated.")
                return redirect(url_for("account.account"))
            except db.IntegrityError:
                error = f"User {username} is already registered."
        
        flash(error)
    
    return render_template("account.html", user=g.user)

