#!/bin/sh
mysql -u root "-pMYD0622" ece1779 < app/setup.sql
. venv/bin/activate
pip install -r requirements.txt
gunicorn -w 4 -b 127.0.0.1:4000 wsgi:webapp
