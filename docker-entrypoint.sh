#!/bin/sh
set -e

python - <<'PYEOF'
import os
import socket
import time

host = os.environ.get('POSTGRES_HOST', 'db')
port = int(os.environ.get('POSTGRES_PORT', '5432'))

for _ in range(60):
    try:
        with socket.create_connection((host, port), timeout=2):
            break
    except OSError:
        time.sleep(1)
else:
    raise SystemExit(f'Timed out waiting for database at {host}:{port}')
PYEOF

python manage.py migrate --noinput
python manage.py collectstatic --noinput

python - <<'PYEOF'
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from accounts.models import User

username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')

if not password:
    print('DJANGO_SUPERUSER_PASSWORD not set, skipping admin bootstrap.')
elif User.objects.filter(username=username).exists():
    print(f'Superuser "{username}" already exists, skipping.')
else:
    User.objects.create_superuser(
        username=username,
        email=os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@example.com'),
        password=password,
        nickname=os.environ.get('DJANGO_SUPERUSER_NICKNAME', username),
    )
    print(f'Created superuser "{username}".')
PYEOF

exec "$@"
