import bcrypt
from flask import Blueprint, flash, g, redirect, session, render_template, request, url_for, jsonify
from .user import login_required, authenticate

from werkzeug.exceptions import abort
from PIL import Image
import cv2
import os
import numpy as np
import time
import collections
import logging
import boto3
import app
import shutil


s3_client = boto3.client('s3')
bp = Blueprint("image", __name__)
BUCKET = "ece1779-a2-pic"

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
# derive the paths to the YOLO weights and model configuration
weightsPath = os.path.join(APP_ROOT, "yolo-coco/yolov3.weights")
configPath = os.path.join(APP_ROOT, "yolo-coco/yolov3.cfg")

# load our YOLO object detector trained on COCO dataset (80 classes)
print("[INFO] loading YOLO from disk...")
net = cv2.dnn.readNetFromDarknet(configPath, weightsPath)
ln = net.getLayerNames()
ln = [ln[i[0] - 1] for i in net.getUnconnectedOutLayers()]


@bp.route('/api/upload', methods=["POST"])
def upload():
    """[this endpoint authenticate user's credential and uploads one image for authenticated one with HTTP POST] 

    Returns:
        [JSON] -- [this endpoints return a json object indicates if upload succeeds ]
    """
    username = request.form["username"]
    password = request.form["password"]
    image = request.files.getlist("file")[0]
    try:

        authenticate(username, password)
        process_images(username, image)

        return jsonify({"success": True})

    except AssertionError as e:
        return jsonify({
            "success": False,
            "message": e.args
        })
    except Exception:
        abort(500)


@bp.route("/api/profile", methods=["GET", "POST"])
@login_required
def profile():
    """[this endpoint is secured for authenticated users. it uploads one image with HTTP POST,
    and returns updated profile view in HTML. This endpoint retrieves current profile view HTML with HTTP GET]

    Returns:
        [HTML] -- [this endpoint returns html for profile view upon successful uploading, otherwise error view]
    """
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
    # create a dictionary with timestamp as key and image_name as value
    dict_name = {}
    images_names = getFromdb(username, "thumbnail")
    for image in images_names:
        im_name = image.location.split(".")[0]
        dict_name[im_name.split("_")[1]] = image.location
    # sort dictionary by timestamp
    dict_name = collections.OrderedDict(
        sorted(dict_name.items(), reverse=True))

    result = dict_name.values()

    list_url = {}
    for each in result:
        list_url[each] = s3_client.generate_presigned_url('get_object',
                                                          Params={
                                                              'Bucket': BUCKET,
                                                              'Key': each,
                                                          },
                                                          ExpiresIn=3600)

    return render_template("image/profile.html", username=username, images_names=list_url)


@bp.route("/api/images", methods=["GET"])
@login_required
def images():
    """[this endopiont is secured for authenticated users and only takes HTTP GET. It retrieves an HTML view including 
    the original images and the processed image]

    Returns:
        [HTML] -- [a HTML view contains both the original image and the processed one.]
    """
    pass_name = request.args.get("pass_name")
    username = session.get("username")
    image_name_parts = pass_name.split(".")
    filename = image_name_parts[0][:-6] + "." + image_name_parts[1]
    processed_filename = image_name_parts[0][:-
                                             5] + "pro." + image_name_parts[1]

    image_url = s3_client.generate_presigned_url('get_object',
                                                 Params={
                                                     'Bucket': BUCKET,
                                                     'Key': filename,
                                                 },
                                                 ExpiresIn=3600)

    pro_image_url = s3_client.generate_presigned_url('get_object',
                                                     Params={
                                                         'Bucket': BUCKET,
                                                         'Key': processed_filename,
                                                     },
                                                     ExpiresIn=3600)

    return render_template("image/showImage.html", username=username, user_image=image_url,
                           user_image_pro=pro_image_url)


def process_images(username, image):
    extension = image.filename.split('.')[-1]
    assert extension in set(
        ["bmp", "pbm", "pgm", "ppm", "sr", "ras", "jpeg", "jpg", "jpe", "jp2", "tiff", "tif", "png"]), \
        "Unsupported format "

    target = os.path.join(APP_ROOT, 'static/uploaded_images')

    if not os.path.isdir(target):
        os.mkdir(target)

    timestamp = str(int(time.time()))
    filename = username + "_" + timestamp + "." + extension

    image_path = "/".join([target, filename])
    # save images to file "uploaded_images"
    image.save(image_path)

    # save images to s3 bucket
    # image.save(filename)
    # upload_image(f"{filename}", BUCKET)
    s3_client.upload_file(image_path, BUCKET, filename)
    # save image name to mysql
    saveImagePath(filename, username, timestamp, "original")

    # generate the processed image
    processed_filename = username + "_" + timestamp + "_pro" + "." + extension
    processed_path = "/".join([target, processed_filename])
    objectDetection(processed_path, image_path, processed_filename)
    saveImagePath(processed_filename, username, timestamp, "processed")

    # generate the thumbnail image
    im_thumb = Image.open(processed_path)
    im_thumb.thumbnail((256, 256), Image.ANTIALIAS)
    thumb_filename = username + "_" + timestamp + "_thumb" + "." + extension
    thumb_path = "/".join([target, thumb_filename])
    im_thumb.save(thumb_path)
    s3_client.upload_file(thumb_path, BUCKET, thumb_filename)
    saveImagePath(thumb_filename, username, timestamp, "thumbnail")

    # os.remove(image_path)
    # os.remove(processed_path)
    # os.remove(thumb_path)
    shutil.rmtree(target)


def saveImagePath(location, username, currenttime, pictype):
    # cnx = get_db()
    # db_cursor = cnx.cursor()
    # query = 'INSERT INTO Image (location, username, currenttime, pictype) VALUES (%s,%s,%s,%s)'

    new_image = app.ImageModel(
        location=location, username=username, currenttime=currenttime, pictype=pictype)
    app.db.session.add(new_image)
    app.db.session.commit()



def getFromdb(username, pictype):


    lst_path = list(app.ImageModel.query.filter_by(
        username=username, pictype=pictype).all())

    # lst_path = []
    # for row in result:
    #     path = str(row)[2:-3]
    #     print("image path: " + path)
    #     lst_path.append(path)
    # # cnx.commit()
    # # close_db()
    # list_path=result
    return lst_path


def objectDetection(processed_path, image_path, store_name):
    # load the COCO class labels our YOLO model was trained on
    labelsPath = os.path.join(APP_ROOT, 'yolo-coco/coco.names')
    # labelsPath = os.path.sep.join(["yolo-coco", "coco.names"])
    LABELS = open(labelsPath).read().strip().split("\n")

    # initialize a list of colors to represent each possible class label
    np.random.seed(42)
    COLORS = np.random.randint(0, 255, size=(len(LABELS), 3),
                               dtype="uint8")

    # load our input image and grab its spatial dimensions
    image = cv2.imread(image_path)
    (H, W) = image.shape[:2]

    # determine only the *output* layer names that we need from YOLO
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

    # save the output image
    cv2.imwrite(processed_path, image)
    s3_client.upload_file(processed_path, BUCKET, store_name)


# def download_image(file_name, bucket):
#     """
#     Function to download a given file from an S3 bucket
#     """
#     s3 = boto3.resource('s3')
#     output = f"downloads/{file_name}"
#     s3.Bucket(bucket).download_file(file_name, output)
#
#     return output

#
# def list_files(bucket):
#     """
#     Function to list files in a given S3 bucket
#     """
#     s3 = boto3.client('s3')
#     contents = []
#     try:
#         for item in s3.list_objects(Bucket=bucket)['Contents']:
#             print(item)
#             contents.append(item)
#     except Exception as e:
#         pass
#
#     return contents
