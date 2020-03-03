#!/bin/sh
mkdir -p app/static
mkdir -p app/static/uploaded_images
{
    if [ ! -e "./app/yolo-coco/yolov3.weights" ]; then
        bash setup/download.sh        
    fi
}

{
    if [ ! -e "./venv" ]; then
        python3.7 -m venv venv
    fi
}

source venv/bin/activate
pip3 install -r setup/requirements.txt
gunicorn -w 1 -b 127.0.0.1:5000 run_user:user_app
