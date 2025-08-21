#!/usr/bin/env bash
# Minimal build script - no Node.js dependencies
set -o errexit

echo "Starting minimal build process..."

# Upgrade pip
python -m pip install --upgrade pip

# Install minimal Python dependencies
echo "Installing minimal Python dependencies..."
pip install -r requirements-minimal.txt

# Create basic CSS if needed
mkdir -p static/css
if [ ! -f "static/css/output.css" ]; then
    echo "Creating basic CSS file..."
    echo "/* Basic styles */" > static/css/output.css
fi

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --no-input

# Run migrations
echo "Running database migrations..."
python manage.py migrate

echo "Minimal build completed successfully!"
