#!/usr/bin/env bash
# SQLite fallback build script - avoid PostgreSQL issues
set -o errexit

echo "=== SQLITE FALLBACK BUILD ==="

# Upgrade pip
python -m pip install --upgrade pip

# Install only packages that definitely work with Python 3.13
echo "Installing core Django packages..."
pip install Django==4.2.7
pip install gunicorn==20.1.0
pip install whitenoise==6.5.0
pip install python-decouple==3.8

# Skip PostgreSQL adapter completely for now
echo "Skipping PostgreSQL adapter - using SQLite fallback..."

# Create necessary directories
mkdir -p static/css static/js logs media

# Create basic CSS
echo "/* Basic CSS */" > static/css/output.css

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --no-input

# Run migrations with SQLite
echo "Running migrations with SQLite..."
python manage.py migrate

echo "=== SQLITE BUILD COMPLETE ==="
