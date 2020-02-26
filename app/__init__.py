import os
from datetime import timedelta

from flask import Flask, url_for, redirect

from app import error
from . import db, image, user
from .user import login_required


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
    app.register_error_handler(404, error.page_not_found)
    app.register_error_handler(403, error.forbidden)
    app.register_error_handler(401, error.unauthorized)
    app.register_error_handler(500, error.server_error)
    app.register_error_handler(400, error.bad_request)

    @app.route('/')
    @app.route('/index')
    @app.route('/api')
    @login_required
    def index():
        return redirect(url_for('image.profile'))

    return app
