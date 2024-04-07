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

    from . import homepage
    app.register_blueprint(homepage.bp)
    app.add_url_rule('/', endpoint='homepage')

    from . import stocksearch
    app.register_blueprint(stocksearch.bp)
    app.add_url_rule('/stock_search', endpoint='stock_search')

    from . import buySell
    app.register_blueprint(buySell.bp)
<<<<<<< HEAD
    app.add_url_rule('/buySell', endpoint = 'buySell')
    
    from . import account
    app.register_blueprint(account.bp)
    app.add_url_rule('/account', endpoint = 'account')
=======
    app.add_url_rule('/buySell', endpoint='buySell')

    from . import account
    app.register_blueprint(account.bp)
    app.add_url_rule('/account', endpoint='account')
>>>>>>> 965e0618d926d6d8712a95cec22ba91f52ed1d74

    from . import db
    db.init_app(app)

    return app
