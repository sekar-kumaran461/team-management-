#!/usr/bin/env bash
# exit on error
set -o errexit

echo "Starting build process..."

# Upgrade pip to latest version
echo "Upgrading pip..."
python -m pip install --upgrade pip

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Check if we're in a Node.js environment and package.json exists
if [ -f "package.json" ]; then
    echo "Node.js environment detected. Installing dependencies..."
    # Try to install Node.js dependencies
    if command -v npm >/dev/null 2>&1; then
        echo "Installing Node.js dependencies..."
        npm install
        echo "Building CSS with Tailwind..."
        npm run build
    else
        echo "npm not found, skipping Node.js build step..."
        # Create a basic output.css file if it doesn't exist
        mkdir -p static/css
        if [ ! -f "static/css/output.css" ]; then
            echo "Creating basic CSS file..."
            cp static/css/input.css static/css/output.css 2>/dev/null || echo "/* Basic CSS */" > static/css/output.css
        fi
    fi
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
