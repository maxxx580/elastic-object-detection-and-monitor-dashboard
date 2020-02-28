import time
import atexit

from datetime import timedelta

from flask import Flask, url_for, redirect, render_template
from flask_caching import Cache
from manager import workers
from manager.aws import autoscale

from apscheduler.schedulers.background import BackgroundScheduler


worker_pool_size = []
auto_scaler = autoscale.AutoScaler()


def create_app():

    app = Flask(__name__, instance_relative_config=True)
    app.register_blueprint(workers.bp)

    @app.route('/')
    @app.route('/home')
    @app.route('/index')
    @app.route('/dashboard')
    def dashboard():
        return render_template('dashboard.html')

    @app.route('/workers_tracking')
    def workers_tracking():
        return render_template('workers_tracking.html')

    def update_worker_pool_size():
        if len(worker_pool_size) > 30:
            worker_pool_size.pop(0)
        worker_pool_size.append(len(auto_scaler.worker_pool))
        print("##############Updating worker pool size: %d ############" %
              worker_pool_size[-1])

    scheduler = BackgroundScheduler()
    scheduler.add_job(func=update_worker_pool_size,
                      trigger="interval", seconds=60)
    scheduler.start()

    # Shut down the scheduler when exiting the app
    atexit.register(lambda: scheduler.shutdown())

    return app
