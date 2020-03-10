import atexit
import functools
import logging
import re
import sys
import threading
import time
from datetime import datetime, timedelta

import bcrypt
import boto3
from apscheduler.schedulers.background import BackgroundScheduler
from flask import (Blueprint, Flask, g, jsonify, redirect, render_template,
                   request, session, url_for)
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc

from manager import workers
from manager.aws import autoscale, instance_manager
from manager.config import Config

lock = threading.Lock()
worker_pool_size = []
ec2_manager = instance_manager.InstanceManager()
auto_scaler = autoscale.AutoScaler(ec2_manager)
db = SQLAlchemy()
scheduler = BackgroundScheduler()
scheduler.start()

bp = Blueprint('auth', __name__)


def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)
    db.init_app(app)
    with app.app_context():
        db.create_all()

    app.register_blueprint(workers.bp)
    @app.route('/')
    @app.route('/home')
    @app.route('/index')
    @app.route('/dashboard')
    def dashboard():
        """[summary]
        this endpoint renders index page (dashboard view)
        Returns:
            [type] -- [description] html for dashboard view
        """
        return render_template('dashboard.html')

    @app.route('/workers_dashboard')
    def workers_dashboard():
        """[summary] this endpoint renders the workers dashboard view

        Returns:
            [type] -- [description] html for workers dashboard
        """
        return render_template('workers_dashboard.html')

    @app.route('/workers_configuration')
    def worker_configuration():
        """[summary] this endpoint renders the worker configuration view

        Returns:
            [type] -- [description] html for worker configuration view
        """
        return render_template('workers_configuration.html')

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        """[summary] this endpoint accepts GET and POST request. 
        Given a GET request, this endpoint renders the register view. 
        Given a POST request, this endpoint creates a new user for manager app

        Returns:
            [type] -- [description] html view for registration view given GET request.
            json object given POST request
            {
                isSuccess: boolean indecating if a user is created successfully,
                url: url to login view given successful user creation,
                message: error message if applicable
            }
        """
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
        """[summary] this endpoint accepts GET and POST requests.
        Given a GET request, this endpoint renders the login view.
        Given a POST request, this endpoint authenticates log in attempts. 

        Returns:
            [type] -- [description] this endpoint renders login view given a GET request.
            this endpoint return json object given POST request
            {
                isSuccess: boolean indecating if a user authentication is successful,
                url: url to dashboard view given successful user authentication,
                message: error message if applicable
            }
        """
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
        """[summary] this endpoint accepts a POST request and logs out an user

        Returns:
            [type] -- [description] html for login view
        """
        session.clear()
        return render_template('logint.html')

    @app.route('/terminate', methods=['POST'])
    def terminate():
        """[summary] this endpoint accepts a POST request. It terminates all worker instances and 
        the manager application itself.
        """
        instances = ec2_manager.get_instances(alive=True)
        instance_ids = [instance['InstanceId'] for instance in instances]
        ec2_manager.terminate_instances(instance_ids)
        sys.exit(0)

    @app.route('/clearall', methods=['DELETE'])
    def clearall():
        s3_clear = boto3.resource('s3')
        bucket_clear = s3_clear.Bucket('ece1779-a2-pic')
        for key in bucket_clear.objects.all():
            key.delete()

        ManagerUserModel.query.delete()
        db.session.commit()
        ImageModel.query.delete()
        db.session.commit()

        return jsonify({
                'isSuccess': True
            })

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

    scheduler.add_job(func=auto_scaler.auto_scale,
                      trigger='interval', seconds=60)

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


class UserModel(db.Model):
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


class ManagerUserModel(db.Model):
    __tablename__ = 'AdminUsers'
    username = db.Column(db.String(100), unique=True,
                         primary_key=True, index=True)
    password = db.Column(db.String(64), unique=False)
