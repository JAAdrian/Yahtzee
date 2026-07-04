#!/bin/sh
set -e

cd /app

# Apply database migrations on every start so SQLite stays up-to-date.
echo "Running database migrations..."
python manage.py migrate --noinput

echo "Starting Gunicorn..."
exec gunicorn yahtzee_tracker.wsgi:application --bind 0.0.0.0:8000 --workers 2
