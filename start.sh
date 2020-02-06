#!/bin/sh
mysql -u root "-pMYD0622" ece1779 < app/setup.sql
. venv/bin/activate
pip install -r requirements.txt
gunicorn wsgi.py
