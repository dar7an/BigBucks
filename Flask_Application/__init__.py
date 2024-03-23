import os

from flask import Flask

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    
    app.config.from_mapping(
        # store the database in the instance folder
        SECRET_KEY="dev",
        DATABASE=os.path.join(app.instance_path, "stock_database.db")
    )
    
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    
    from . import auth
    app.register_blueprint(auth.bp)
    app.add_url_rule('/auth', endpoint='auth')
    
    from . import homepage
    app.register_blueprint(homepage.bp)
    app.add_url_rule('/', endpoint= 'homepage')
    
    from . import db
    db.init_app(app)

    return app