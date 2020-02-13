#!/bin/sh
mysql -u root "-ppassword" < setup/setup.sql
mkdir -p app/static
mkdir -p app/static/uploaded_images
{
    if [ ! -f /app/yolo-coco/yolov3.weights ]; then
    echo "yolov3.weights exits"
    else
        bash setup/download.sh
    fi
}
. venv/bin/activate
pip3 install .
gunicorn -w 3 -b 127.0.0.1:5000 wsgi:webapp --timeout 90 --graceful-timeout 60
