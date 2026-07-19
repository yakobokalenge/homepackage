#!/bin/bash
set -e

echo "Waiting for PostgreSQL..."
python -c "
import os, socket, time
from urllib.parse import urlparse

db_url = os.environ.get('DATABASE_URL')
host = os.environ.get('DB_HOST', 'db')
port = int(os.environ.get('DB_PORT', 5432))

if db_url:
    url = urlparse(db_url)
    host = url.hostname or host
    port = url.port or port

print(f'Attempting to connect to {host}:{port}...')

while True:
    try:
        socket.create_connection((host, port), timeout=1)
        break
    except OSError:
        time.sleep(1)
"

echo "PostgreSQL ready!"

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput 2>/dev/null || true

exec "$@"
