#!/bin/sh
mysql -u root "-ppassword" ece1779 < app/setup.sql
. venv/bin/activate
pip install -r < requirements.txt
export FLASK_APP=app
export FLASK_ENV=development
flask run
