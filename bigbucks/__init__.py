"""Flask application factory."""

from __future__ import annotations

from pathlib import Path

from flask import Flask, render_template
from flask_wtf.csrf import CSRFError, CSRFProtect

from . import formatters

csrf = CSRFProtect()


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    db_folder = Path(app.root_path) / "database"
    db_folder.mkdir(parents=True, exist_ok=True)
    app.config.from_object("bigbucks.config.Config")
    app.config.setdefault("DATABASE", str(db_folder / "stock_database.db"))
    if test_config:
        app.config.update(test_config)

    csrf.init_app(app)

    from . import db as db_module

    db_module.init_app(app)

    from . import account, admin, auth, history, home, metrics, search, trade

    app.register_blueprint(auth.bp)
    app.register_blueprint(home.bp)
    app.register_blueprint(search.bp)
    app.register_blueprint(trade.bp)
    app.register_blueprint(account.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(metrics.bp)
    app.register_blueprint(history.bp)

    app.add_url_rule("/", endpoint="index", view_func=home.index)
    app.before_request(auth.load_logged_in_user)

    app.jinja_env.filters["usd"] = formatters.usd
    app.jinja_env.filters["signed_usd"] = formatters.signed_usd
    app.jinja_env.filters["pct"] = formatters.pct
    app.jinja_env.filters["signed_pct"] = formatters.signed_pct
    app.jinja_env.filters["compact"] = formatters.compact_number
    app.jinja_env.filters["shares"] = formatters.shares
    app.jinja_env.filters["zip"] = zip

    @app.context_processor
    def inject_globals():
        return {
            "paper_disclaimer": (
                "Paper trading — $1,000,000 virtual cash, last close, whole shares, no commissions."
            )
        }

    @app.errorhandler(404)
    def not_found(_e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(403)
    def forbidden(_e):
        return render_template("errors/403.html"), 403

    @app.errorhandler(500)
    def server_error(_e):
        return render_template("errors/500.html"), 500

    @app.errorhandler(CSRFError)
    def csrf_error(_e):
        from flask import flash, redirect, request, url_for

        flash("This form expired. Refresh the page and try again.", "error")
        target = request.referrer or url_for("home.index")
        return redirect(target)

    @app.after_request
    def security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        return response

    return app
