#!/bin/sh
set -e

cd /app

# Collect static files and apply database migrations on every start.
echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Running database migrations..."
python manage.py migrate --noinput

echo "Starting Gunicorn..."
exec gunicorn yahtzee_tracker.wsgi:application --bind 0.0.0.0:8000 --workers 2 --worker-tmp-dir /dev/shm
