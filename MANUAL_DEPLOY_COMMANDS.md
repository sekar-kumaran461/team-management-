# Manual Build Commands for Render Dashboard

## Option 1: Pre-built wheels only
```bash
pip install --only-binary=all Django==4.2.7 gunicorn==20.1.0 whitenoise==6.5.0 python-decouple==3.8 dj-database-url==2.1.0 && mkdir -p static/css && echo "/* CSS */" > static/css/output.css && python manage.py collectstatic --no-input && python manage.py migrate
```

## Option 2: Without psycopg2 (use Django's db fallback)
```bash
pip install Django==4.2.7 gunicorn==20.1.0 whitenoise==6.5.0 python-decouple==3.8 && mkdir -p static/css && echo "/* CSS */" > static/css/output.css && python manage.py collectstatic --no-input
```

## Option 3: Force specific Python version
```bash
python3.11 -m pip install Django==4.2.7 gunicorn==20.1.0 whitenoise==6.5.0 python-decouple==3.8 dj-database-url==2.1.0 && python3.11 manage.py collectstatic --no-input && python3.11 manage.py migrate
```

## Start Command
```bash
gunicorn team_management.wsgi:application --bind 0.0.0.0:$PORT
```

## Environment Variables (Essential)
```
DEBUG=False
SECRET_KEY=[AUTO-GENERATE]
ALLOWED_HOSTS=*
DATABASE_URL=postgresql://postgres.xvwwawadfeqnrwmozeai:Vif2025team$@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres
```
