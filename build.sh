#!/usr/bin/env bash
# exit on error
set -o errexit

echo "Starting build process..."

# Upgrade pip to latest version
echo "Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Install Node.js dependencies and build CSS (if package.json exists)
if [ -f "package.json" ]; then
    echo "Installing Node.js dependencies and building CSS..."
    npm install
    npm run build
else
    echo "No package.json found, skipping Node.js build..."
fi

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --no-input

# Run migrations
echo "Running database migrations..."
python manage.py migrate

echo "Build process completed successfully!"
