#!/bin/sh
set -e

echo "Waiting for PostgreSQL to be ready..."
python - <<'EOF'
import os
import socket
import sys
import time

host = os.environ.get('DB_HOST', 'db')
port = int(os.environ.get('DB_PORT', '5432'))

for _ in range(60):
    try:
        socket.create_connection((host, port), timeout=2).close()
        print("PostgreSQL is up.")
        break
    except OSError:
        time.sleep(1)
else:
    sys.exit("ERROR: could not connect to PostgreSQL after 60s")
EOF

echo "Applying database migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting Gunicorn..."
exec gunicorn xeax_sports_project.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers "${GUNICORN_WORKERS:-3}" \
    --timeout 120
