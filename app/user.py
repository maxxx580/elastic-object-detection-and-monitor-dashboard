import functools
import logging
import re

import bcrypt
from flask import (Blueprint, abort, flash, g, jsonify, redirect,
                   render_template, request, session, url_for)
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import update
from werkzeug.exceptions import abort

import app

bp = Blueprint("user", __name__)


def login_required(view):
    """View decorator that redirects anonymous users to the login page."""

    @functools.wraps(view)
    def wrapped_view(**kwargs):
        logger = logging.getLogger()
        if g.user is None:
            logger.info("user yet logged in, redirecting log-in page")
            return redirect(url_for("user.login"))
        logger.info('user already logged in')
        return view(**kwargs)
    return wrapped_view


@bp.before_app_request
def load_logged_in_user():

    username = session.get('username')

    if username is None:
        g.user = None

    g.user = username


@bp.route("/api/register", methods=("GET", "POST"))
def register():
    """Register a new user.
    Validates that the username is not already taken. Hashes the
    password for security.
    """
    if request.method == "GET":
        return render_template('user/register.html')

    username = request.form['username']
    password = request.form['password']

    try:

        assert username is not None, "Please enter username"
        assert password is not None, "Please enter password"

        result_name = r'^[A-Za-z0-9._-]{2,100}$'
        result_password = r'^.{6,}$'

        assert re.match(result_name, username, re.M | re.I)
        "Username should have 2 to 100 characters, and only contains letter, number, underline and dash."
        assert re.match(result_password, password)
        "Password should have 6 to 18 characters"

        password = password.encode('utf-8')
        # cnx = get_db()
        # db_cursor = cnx.cursor()
        #
        # db_cursor.execute(
        #     'select * from User where username="%s"' % (username))
        # user = db_cursor.fetchone()

        user = app.UserModel.query.filter_by(username=username).first()
        assert user is None, "Username exists"

        salt = bcrypt.gensalt()

        pw_hashed = bcrypt.hashpw(password, salt)

        new_user = app.UserModel(username=username, password=pw_hashed)
        app.db.session.add(new_user)
        app.db.session.commit()

        return redirect(url_for("user.login"))

    except AssertionError as e:
        flash(e)
        print(e)
        return render_template('user/register.html', e=e.args)

    except Exception as e:
        flash(e)
        print(e)
        return render_template('user/register.html', e=e)

    finally:

        pass


@bp.route('/api/login', methods=['GET', 'POST'])
def login():
    """[this api is used to authenticate user. It retrieves HTML login view with HTTP GET. 
    it authencate user's credential with HTTP POST]

    Returns:
        [HTML] -- [this endpoint returns html profile view upon successful authentication, 
        otherwise login view with error message]
    """
    logger = logging.getLogger()
    if request.method == 'GET':
        return render_template('user/login.html')

    username = request.form['username']
    password = request.form['password']

    try:

        authenticate(username, password)

        session.clear()
        session.permanent = True

        session['username'] = username

        return redirect(url_for('image.profile'))

    except AssertionError as e:
        flash(e)
        logger.error(e.args)
        return render_template('user/login.html', e=e.args)

    except Exception as e:
        flash(e)
        logger.error(e)
        return render_template('user/login.html')
    finally:
        pass


@bp.route("/api/logout")
@login_required
def logout():
    """Clear the current session, including the stored user id."""
    session.clear()
    return redirect(url_for("user.login"))


def authenticate(username, password):

    assert username is not None, "invalid username"
    assert password is not None, "invalid password"

    # db_cursor = get_db().cursor()
    # db_cursor.execute(
    #     'select * from User where username="%s"' % (username))
    # user = db_cursor.fetchone()

    user = app.UserModel.query.filter_by(
        username=username).first()

    assert user is not None, "invalid credential"
    assert bcrypt.checkpw(password.encode('utf-8'),
                          user.password.encode('utf-8')), "invalid credential"
