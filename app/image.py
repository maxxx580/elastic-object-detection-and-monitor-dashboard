import bcrypt
from flask import Blueprint, flash, g, redirect, session, render_template, request, url_for, jsonify
from .user import login_required
from app.db import get_db, close_db
from werkzeug.exceptions import abort
from PIL import Image
import cv2
import os
import numpy as np
import time
import collections

bp = Blueprint("image", __name__)

APP_ROOT = os.path.dirname(os.path.abspath(__file__))


@bp.route('/api/upload', methods=["POST"])
def upload():
    username = request.form["username"]
    password = request.form["password"]
    image = request.files.getlist("file")[0]
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

        process_images(username, image)
    except AssertionError as e:
        return jsonify({
            "success": False,
            "message": e.args
        })
    return jsonify({"success": True})


@bp.route("/api/profile", methods=["GET", "POST"])
@login_required
def profile():
    username = session.get("username")
    try:
        assert username != ""
    except AssertionError:
        abort(403)

    if request.files.getlist("file"):
        for file in request.files.getlist("file"):
            # filename should use username_timestamp
            try:
                process_images(username, file)
            except AssertionError:
                abort(400)

    # order by timestamp
    images_names = []
    # create a dictionary with image_name as key and timestamp as value
    dict_name = {}
    username = session.get("username")
    images_path = getFromDatabase(username, "thumbnail")
    for image_path in images_path:
        path_parts = image_path.split("/")
        images_names.append(path_parts[-1])
    for i in range(len(images_names)):
        im_name = images_names[i].split(".")[0]
        dict_name[im_name.split("_")[1]] = images_names[i]
    # sort dictionary by timestamp
    dict_name = collections.OrderedDict(
        sorted(dict_name.items(), reverse=True))

    result = dict_name.values()

    return render_template("image/profile.html", username=username, images_names=result)


@bp.route("/api/images", methods=["GET"])
@login_required
def gallery():
    pass_name = request.args.get("pass_name")
    username = session.get("username")
    image_name_parts = pass_name.split(".")
    filename = image_name_parts[0][:-6] + "." + image_name_parts[1]
    processed_filename = image_name_parts[0][:-
                                             5] + "pro." + image_name_parts[1]

    return render_template("image/showImage.html", username=username, user_image=filename,
                           user_image_pro=processed_filename)


def process_images(username, image):
    extension = image.filename.split('.')[-1]

    assert extension in set(
        ["bmp", "pbm", "pgm", "ppm", "sr", "ras", "jpeg", "jpg", "jpe", "jp2", "tiff", "tif", "png"]),\
        "Unsupported formmat "

    target = os.path.join(APP_ROOT, 'static/uploaded_images/' + username)

    if not os.path.isdir(target):
        os.mkdir(target)

    timestamp = str(int(time.time()))
    filename = username + "_" + timestamp + "." + extension
    image_path = "/".join([target, filename])
    # save images to file "uploaded_images"
    image.save(image_path)
    # save image path to mysql
    saveImagePath(image_path, username, timestamp, "original")

    # generate the processed image
    processed_filename = username + "_" + timestamp + "_pro" + "." + extension
    processed_path = "/".join([target, processed_filename])
    objectDetection(filename, processed_path, username)
    saveImagePath(processed_path, username, timestamp, "processed")

    # generate the thumbnail
    im_thumb = Image.open(processed_path)
    # convert to thumbnail image
    im_thumb.thumbnail((256, 256), Image.ANTIALIAS)
    thumb_filename = username + "_" + timestamp + "_thumb" + "." + extension
    thumb_path = "/".join([target, thumb_filename])
    im_thumb.save(thumb_path)
    saveImagePath(thumb_path, username, timestamp, "thumbnail")


def saveImagePath(location, username, currenttime, pictype):
    cnx = get_db()
    db_cursor = cnx.cursor()
    query = 'INSERT INTO Image (location, username, currenttime, pictype) VALUES (%s,%s,%s,%s)'
    db_cursor.execute(query, (location, username, currenttime, pictype))
    cnx.commit()
    close_db()


def getFromDatabase(username, pictype):
    cnx = get_db()
    db_cursor = cnx.cursor()
    query = "SELECT location FROM Image WHERE username='" + \
        username + "' AND pictype='" + pictype + "'"
    db_cursor.execute(query)
    result = db_cursor.fetchall()
    lst_path = []
    for row in result:
        path = str(row)[2:-3]
        print("image path: " + path)
        lst_path.append(path)
    cnx.commit()
    close_db()
    return lst_path


def objectDetection(file_name, image_path, username):
    # load the COCO class labels our YOLO model was trained on
    labelsPath = os.path.join(APP_ROOT, 'yolo-coco/coco.names')
    # labelsPath = os.path.sep.join(["yolo-coco", "coco.names"])
    LABELS = open(labelsPath).read().strip().split("\n")

    # initialize a list of colors to represent each possible class label
    np.random.seed(42)
    COLORS = np.random.randint(0, 255, size=(len(LABELS), 3),
                               dtype="uint8")

    # derive the paths to the YOLO weights and model configuration
    weightsPath = os.path.join(APP_ROOT, "yolo-coco/yolov3.weights")
    configPath = os.path.join(APP_ROOT, "yolo-coco/yolov3.cfg")

    # load our YOLO object detector trained on COCO dataset (80 classes)
    print("[INFO] loading YOLO from disk...")
    net = cv2.dnn.readNetFromDarknet(configPath, weightsPath)

    # load our input image and grab its spatial dimensions
    readImagePath = os.path.join(
        APP_ROOT, "static/uploaded_images/" + username + "/" + file_name)
    image = cv2.imread(readImagePath)
    (H, W) = image.shape[:2]

    # determine only the *output* layer names that we need from YOLO
    ln = net.getLayerNames()
    ln = [ln[i[0] - 1] for i in net.getUnconnectedOutLayers()]

    # construct a blob from the input image and then perform a forward
    # pass of the YOLO object detector, giving us our bounding boxes and
    # associated probabilities
    blob = cv2.dnn.blobFromImage(image, 1 / 255.0, (416, 416),
                                 swapRB=True, crop=False)
    net.setInput(blob)
    start = time.time()
    layerOutputs = net.forward(ln)
    end = time.time()

    # show timing information on YOLO
    print("[INFO] YOLO took {:.6f} seconds".format(end - start))

    # initialize our lists of detected bounding boxes, confidences, and
    # class IDs, respectively
    boxes = []
    confidences = []
    classIDs = []

    # loop over each of the layer outputs
    for output in layerOutputs:
        # loop over each of the detections
        for detection in output:
            # extract the class ID and confidence (i.e., probability) of
            # the current object detection
            scores = detection[5:]
            classID = np.argmax(scores)
            confidence = scores[classID]

            # filter out weak predictions by ensuring the detected
            # probability is greater than the minimum probability
            if confidence > 0.5:
                # scale the bounding box coordinates back relative to the
                # size of the image, keeping in mind that YOLO actually
                # returns the center (x, y)-coordinates of the bounding
                # box followed by the boxes' width and height
                box = detection[0:4] * np.array([W, H, W, H])
                (centerX, centerY, width, height) = box.astype("int")

                # use the center (x, y)-coordinates to derive the top and
                # and left corner of the bounding box
                x = int(centerX - (width / 2))
                y = int(centerY - (height / 2))

                # update our list of bounding box coordinates, confidences,
                # and class IDs
                boxes.append([x, y, int(width), int(height)])
                confidences.append(float(confidence))
                classIDs.append(classID)

    # apply non-maxima suppression to suppress weak, overlapping bounding
    # boxes
    idxs = cv2.dnn.NMSBoxes(boxes, confidences, 0.5,
                            0.3)

    # ensure at least one detection exists
    if len(idxs) > 0:
        # loop over the indexes we are keeping
        for i in idxs.flatten():
            # extract the bounding box coordinates
            (x, y) = (boxes[i][0], boxes[i][1])
            (w, h) = (boxes[i][2], boxes[i][3])

            # draw a bounding box rectangle and label on the image
            color = [int(c) for c in COLORS[classIDs[i]]]
            cv2.rectangle(image, (x, y), (x + w, y + h), color, 2)
            text = "{}: {:.4f}".format(LABELS[classIDs[i]], confidences[i])
            cv2.putText(image, text, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX,
                        0.5, color, 2)

    # show the output image
    cv2.imwrite(image_path, image)
