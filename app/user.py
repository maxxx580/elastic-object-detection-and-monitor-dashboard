from flask import Blueprint
from flask import flash
from flask import g
from flask import jsonify
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from werkzeug.exceptions import abort
from app.db import get_db

bp = Blueprint("user", __name__, url_prefix='/user')

@bp.route("/")
def get_users():
    cnt = get_db()
    cursor = cnt.cursor()
    cursor.execute('select * from User;')
    for row in cursor:
        print(row)
    return render_template('user/index.html')

# db connection test only
@bp.route('/all')
def get_all_users():
    db_connection = get_db()
    cursor = db_connection.cursor()
    cursor.execute('select * from User;')
    rows = cursor.fetchall()
    return jsonify(rows)
