from flask import render_template, request, Flask
app = Flask(__name__)
from flask import json
from werkzeug.exceptions import HTTPException

@app.errorhandler(404)
def page_not_found(e):
    """Return JSON instead of HTML for HTTP errors."""
    # start with the correct headers and status code from the error
    response = e.get_response()
    # replace the body with JSON
    response.data = json.dumps({
        "code": e.code,
        "name": e.name,
        "description": e.description,
    })
    response.content_type = "application/json"
    return response
    # return render_template('error.html'), 404

@app.errorhandler(403)
def forbidden(e):
    return render_template('error.html'), 403

@app.errorhandler(401)
def unauthorized(e):
    return render_template('error.html'), 401

@app.errorhandler(500)
def server_error(e):
    response = e.get_response()
    # replace the body with JSON
    response.data = json.dumps({
        "code": e.code,
        "name": e.name,
        "description": e.description,
    })
    response.content_type = "application/json"
    return response

