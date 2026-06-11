#!/usr/bin/env bash
set -o errexit
pip install -r requirements.txt
python manage.py migrate --run-syncdb
python manage.py collectstatic --no-input