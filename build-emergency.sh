#!/usr/bin/env bash
# Emergency deployment script - absolute minimal setup
set -o errexit

echo "=== EMERGENCY DEPLOYMENT SCRIPT ==="

# Force Python version
export PYTHON_VERSION=3.11.6

# Upgrade pip first
echo "Upgrading pip..."
python3.11 -m pip install --upgrade pip || python -m pip install --upgrade pip

# Install only essential packages one by one to catch errors
echo "Installing Django..."
pip install Django==4.2.7

echo "Installing gunicorn..."
pip install gunicorn==20.1.0

echo "Installing whitenoise..."
pip install whitenoise==6.5.0

echo "Installing database adapter..."
pip install psycopg2-binary==2.9.6

echo "Installing decouple..."
pip install python-decouple==3.8

echo "Installing dj-database-url..."
pip install dj-database-url==2.1.0

# Skip CSS build entirely
echo "Skipping CSS build..."

# Create minimal static directories
mkdir -p static/css
echo "/* Minimal CSS */" > static/css/output.css

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --no-input --clear

# Run migrations
echo "Running migrations..."
python manage.py migrate

echo "=== EMERGENCY DEPLOYMENT COMPLETE ==="
