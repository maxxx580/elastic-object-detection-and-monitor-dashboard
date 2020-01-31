from flask import Flask 
from flask import current_app
from flask import render_template
from datetime import timedelta

from . import user, image, db
from .user import login_required

import os

def create_app(test_config=None):
    
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        PERMANENT_SESSION_LIFETIME=timedelta(minutes=60 * 24)
    )


    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)


    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    db.init_app(app)

    app.register_blueprint(user.bp)
    app.register_blueprint(image.bp)

    @app.route('/')
    @app.route('/index')
    @login_required
    def index():
        return render_template('index.html')
    return app
