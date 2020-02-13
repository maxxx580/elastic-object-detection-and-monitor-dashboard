#!/bin/sh
mysql -u root "-ppassword" < setup.sql
mkdir -p app/static
mkdir -p app/static/uploaded_images
. venv/bin/activate
pip3 install -r requirements.txt
gunicorn -w 3 -b 127.0.0.1:5000 wsgi:webapp