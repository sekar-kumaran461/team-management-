#!/usr/bin/env bash
# Emergency deployment script - absolute minimal setup
set -o errexit

echo "=== EMERGENCY DEPLOYMENT SCRIPT ==="

# Force Python version and upgrade pip
echo "Setting up Python environment..."
python -m pip install --upgrade pip

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

# Skip problematic packages for now
echo "Skipping dj-database-url to avoid parsing issues..."

# Skip CSS build entirely
echo "Skipping CSS build..."

# Create minimal static directories and files
mkdir -p static/css static/js static/admin
echo "/* Minimal CSS */" > static/css/output.css

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --no-input --clear

# Run migrations
echo "Running migrations..."
python manage.py migrate

echo "=== EMERGENCY DEPLOYMENT COMPLETE ==="
