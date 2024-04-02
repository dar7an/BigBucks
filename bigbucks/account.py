from flask import Blueprint, flash, g, redirect, render_template, request, url_for
from .db import get_db

bp = Blueprint("account", __name__, url_prefix="/account")
@bp.route("/", methods=["GET", "POST"])
def account():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        db = get_db()
        error = None
        if error is None:
            try:
                if password:
                    db.execute(
                        "UPDATE Users SET password = ?, email = ? WHERE userID = ?",
                        (password, email, g.user['userID']),
                    )
                else:
                    db.execute(
                        "UPDATE Users SET email = ? WHERE userID = ?",
                        (email, g.user['userID']),
                    )
                db.commit()
                flash("Your account has been updated.")
                return redirect(url_for("account.account"))
            except db.IntegrityError:
                error = "Could not update the account."

        flash(error)

    return render_template("account.html", user=g.user)