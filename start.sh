#!/bin/sh
mysql -u root "-pMYD0622" ece1779 < app/setup.sql
. venv/bin/activate
pip install -r < requirements.txt
export FLASK_APP=app
export FLASK_ENV=development
flask run
