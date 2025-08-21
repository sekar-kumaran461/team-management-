#!/usr/bin/env bash
# SQLite fallback build - bypass PostgreSQL issues temporarily
set -o errexit

echo "=== SQLITE FALLBACK BUILD ==="

# Install packages without PostgreSQL adapter
echo "Installing core packages..."
pip install Django==4.2.7
pip install gunicorn==20.1.0  
pip install whitenoise==6.5.0
pip install python-decouple==3.8

echo "Skipping psycopg2 - using SQLite for initial deployment..."

# Create directories
mkdir -p static/css static/js logs media

# Create basic CSS
echo "/* Basic CSS */" > static/css/output.css

# Use SQLite for now (will connect to Supabase later)
echo "Collecting static files..."
python manage.py collectstatic --no-input --clear

echo "Creating SQLite database..."
python manage.py migrate

echo "=== SQLITE BUILD COMPLETE ==="
echo "Note: Using SQLite temporarily. Add PostgreSQL adapter later."
