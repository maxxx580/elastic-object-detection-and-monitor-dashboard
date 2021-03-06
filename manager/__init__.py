import atexit
import functools
import logging
import re
import sys
import time
from datetime import datetime, timedelta

import bcrypt
import boto3
import botocore
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
    ec2_manager, upper_threshold=70, lower_threshold=30, increase_ratio=2, decrease_ratio=0.5)
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
        auto_policy = AutoscalePolicyModel.query.first();

        if (auto_policy is None):
            new_policy = AutoscalePolicyModel(
                upper_threshold=70, lower_threshold=30,
                increase_ratio=2, decrease_ratio=0.5)
            db.session.add(new_policy)
            db.session.commit()
        else:
            auto_scaler.set_policy(upper_threshold=auto_policy.upper_threshold,
                                   lower_threshold=auto_policy.lower_threshold,
                                   increase_ratio=auto_policy.increase_ratio,
                                   decrease_ratio=auto_policy.decrease_ratio)

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
        stop the manager application itself.
        """
        instances = ec2_manager.get_instances(alive=True)
        manager_instances = ec2_manager.get_instances(
            alive=True, manager_instances=True)
        instance_ids = [instance['InstanceId'] for instance in instances]
        manager_ids = [instance['InstanceId']
                       for instance in manager_instances]
        ec2_manager.stop_instances(manager_ids)
        ec2_manager.terminate_instances(instance_ids)
        sys.exit(0)

    @app.route('/clearall', methods=['DELETE'])
    @login_required
    def clearall():
        """[summary] this endpoint accepts DELETE request and removes all item from MySql and S3

        Returns:
            [type] -- [description] this endpiont returns json object
            {
                isSucess: boolean indecating if operation is successful,
                message: error message if applicable
            }

        """
        try:
            s3 = boto3.resource('s3').Bucket(
                'ece1779-a2-pic').objects.all().delete()
            ImageModel.query.delete()
            db.session.commit()
            UserModel.query.delete()
            db.session.commit()
            return jsonify({
                'isSuccess': True
            })
        except botocore.exceptions.ClientError as e:
            return jsonify({
                'isSuccess': False,
                'message': e.args
            })

    @app.route('/submitscale', methods=['POST'])
    def submitscale():
        try:
            upper_threshold = float(request.form['upper-threshold'])
            lower_threshold = float(request.form['lower-threshold'])
            increase_ratio = float(request.form['increase-ratio'])
            decrease_ratio = float(request.form['decrease-ratio'])

            assert 0 < upper_threshold < 100,\
                "Threshold should be between 0~100(%)"
            assert 0 < lower_threshold < 100,\
                "Threshold should be between 0~100(%)"
            assert increase_ratio > 1,\
                "Increase ratio should be larger than 1"
            assert 0 < decrease_ratio < 1,\
                "Decrease ratio should be between 0~1"
            assert upper_threshold >= lower_threshold, \
                "Upper threshold should be higher than lower threshold"

            scale_policy = AutoscalePolicyModel.query.first()

            if(scale_policy is None):
                new_policy = AutoscalePolicyModel(
                    upper_threshold=upper_threshold, lower_threshold=lower_threshold,
                    increase_ratio=increase_ratio, decrease_ratio=decrease_ratio)
                db.session.add(new_policy)
                db.session.commit()

            else:
                scale_policy.upper_threshold = upper_threshold
                scale_policy.lower_threshold = lower_threshold
                scale_policy.increase_ratio = increase_ratio
                scale_policy.decrease_ratio = decrease_ratio
                db.session.commit()

            auto_scaler.set_policy(upper_threshold=upper_threshold,
                                   lower_threshold=lower_threshold,
                                   increase_ratio=increase_ratio,
                                   decrease_ratio=decrease_ratio)

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

    @app.route('/loadpolicy', methods=['GET'])
    @login_required
    def load_policy():
        load_policy = AutoscalePolicyModel.query.first()
        return jsonify({
                'isSuccess': True,
                'upper_threshold': load_policy.upper_threshold,
                'lower_threshold': load_policy.lower_threshold,
                'increase_ratio': load_policy.increase_ratio,
                'decrease_ratio': load_policy.decrease_ratio
            })

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
        db.Float, unique=False, nullable=True, default=70)
    lower_threshold = db.Column(
        db.Float, unique=False, nullable=True, default=30)
    increase_ratio = db.Column(
        db.Float, unique=False, nullable=True, default=2)
    decrease_ratio = db.Column(
        db.Float, unique=False, nullable=True, default=0.5)
