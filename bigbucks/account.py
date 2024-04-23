from flask import Blueprint, flash, g, redirect, render_template, request, url_for
from werkzeug.security import generate_password_hash
from .db import get_db
from .home import login_required

bp = Blueprint("account", __name__, url_prefix="/account")

@bp.route("/", methods=["GET", "POST"])
@login_required
def account():
    if request.method == "POST":
        db = get_db()
        error = None

        # Initialize variables, use None if key doesn't exist
        email = request.form.get("email")
        password = request.form.get("password")

        try:
            if password:
                password = generate_password_hash(password)  # hash the new password

            if password and email:  # if both email and password are provided
                db.execute(
                    "UPDATE Users SET password = ?, email = ? WHERE userID = ?",
                    (password, email, g.user['userID']),
                )
            elif email:  # if only email is provided
                db.execute(
                    "UPDATE Users SET email = ? WHERE userID = ?",
                    (email, g.user['userID']),
                )
            elif password:  # if only password is provided
                db.execute(
                    "UPDATE Users SET password = ? WHERE userID = ?",
                    (password, g.user['userID']),
                )
            else:
                error = "No updates were provided."

            db.commit()

            if error is None:
                flash("Your account has been updated.")
                return redirect(url_for("account.account"))
            else:
                flash(error)

        except db.IntegrityError:
            flash("Could not update the account.")

    return render_template("account.html", user=g.user)
