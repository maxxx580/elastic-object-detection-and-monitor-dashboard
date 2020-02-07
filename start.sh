#!/bin/sh
mysql -u root "-ppassword" ece1779 < app/setup.sql
. venv/bin/activate
# pip install -r requirements.txt
pip install .
gunicorn -w 4 -b 127.0.0.1:4000 wsgi:webapp
