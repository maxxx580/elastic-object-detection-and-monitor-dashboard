#!/bin/sh
mysql -u root "-ppassword" < app/setup.sql
mkdir app/static
mkdir app/static/uploaded_images
. venv/bin/activate
pip3 install -r requirements.txt
gunicorn -w 3 -b 127.0.0.1:5000 wsgi:webapp