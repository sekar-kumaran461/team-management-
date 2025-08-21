#!/bin/bash

# Build script for Django Team Management Application
# Handles deployment to Render with fallback strategies

set -o errexit  # Exit on any error

echo "🚀 Starting Django Team Management build process..."
echo "Build timestamp: $(date)"

# Create necessary directories
echo "📁 Creating required directories..."
mkdir -p logs
mkdir -p media/submissions
mkdir -p media/task_submissions
mkdir -p static
mkdir -p staticfiles

# Set directory permissions
chmod 755 logs media static staticfiles

echo "✅ Directories created successfully"

# Upgrade pip first
echo "📦 Upgrading pip..."
python -m pip install --upgrade pip

# Check Python version
echo "🐍 Python version:"
python --version

# Try to install dependencies with fallback strategy
echo "📦 Installing dependencies..."

# First try with full requirements (including PostgreSQL)
if pip install -r requirements.txt; then
    echo "✅ Full requirements installed successfully"
    DB_TYPE="postgresql"
else
    echo "⚠️  Full requirements failed, trying SQLite fallback..."
    
    # Install minimal requirements for SQLite
    if pip install Django==4.2.7 gunicorn==20.1.0 whitenoise==6.5.0 python-decouple==3.8 dj-database-url==2.1.0; then
        echo "✅ SQLite requirements installed successfully"
        DB_TYPE="sqlite"
    else
        echo "❌ Even minimal requirements failed"
        exit 1
    fi
fi

# Verify gunicorn installation
echo "🔍 Verifying gunicorn installation..."
if command -v gunicorn &> /dev/null; then
    echo "✅ Gunicorn is available"
    gunicorn --version
else
    echo "⚠️  Gunicorn not found in PATH, installing explicitly..."
    pip install gunicorn==20.1.0
    # Add Python user bin to PATH
    export PATH="$HOME/.local/bin:$PATH"
    export PATH="/opt/render/project/src/.venv/bin:$PATH"
fi

# Final verification
echo "🔍 Final gunicorn check..."
which gunicorn || echo "Gunicorn location not found"
python -c "import gunicorn; print(f'Gunicorn version: {gunicorn.__version__}')" || echo "Gunicorn import failed"

# Collect static files
echo "🎨 Collecting static files..."
python manage.py collectstatic --noinput --clear

# Apply database migrations
echo "🗄️  Applying database migrations..."
if [ "$DB_TYPE" = "postgresql" ]; then
    echo "Using PostgreSQL database"
    python manage.py migrate
elif [ "$DB_TYPE" = "sqlite" ]; then
    echo "Using SQLite database"
    python manage.py migrate
else
    echo "Unknown database type, attempting migration anyway..."
    python manage.py migrate
fi

# Create superuser if environment variables are set
if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_EMAIL" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
    echo "👤 Creating superuser..."
    python manage.py createsuperuser --noinput --username "$DJANGO_SUPERUSER_USERNAME" --email "$DJANGO_SUPERUSER_EMAIL" || echo "Superuser might already exist"
fi

# Run post-build verification
echo "🔍 Running post-build verification..."
chmod +x verify.sh
./verify.sh

echo "🎉 Build completed successfully!"
echo "Database type: $DB_TYPE"
echo "Ready for deployment!"
