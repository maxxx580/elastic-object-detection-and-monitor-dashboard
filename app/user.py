import functools
import logging
from typing import re

import bcrypt
from flask import (Blueprint, flash, g, jsonify, redirect, render_template,
                   request, session, url_for, abort)

from werkzeug.exceptions import abort

from app.db import close_db, get_db

bp = Blueprint("user", __name__, url_prefix='/user')


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

        assert username is not None, "Please enter username"
        assert password is not None, "Please enter password"

        # result_name = re.compile(r"[\u4e00-\u9fa5]")
        # result_password = re.compile(r"^[a-zA-Z]\w{6,18}")
        #
        #
        # assert result_name.match(username), "Please check the format of username"
        # assert result_password.match(password),"Password should have 6 to 18 characters"

        assert len(password) >= 6, "Password should be longer than 6 characters"
        assert 2 <= len(
            username) <= 100, "Username should have 2~100 characters"

        cnx = get_db()
        db_cursor = cnx.cursor()

        db_cursor.execute(
            'select * from User where username="%s"' % (username))
        user = db_cursor.fetchone()
        assert user is None, "Username exists"

        salt = bcrypt.gensalt()

        pw_hashed = bcrypt.hashpw(password, salt)
        query = 'INSERT INTO User (username, password) VALUES (%s,%s)'
        db_cursor.execute(query, (username, pw_hashed))

        cnx.commit()

        return redirect(url_for("user.login"))

    except AssertionError as e:
        flash(e)
        print(e)
        return render_template('user/login.html', e=e.args)

    except Exception as e:
        flash(e)
        print(e)
        return render_template('user/register.html', e=e)

    finally:
        close_db()


@bp.route('login', methods=['GET', 'POST'])
def login():
    logger = logging.getLogger()
    if request.method == 'GET':
        return render_template('user/login.html')

    username = request.form['username']
    password = request.form['password']

    try:

        assert username is not None, "invalid username"
        assert password is not None, "invalid password"

        db_cursor = get_db().cursor()
        db_cursor.execute(
            'select * from User where username="%s"' % (username))
        user = db_cursor.fetchone()

        assert user is not None, "invalid credential"
        assert bcrypt.checkpw(password.encode('utf-8'),
                              user[1].encode('utf-8')), "invalid credential"

        session.clear()
        session.permanent = True

        session['username'] = username

        return redirect(url_for('index'))

    except AssertionError as e:
        flash(e)
        logger.error(e.args)
        return render_template('user/login.html', e=e.args)

    except Exception as e:
        flash(e)
        logger.error(e)
        return render_template('user/login.html')
    finally:
        close_db()


@bp.route("/logout")
@login_required
def logout():
    """Clear the current session, including the stored user id."""
    session.clear()
    return redirect(url_for("user.login"))
