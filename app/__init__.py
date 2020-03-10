import os
from datetime import timedelta

from flask import Flask, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy_utils import create_database, database_exists

from app import error, image, user
from app.config import Config

from .user import login_required

db = SQLAlchemy()


def create_app(test_config=None):

    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    # app.config.from_mapping(
    #     SECRET_KEY='dev',
    #     PERMANENT_SESSION_LIFETIME=timedelta(minutes=60 * 24)
    # )

    app.config.from_object(Config)
    db.init_app(app)
    with app.app_context():
        db.create_all()

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


class UserModel(db.Model):
    __tablename__ = 'Users'
    # id = db.Column(db.Integer, unique=True, nullable=True)
    # ,primary_key=True)  # Auto-increment should be default
    username = db.Column(db.String(100), unique=True,
                         primary_key=True, index=True)
    password = db.Column(db.String(64), unique=False)


class ImageModel(db.Model):
    __tablename__ = 'Images'
    id = db.Column(db.Integer, unique=True, nullable=True,
                   primary_key=True)  # Auto-increment should be default
    location = db.Column(db.String(200), nullable=True)
    username = db.Column(db.String(200), db.ForeignKey(
        "Users.username"), nullable=True)
    currenttime = db.Column(db.String(45), nullable=True)
    pictype = db.Column(db.String(45), nullable=True)
