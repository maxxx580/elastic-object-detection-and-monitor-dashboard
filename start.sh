#!/bin/sh
sudo mysql -u root "-pece1779pass" ece1779 < app/setup.sql
. venv/bin/activate
sudo pip install -r requirements.txt
gunicorn -w 4 -b 127.0.0.1:80 wsgi:webapp
