#!/bin/sh
set -e
python manage.py migrate --noinput
if [ -n "$ADMIN_USERNAME" ] && [ -n "$ADMIN_EMAIL" ] && [ -n "$ADMIN_PASSWORD" ]; then
  python manage.py createadmin "$ADMIN_USERNAME" "$ADMIN_EMAIL" "$ADMIN_PASSWORD" "${ADMIN_NAME:-Administrateur}"
fi
exec gunicorn eni_mail.wsgi:application --bind 0.0.0.0:${PORT:-10000} --workers ${WEB_CONCURRENCY:-1} --threads 4 --timeout 60
