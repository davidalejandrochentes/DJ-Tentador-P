#!/bin/sh

echo 'Running collecstatic...'
python manage.py collectstatic --no-input --settings=tentador.settings.production

echo 'Applying migrations...'
python manage.py wait_for_db --settings=tentador.settings.production
python manage.py migrate --settings=tentador.settings.production

echo 'Running server...'
gunicorn --env DJANGO_SETTINGS_MODULE=tentador.settings.production tentador.wsgi:application --bind 0.0.0.0:8000