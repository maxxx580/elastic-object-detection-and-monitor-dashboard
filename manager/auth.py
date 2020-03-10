import functools
import logging
import re

import bcrypt
from flask import (Blueprint, g, jsonify, redirect, render_template, request,
                   session, url_for)

import manager

bp = Blueprint('auth', __name__)


def login_required(view):
    """View decorator that redirects anonymous users to the login page."""

    @functools.wraps(view)
    def wrapped_view(**kwargs):
        logger = logging.getLogger('manager')
        if g.user is None:
            logger.info("user yet logged in, redirecting log-in page")
            return redirect(url_for("auth.login"))
        logger.info('user already logged in')
        return view(**kwargs)
    return wrapped_view


@bp.before_app_request
def load_logged_in_user():

    username = session.get('username')

    if username is None:
        g.user = None

    g.user = username


def authenticate(username, password):

    assert username is not None, "invalid username"
    assert password is not None, "invalid password"

    user = manager.ManagerUserModel.query.filter_by(
        username=username).first()

    assert user is not None, "invalid credential"
    assert bcrypt.checkpw(password.encode('utf-8'),
                          user.password.encode('utf-8')), "invalid credential"


@bp.route('/register', methods=['GET', 'POST'])
def register():
    """[summary] this endpoint accepts GET and POST request. 
    Given a GET request, this endpoint renders the register view. 
    Given a POST request, this endpoint creates a new user for manager app

    Returns:
        [type] -- [description] html view for registration view given GET request.
        json object given POST request
        {
            isSuccess: boolean indecating if a user is created successfully,
            url: url to login view given successful user creation,
            message: error message if applicable
        }
    """
    if request.method == 'GET':
        return render_template('register.html')
    try:

        username = request.form['username']
        password = request.form['password']

        assert username is not None, "Please enter username"
        assert password is not None, "Please enter password"

        result_name = r'^[A-Za-z0-9._-]{2,100}$'
        result_password = r'^.{6,}$'

        assert re.match(result_name, username, re.M | re.I)
        "Username should have 2 to 100 characters, and only contains letter, number, underline and dash."
        assert re.match(result_password, password)
        "Password should have 6 to 18 characters"

        password = password.encode('utf-8')

        user = manager.ManagerUserModel.query.filter_by(
            username=username).first()
        assert user is None, "Username exists"

        salt = bcrypt.gensalt()

        pw_hashed = bcrypt.hashpw(password, salt)

        new_user = manager.ManagerUserModel(
            username=username, password=pw_hashed)
        manager.db.session.add(new_user)
        manager.db.session.commit()

        return jsonify({
            'isSuccess': True,
            'url': url_for('auth.login')
        })

    except AssertionError as e:
        return jsonify({
            'isSuccess': False,
            'message': e.args
        })


@bp.route('/login', methods=['GET', 'POST'])
def login():
    """[summary] this endpoint accepts GET and POST requests.
    Given a GET request, this endpoint renders the login view.
    Given a POST request, this endpoint authenticates log in attempts. 

    Returns:
        [type] -- [description] this endpoint renders login view given a GET request.
        this endpoint return json object given POST request
        {
            isSuccess: boolean indecating if a user authentication is successful,
            url: url to dashboard view given successful user authentication,
            message: error message if applicable
        }
    """
    if request.method == 'GET':
        return render_template('login.html')

    try:

        username = request.form['username']
        password = request.form['password']

        authenticate(username, password)

        session.clear()
        session.permanent = True

        session['username'] = username

        return jsonify({
            'isSuccess': True,
            'url': url_for('dashboard')
        })

    except AssertionError as e:
        return jsonify({
            'isSuccess': False,
            'message': e.args
        })


@bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """[summary] this endpoint accepts a POST request and logs out an user

    Returns:
        [type] -- [description] html for login view
    """
    session.clear()
    return render_template('logint.html')
