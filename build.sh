#!/usr/bin/env bash
# exit on error
set -o errexit

if [ -n "${DJANGO_SUPERUSER_USERNAME:-}" ] \
  || [ -n "${DJANGO_SUPERUSER_EMAIL:-}" ] \
  || [ -n "${DJANGO_SUPERUSER_PASSWORD:-}" ]; then
  if [ -z "${DJANGO_SUPERUSER_USERNAME:-}" ] \
    || [ -z "${DJANGO_SUPERUSER_EMAIL:-}" ] \
    || [ -z "${DJANGO_SUPERUSER_PASSWORD:-}" ]; then
    echo "Set DJANGO_SUPERUSER_USERNAME, DJANGO_SUPERUSER_EMAIL, and DJANGO_SUPERUSER_PASSWORD together." >&2
    exit 1
  fi
fi

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --noinput

# Run database migrations
python manage.py migrate

# Create the configured superuser once; existing accounts and setup errors are preserved.
if [ -n "${DJANGO_SUPERUSER_USERNAME:-}" ]; then
  python manage.py shell -c '
import os
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password

User = get_user_model()
username = os.environ["DJANGO_SUPERUSER_USERNAME"]
email = os.environ["DJANGO_SUPERUSER_EMAIL"]
password = os.environ["DJANGO_SUPERUSER_PASSWORD"]
user, created = User.objects.get_or_create(
    username=username,
    defaults={
        "email": email,
        "is_staff": True,
        "is_superuser": True,
        "password": make_password(password),
    },
)
if not (user.is_staff and user.is_superuser):
    raise RuntimeError(f"Configured username {username} already exists but is not a superuser.")
print(f"Created configured superuser {username}." if created else f"Configured superuser {username} already exists.")
'
fi
