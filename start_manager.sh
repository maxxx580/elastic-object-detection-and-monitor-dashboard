#!/bin/sh
{ 
    if [ ! -e "./venv" ]; then
        python3.7 -m venv venv
    fi
}

source venv/bin/activate
pip3 install -r setup/requirements.txt
gunicorn -w 1 -b 127.0.0.1:5001 run_manager:manager_app