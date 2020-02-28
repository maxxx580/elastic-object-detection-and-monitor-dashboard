from datetime import timedelta

from flask import Flask, url_for, redirect, render_template
from manager import workers


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

    return app
