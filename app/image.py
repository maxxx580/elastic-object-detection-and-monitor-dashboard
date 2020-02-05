from flask import Blueprint
from flask import flash
from flask import g
from flask import redirect
from flask import render_template
from flask import request
import os
import calendar
import time
from datetime import datetime
from app.db import get_db, close_db
from flask import url_for
from werkzeug.exceptions import abort

bp = Blueprint("image", __name__, url_prefix='/image')

@bp.route("/")
def index():
    return render_template('image/uploadImage.html')

# bp.config["IMAGE_UPLOADS"] = "/Users/wangran/Desktop/pic"
APP_ROOT = os.path.dirname(os.path.abspath(__file__))

@bp.route("/uploadImages", methods=["GET", "POST"])
def upload_images():

    if request.method == "POST":
        if request.files:
            image = request.files["image"]
            print(image)
            # image.save(os.path.join(bp.config["IMAGE_UPLOADS"], image.filename))

            print("image saved")
            return redirect(request.url)

    return render_template("image/uploadImage.html")


@bp.route("/uploadImage", methods=["GET", "POST"])
def upload_image():
    target = os.path.join(APP_ROOT, 'uploaded_images')
    print("!!!!!target"+target)
    # how to fetch username
    username = "eric"
    # timestamp = calendar.timegm(time.gmtime())
    ts = time.time()
    timestamp = str(int(ts))
    # timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print("!!!!!timestamp"+timestamp)
    # timestamp = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

    if not os.path.isdir(target):
        os.mkdir(target)
    for file in request.files.getlist("image"):
        print(file)
        # filename should use username_timestamp
        filename = file.filename
        destination = "/".join([target, filename])
        print("!!!!!location"+destination)
        file.save(destination)

    cnx = get_db()
    db_cursor = cnx.cursor()
    query = 'INSERT INTO image (location, username, current_time) VALUES (%s,%s,%s)'
    # db_cursor.execute(query, (destination, username, timestamp))

    cnx.commit()
    close_db()

    return render_template("image/showImage.html")



















