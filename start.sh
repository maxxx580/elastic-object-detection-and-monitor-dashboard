#!/bin/sh
mysql -u root "-pece1779pass" < app/setup.sql
. venv/bin/activate
pip3 install -r requirements.txt
gunicorn -w 4 -b 127.0.0.1:8000 wsgi:webapp
