from flask import Blueprint
from flask import flash
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from werkzeug.exceptions import abort
from app.db import get_db

bp = Blueprint("user", __name__)

@bp.route("/user")
def get_users():
    db = get_db().cursor()
    db.execute('select * from User;')
    return db.fetchone()


