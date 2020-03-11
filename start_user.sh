#!/bin/sh
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
gunicorn -w 1 -b 0.0.0.0:5000 run_user:user_app --timeout 90
