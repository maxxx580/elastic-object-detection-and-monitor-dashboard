#!/bin/sh
{ 
    if [ ! -e "./venv" ]; then
        python3.7 -m venv venv
    fi
}

source venv/bin/activate
pip3 install -r setup/requirements.txt
gunicorn -w 1 -b 0.0.0.0:5001 run_manager:manager_app --timeout 120