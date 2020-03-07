import functools
import atexit
import logging
import sys
import time

import re

import boto3
from datetime import datetime, timedelta
import app
from app import UserModel, ImageModel, db
from sqlalchemy import desc

from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, redirect, render_template, request, url_for, jsonify, session, g, Blueprint
from flask_caching import Cache
from flask_sqlalchemy import SQLAlchemy


import bcrypt
from manager.config import Config
from manager import workers
from manager.aws import autoscale, instance_manager

worker_pool_size = []
ec2_manager = instance_manager.InstanceManager()
auto_scaler = autoscale.AutoScaler(ec2_manager)
db = SQLAlchemy()

bp = Blueprint('auth', __name__)


def create_app():
    logger = logging.getLogger('manager')
    app = Flask(__name__, instance_relative_config=True)
    app.register_blueprint(workers.bp)
    app.config.from_object(Config)
    db.init_app(app)

    with app.app_context():
        db.create_all()

    @app.route('/')
    @app.route('/home')
    @app.route('/index')
    @app.route('/dashboard')
    def dashboard():
        return render_template('dashboard.html')

    @app.route('/workers_dashboard')
    def workers_dashboard():
        return render_template('workers_dashboard.html')

    @app.route('/workers_configuration')
    def worker_configuration():
        return render_template('workers_configuration.html')

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'GET':
            return render_template('register.html')
        try:

            username = request.form['username']
            password = request.form['password']

            assert username is not None, "Please enter username"
            assert password is not None, "Please enter password"

            result_name = r'^[A-Za-z0-9._-]{2,100}$'
            result_password = r'^.{6,}$'

            assert re.match(result_name, username, re.M | re.I)
            "Username should have 2 to 100 characters, and only contains letter, number, underline and dash."
            assert re.match(result_password, password)
            "Password should have 6 to 18 characters"

            password = password.encode('utf-8')

            user = ManagerUserModel.query.filter_by(username=username).first()
            assert user is None, "Username exists"

            salt = bcrypt.gensalt()

            pw_hashed = bcrypt.hashpw(password, salt)

            new_user = ManagerUserModel(
                username=username, password=pw_hashed)
            db.session.add(new_user)
            db.session.commit()

            return jsonify({
                'isSuccess': True,
                'url': url_for('login')
            })

        except AssertionError as e:
            return jsonify({
                'isSuccess': False,
                'message': e.args
            })

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'GET':
            return render_template('login.html')

        try:

            username = request.form['username']
            password = request.form['password']

            authenticate(username, password)

            session.clear()
            session.permanent = True

            session['username'] = username

            return jsonify({
                'isSuccess': True,
                'url': url_for('dashboard')
            })

        except AssertionError as e:
            return jsonify({
                'isSuccess': False,
                'message': e.args
            })

    @app.route('/logout', methods=['POST'])
    def logout():
        session.clear()
        return render_template('logint.html')

    @app.route('/terminate', methods=['POST'])
    def terminate():
        assert (len(auto_scaler.worker_pool)+len(auto_scaler.starting_up_pool)) != 0, 'Manager has already been terminated'
        if len(auto_scaler.worker_pool) >0:
            ec2_manager.terminate_instance(list(auto_scaler.worker_pool))
        if len(auto_scaler.starting_up_pool) >0:
            ec2_manager.terminate_instance(list(auto_scaler.starting_up_pool))

        sys.exit(0)

    # @app.route('/clearall',methods=['DELETE'])
    # def clearall():
    #     # s3 = boto3.resource('s3')
    #     # bucket = s3.Bucket('ece1779-a2-images')
    #     # bucket.objects.all().delete()
    #     UserModel.query.delete()
    #     db.session.commit()
    #     ImageModel.query.delete()
    #     db.session.commit()
    def login_required(view):
        """View decorator that redirects anonymous users to the login page."""

        @functools.wraps(view)
        def wrapped_view(**kwargs):
            logger = logging.getLogger()
            if g.user is None:
                logger.info("user yet logged in, redirecting log-in page")
                return redirect(url_for("user.login"))
            logger.info('user already logged in')
            return view(**kwargs)
        return wrapped_view

    @bp.before_app_request
    def load_logged_in_user():

        username = session.get('username')

        if username is None:
            g.user = None

        g.user = username

    def _update_worker_pool_size():
        if len(worker_pool_size) > 30:
            worker_pool_size.pop(0)
        worker_pool_size.append(
            (len(auto_scaler.worker_pool), datetime.utcnow()))
        logger.info(msg="[%s] updated worker pool; current worker pool size is %d" %
                    (str(datetime.now()), worker_pool_size[-1][0]))

    _update_worker_pool_size()
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=_update_worker_pool_size,
                      trigger="interval", seconds=60)
    scheduler.add_job(func=auto_scaler.auto_update,
                      trigger='interval', seconds=10)
    scheduler.add_job(func=auto_scaler.auto_scale,
                      trigger='interval', seconds=60)
    scheduler.start()

    atexit.register(lambda: scheduler.shutdown())
    return app


def authenticate(username, password):

    assert username is not None, "invalid username"
    assert password is not None, "invalid password"

    user = ManagerUserModel.query.filter_by(
        username=username).first()

    assert user is not None, "invalid credential"
    assert bcrypt.checkpw(password.encode('utf-8'),
                          user.password.encode('utf-8')), "invalid credential"


class ManagerUserModel(db.Model):
    __tablename__ = 'Users'
    username = db.Column(db.String(100), unique=True,
                         primary_key=True, index=True)
    password = db.Column(db.String(64), unique=False)


class ImageModel(db.Model):
    __tablename__ = 'Images'
    id = db.Column(db.Integer, unique=True, nullable=True,
                   primary_key=True)
    location = db.Column(db.String(200), nullable=True)
    username = db.Column(db.String(200), db.ForeignKey(
        "Users.username"), nullable=True)
    currenttime = db.Column(db.String(45), nullable=True)
    pictype = db.Column(db.String(45), nullable=True)


class ManagerManagerUserModel(db.Model):
    __tablename__ = 'AdminUsers'
    username = db.Column(db.String(100), unique=True,
                         primary_key=True, index=True)
    password = db.Column(db.String(64), unique=False)
