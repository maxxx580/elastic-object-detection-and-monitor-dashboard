from datetime import timedelta

from flask import Flask, url_for, redirect


def create_app():

	app = Flask(__name__, instance_relative_config=True)
	app.config.from_mapping(
		SECRET_KEY='dev',
		PERMANENT_SESSION_LIFETIME=timedelta(minutes=60 * 24)
	)
	return app
