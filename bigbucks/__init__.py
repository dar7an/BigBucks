import os

from flask import Flask


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)

    # Define the path to the database folder within the Flask application directory
    db_folder = os.path.join(app.root_path, 'database')

    # Ensure the database folder exists
    try:
        os.makedirs(db_folder)
    except OSError:
        pass

    # Define the path to the database file inside the database folder
    db_path = os.path.join(db_folder, 'stock_database.db')

    app.config.from_mapping(
        SECRET_KEY="dev",
        # Use the modified database path
        DATABASE=db_path
    )

    from . import auth
    app.register_blueprint(auth.bp)
    app.add_url_rule('/auth', endpoint='auth')

    from . import home
    app.register_blueprint(home.bp)
    app.add_url_rule('/', endpoint='home')

    from . import search
    app.register_blueprint(search.bp)
    app.add_url_rule('/search', endpoint='search')

    from . import trade
    app.register_blueprint(trade.bp)
    app.add_url_rule('/trade', endpoint='trade')

    from . import account
    app.register_blueprint(account.bp)
    app.add_url_rule('/account', endpoint='account')

    from . import admin
    app.register_blueprint(admin.bp)
    app.add_url_rule('/admin', endpoint='admin')

    from . import metrics
    app.register_blueprint(metrics.bp)
    app.add_url_rule('/metrics', endpoint='metrics')

    from . import db
    db.init_app(app)

    return app
