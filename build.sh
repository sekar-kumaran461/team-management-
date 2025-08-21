#!/usr/bin/env bash
# exit on error
set -o errexit

echo "Starting build process..."

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Install Node.js dependencies and build CSS
echo "Installing Node.js dependencies and building CSS..."
npm install
npm run build

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --no-input

# Run migrations
echo "Running database migrations..."
python manage.py migrate

echo "Build process completed successfully!"
