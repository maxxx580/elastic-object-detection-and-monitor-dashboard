#!/bin/sh
mysql -u root "-ppassword" < app/setup.sql
. venv/bin/activate
pip3 install -r requirements.txt
gunicorn -w 12 -b 127.0.0.1:8000 wsgi:webapp