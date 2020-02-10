from flask import Blueprint, flash, g, redirect, session, render_template, request, url_for
from .user import login_required
from cvlib.object_detection import draw_bbox
from app.db import get_db, close_db
from werkzeug.exceptions import abort
from PIL import Image
import cv2
import cvlib as cv
import os
import numpy as np
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
        try:
            assert (len(name_parts) == 2)
        except Exception as e:
            print("image name has two dots in it")
            # return render_template('error.html')

        postfix = file.filename.split(".")[1]
        filename = username + "_" + timestamp + "." + postfix
        image_path = "/".join([target, filename])
        # save images to file "uploaded_images"
        file.save(image_path)
        # save image path to mysql
        saveImagePath(image_path, username, timestamp, "original")

        # generate the processed image
        processed_filename = username + "_" + timestamp + "_pro" + "." + postfix
        processed_path = "/".join([target, processed_filename])
        objectDetection(filename, processed_path)
        saveImagePath(processed_path, username, timestamp, "processed")

        # generate the thumbnail
        im_thumb = Image.open(image_path)
        # convert to thumbnail image
        im_thumb.thumbnail((128, 128), Image.ANTIALIAS)
        thumb_filename = username + "_" + timestamp + "_thumb" + "." + postfix
        thumb_path = "/".join([target, thumb_filename])
        im_thumb.save(thumb_path)
        saveImagePath(thumb_path, username, timestamp, "thumbnail")

    return render_template("image/showImage.html", user_image=filename, user_image_pro=processed_filename, user_image_thumb=thumb_filename)


def saveImagePath(location, username, currenttime, pictype):
    cnx = get_db()
    db_cursor = cnx.cursor()
    query = 'INSERT INTO Image (location, username, currenttime, pictype) VALUES (%s,%s,%s,%s)'
    db_cursor.execute(query, (location, username, currenttime, pictype))
    cnx.commit()
    close_db()

def objectDetection(file_name, image_path):
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
    readImagePath = os.path.join(APP_ROOT, "static/uploaded_images/"+file_name)
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

