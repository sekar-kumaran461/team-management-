web: python -m gunicorn team_management.wsgi:application --bind 0.0.0.0:$PORT --workers 1 --timeout 120
release: python manage.py migrate
