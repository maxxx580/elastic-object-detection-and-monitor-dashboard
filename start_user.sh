#!/bin/sh
#mysql -u root "-ppassword" < setup/setup.sql

#mysql -h ece1779test.cb9p4b3u80au.us-east-1.rds.amazonaws.com -P 3306 -u admin -p

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
pip3 install -r setup/requirements.txt
gunicorn -w 1 -b 127.0.0.1:5000 run_user:user_app --timeout 90 --graceful-timeout 60
