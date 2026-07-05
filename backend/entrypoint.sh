#!/bin/bash
set -e

echo "Waiting for PostgreSQL..."
while ! python -c "import socket; socket.create_connection(('${DB_HOST:-db}', ${DB_PORT:-5432}), timeout=1)" 2>/dev/null; do
  sleep 1
done
echo "PostgreSQL ready!"

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput 2>/dev/null || true

exec "$@"
