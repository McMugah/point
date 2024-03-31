import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt


db = SQLAlchemy()
login_manager = LoginManager()
bcrypt  = Bcrypt()

def create_app(config_name):
    app = Flask(__name__)

    # apply configuration
    cfg = os.path.join(os.getcwd(), 'config', config_name + '.py')
    app.config.from_pyfile(cfg)
    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)


    from .api_v1.user import api
    app.register_blueprint(api)


    return app
