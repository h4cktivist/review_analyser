#!/bin/sh
set -e

case "$1" in
  celery)
    echo "Starting Celery worker..."
    exec celery -A review_analyser worker -l info -P gevent
    ;;
  *)
    echo "Applying migrations..."
    python manage.py migrate --noinput
    echo "Starting Django server..."
    exec python manage.py runserver 0.0.0.0:8000
    ;;
esac
