import os
from datetime import timedelta


basedir = os.path.abspath(os.path.dirname(__file__))


def get_instanceId():
    return os.popen('ec2metadata --instance-id').read().strip()


class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'ece1779-a2-secretkey'
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://admin:password@ece1779test.cb9p4b3u80au.us-east-1.rds.amazonaws.com:3306/ece1779test'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = basedir + '/static/uploaded_images'
    ALLOWED_EXTENSIONS = ["bmp", "pbm", "pgm", "ppm", "sr",
                          "ras", "jpeg", "jpg", "jpe", "jp2", "tiff", "tif", "png"]

    BUCKET_NAME = 'ece1779-a2-images'
    # INSTANCE_ID = get_instanceId()
    ZONE = 'us-east-1c'
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=60 * 24)
