from datetime import timedelta

from flask import Flask, url_for, redirect, render_template
from manager import workers


def create_app():

    app = Flask(__name__, instance_relative_config=True)
    app.register_blueprint(workers.bp)

    @app.route('/')
    @app.route('/home')
    @app.route('/index')
    def index():
        return render_template('index.html')

    return app
