#!/bin/sh
mysql -u root "-pece1779pass" < setup/setup.sql
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
