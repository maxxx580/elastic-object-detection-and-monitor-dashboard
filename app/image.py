from flask import Blueprint
from flask import flash
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from werkzeug.exceptions import abort

bp = Blueprint("image", __name__, url_prefix='/image')

@bp.route("/")
def index():
    return render_template('image/index.html')
