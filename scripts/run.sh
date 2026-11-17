#!/bin/sh

# Force the script to stop if any command fails
set -e

# Command to start the server
python manage.py wait_for_db
python manage.py collectstatic --noinput
python manage.py migrate

# Start the WebService Gateway Interface
uwsgi --socket :9000 \
      --workers 4 \
      --master \
      --enable-threads \
      --module app.wsgi

