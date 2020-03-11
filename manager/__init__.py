import atexit
import functools
import logging
import re
import sys
import time
from datetime import datetime, timedelta

import bcrypt
import boto3
from apscheduler.schedulers.background import BackgroundScheduler
from flask import (Blueprint, Flask, g, jsonify, redirect, render_template,
                   request, session, url_for)
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc, update

from manager import auth, workers
from manager.aws import autoscale, instance_manager
from manager.config import Config

from .auth import login_required

ec2_manager = instance_manager.InstanceManager()
auto_scaler = autoscale.AutoScaler(
    ec2_manager, upper_threshold=70, lower_threshold=30, ideal_cpu=50)
db = SQLAlchemy()
scheduler = BackgroundScheduler()
scheduler.start()


def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)
    db.init_app(app)
    with app.app_context():
        db.create_all()

    app.register_blueprint(workers.bp)
    app.register_blueprint(auth.bp)
    @app.route('/')
    @app.route('/home')
    @app.route('/index')
    @app.route('/dashboard')
    @login_required
    def dashboard():
        """[summary]
        this endpoint renders index page (dashboard view)
        Returns:
            [type] -- [description] html for dashboard view
        """
        return render_template('dashboard.html')

    @app.route('/workers_dashboard')
    @login_required
    def workers_dashboard():
        """[summary] this endpoint renders the workers dashboard view

        Returns:
            [type] -- [description] html for workers dashboard
        """
        return render_template('workers_dashboard.html')

    @app.route('/workers_configuration')
    @login_required
    def worker_configuration():
        """[summary] this endpoint renders the worker configuration view

        Returns:
            [type] -- [description] html for worker configuration view
        """
        return render_template('workers_configuration.html')

    @app.route('/autoscale_policy')
    def autoscale_policy():
        """[summary] this endpoint renders the auto-scale policy page
        Returns:
            [type] -- [description] html for auto-scale policy
        """
        return render_template('autoscale_policy.html')

    @app.route('/terminate', methods=['POST'])
    @login_required
    def terminate():
        """[summary] this endpoint accepts a POST request. It terminates all worker instances and 
        the manager application itself.
        """
        instances = ec2_manager.get_instances(alive=True)
        instance_ids = [instance['InstanceId'] for instance in instances]
        ec2_manager.terminate_instances(instance_ids)
        sys.exit(0)

    @app.route('/clearall', methods=['DELETE'])
    @login_required
    def clearall():
        s3_clear = boto3.resource('s3')
        bucket_clear = s3_clear.Bucket('ece1779-a2-pic')
        for key in bucket_clear.objects.all():
            key.delete()

        ManagerUserModel.query.delete()
        db.session.commit()
        ImageModel.query.delete()
        db.session.commit()

    @app.route('/submitscale', methods=['POST'])
    def submitscale():
        try:
            upper_threshold = request.form['upper-threshold']
            lower_threshold = request.form['lower-threshold']
            ideal_cpu = request.form['ideal-cpu']

            result_threshold = r'^.{0,100}$'
            result_password = r'^.{6,}$'

            assert re.match(result_threshold, upper_threshold, re.M | re.I)
            "Threshold should be between 0~100(%)"
            assert re.match(result_threshold, lower_threshold, re.M | re.I)
            "Threshold should be between 0~100(%)"
            assert upper_threshold >= lower_threshold, "Upper threshold should be higher than lower threshold"

            scale_policy = AutoscalePolicyModel.query.first()

            if(scale_policy is None):
                new_policy = AutoscalePolicyModel(
                    upper_threshold=upper_threshold, lower_threshold=lower_threshold, ideal_cpu=ideal_cpu)
                db.session.add(new_policy)
                db.session.commit()

            else:
                scale_policy.upper_threshold = upper_threshold
                scale_policy.lower_threshold = lower_threshold
                scale_policy.ideal_cpu = ideal_cpu
                db.session.commit()

            auto_scaler.set_policy(upper_threshold=upper_threshold,
                                   lower_threshold=lower_threshold, ideal_cpu=ideal_cpu)

            return jsonify({
                'isSuccess': True,
                'url': url_for('autoscale_policy')
            })

        except AssertionError as e:
            return jsonify({
                'isSuccess': False,
                'message': e.args
            })

    scheduler.add_job(func=auto_scaler.auto_scale,
                      trigger='interval', seconds=60)

    atexit.register(lambda: scheduler.shutdown())

    auto_scaler.scale_up()

    return app


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
    username = db.Column(db.String(100), db.ForeignKey(
        "Users.username"), nullable=True)
    currenttime = db.Column(db.String(45), nullable=True)
    pictype = db.Column(db.String(45), nullable=True)


class ManagerUserModel(db.Model):
    __tablename__ = 'AdminUsers'
    username = db.Column(db.String(100), unique=True,
                         primary_key=True, index=True)
    password = db.Column(db.String(64), unique=False)


class AutoscalePolicyModel(db.Model):
    __tablename__ = 'AutoscalePolicy'
    id = db.Column(db.Integer, unique=True, nullable=True,
                   primary_key=True)
    upper_threshold = db.Column(
        db.Integer, unique=False, nullable=True, default=70)
    lower_threshold = db.Column(
        db.Integer, unique=False, nullable=True, default=30)
    ideal_cpu = db.Column(db.Integer, unique=False, nullable=True, default=50)
