import functools

import bcrypt
from flask import (Blueprint, flash, g, jsonify, redirect, render_template,
                   request, session, url_for)
from werkzeug.exceptions import abort

from app.db import close_db, get_db

bp = Blueprint("user", __name__, url_prefix='/user')


def login_required(view):
    """View decorator that redirects anonymous users to the login page."""

    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for("user.login"))
        return view(**kwargs)

    return wrapped_view


@bp.before_app_request
def load_logged_in_user():

    username = session.get('username')

    if username is None:
        g.user = None

    g.user = username


@bp.route("/register", methods=("GET", "POST"))
def register():
    """Register a new user.

    Validates that the username is not already taken. Hashes the
    password for security.
    """
    if request.method == "GET":

        return render_template('user/register.html')

    username = request.form['username']
    password = request.form['password'].encode('utf-8')

    try:

        assert(username is not None)
        assert(password is not None)

        cnx=get_db()
        db_cursor = cnx.cursor()
        salt = bcrypt.gensalt()
        pw_hashed = bcrypt.hashpw(password, salt)
        query = 'INSERT INTO user (username, password) VALUES (%s,%s)'
        db_cursor.execute(query,(username,pw_hashed))

        cnx.commit()

        return redirect(url_for("user.login"))

    except Exception as e:
        print(e)
        return render_template('user/register.html', e=e)

    finally:
        close_db()


@bp.route('login', methods=['GET', 'POST'])
def login():

    if request.method == 'GET':
        return render_template('user/login.html')

    username = request.form['username']
    password = request.form['password']

    try:

        assert(username is not None)
        assert(password is not None)

        db_cursor = get_db().cursor()
        db_cursor.execute(
            'select * from user where username="%s"' % (username))
        user = db_cursor.fetchone()

        assert(user is not None)
        assert(bcrypt.checkpw(password.encode('utf-8'), user[1].encode('utf-8')))

        session.clear()
        session.permanent = True
        session['username'] = username

        return redirect(url_for('index'))

    except Exception as e:
        print(e)
        return render_template('user/login.html')


@bp.route("/")
@login_required
def get_users():
    return render_template('user/index.html')

# db connection test only
@bp.route('/all')
@login_required
def get_all_users():
    db_connection = get_db()
    cursor = db_connection.cursor()
    cursor.execute('select * from User;')
    rows = cursor.fetchall()
    return jsonify(rows)

@bp.route("/logout")
@login_required
def logout():
    """Clear the current session, including the stored user id."""
    session.clear()
    return redirect(url_for("user.login"))
