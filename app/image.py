from flask import Blueprint, flash, g, redirect, session, render_template, request, url_for
from .user import login_required
from cvlib.object_detection import draw_bbox
from app.db import get_db, close_db
from werkzeug.exceptions import abort
from PIL import Image
import cv2
import cvlib as cv
import os
import time

bp = Blueprint("image", __name__, url_prefix='/image')


@bp.route("/")
@login_required
def index():
    return render_template('image/uploadImage.html')


APP_ROOT = os.path.dirname(os.path.abspath(__file__))


@bp.route("/uploadImage", methods=["GET", "POST"])
@login_required
def upload_image():
    target = os.path.join(APP_ROOT, 'static/uploaded_images')
    username = session.get("username")
    timestamp = str(int(time.time()))
    image_path = ""

    try:
        assert (username != "")
    except Exception as e:
        # return render_template('error.html')
        print("username is null")

    if not os.path.isdir(target):
        os.mkdir(target)
    for file in request.files.getlist("image"):
        # filename should use username_timestamp
        name_parts = file.filename.split(".")
        postfix = file.filename.split(".")[1]
        filename = username + "_" + timestamp + "." + postfix
        image_path = "/".join([target, filename])

        try:
            assert (len(name_parts) == 2)
        except Exception as e:
            print("image name has two dots in it")
            # return render_template('error.html')

        # generate the processed image
        im = cv2.imread(image_path)
        bbox, label, conf = cv.detect_common_objects(im)
        output_image = draw_bbox(im, bbox, label, conf)
        processed_filename = username + "_" + timestamp + "_pro" + "." + postfix
        processed_path = "/".join([target, processed_filename])

        # generate the thumbnail
        im_thumb = Image.open(image_path)
        # convert to thumbnail image
        im_thumb.thumbnail((128, 128), Image.ANTIALIAS)
        thumb_filename = username + "_" + timestamp + "_thumb" + "." + postfix
        thumb_path = "/".join([target, thumb_filename])

        # save images to file "uploaded_images"
        file.save(image_path)
        output_image.save(processed_path)
        im_thumb.save(thumb_path)

    # save image path to mysql
    saveImagePath(image_path, username, timestamp, "original")
    saveImagePath(processed_path, username, timestamp, "processed")
    saveImagePath(thumb_path, username, timestamp, "thumbnail")

    # query_original = 'INSERT INTO image (location, username, currenttime, pictype) VALUES (%s,%s,%s, %s)'
    # db_cursor.execute(query_original, (image_path, username, timestamp, "original"))
    # query_processed = 'INSERT INTO image (location, username, currenttime, pictype) VALUES (%s,%s,%s, %s)'
    # db_cursor.execute(query_processed, (processed_path, username, timestamp, "processed"))

    return render_template("image/showImage.html", user_image=filename, user_image_pro=processed_filename, user_image_thumb=thumb_filename)


def saveImagePath(location, username, currenttime, pictype):
    cnx = get_db()
    db_cursor = cnx.cursor()
    query = 'INSERT INTO image (location, username, currenttime, pictype) VALUES (%s,%s,%s,%s)'
    db_cursor.execute(query, (location, username, currenttime, pictype))
    cnx.commit()
    close_db()
    return 0
