import atexit
import logging
import sys
import time
from datetime import datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, redirect, render_template, url_for
from flask_caching import Cache

from manager import workers
from manager.aws import autoscale, instance_manager

worker_pool_size = []
ec2_manager = instance_manager.InstanceManager()
auto_scaler = autoscale.AutoScaler(ec2_manager)


def create_app():
    logger = logging.getLogger('manager')
    app = Flask(__name__, instance_relative_config=True)
    app.register_blueprint(workers.bp)

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

    @app.route('/login', methods=['POST'])
    def login():
        pass

    @app.route('/logout', methods=['POST'])
    def logout():
        pass

    @app.route('/terminate', methods=['POST'])
    def terminate():
        assert (len(auto_scaler.worker_pool)+len(auto_scaler.starting_up_pool)) != 0, 'Manager has already been terminated'
        if len(auto_scaler.worker_pool) >0:
            ec2_manager.terminate_instance(list(auto_scaler.worker_pool))
        if len(auto_scaler.starting_up_pool) >0:
            ec2_manager.terminate_instance(list(auto_scaler.starting_up_pool))
        sys.exit(0)


    def update_worker_pool_size():
        if len(worker_pool_size) > 30:
            worker_pool_size.pop(0)
        worker_pool_size.append(
            (len(auto_scaler.worker_pool), datetime.utcnow()))
        logger.info(msg="[%s] updated worker pool; current worker pool size is %d" %
                    (str(datetime.now()), worker_pool_size[-1][0]))

    update_worker_pool_size()
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=update_worker_pool_size,
                      trigger="interval", seconds=60)
    scheduler.add_job(func=auto_scaler.auto_update,
                      trigger='interval', seconds=10)
    scheduler.add_job(func=auto_scaler.auto_scale,
                      trigger='interval', seconds=60)
    scheduler.start()

    atexit.register(lambda: scheduler.shutdown())
    return app
