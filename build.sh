#!/bin/bash

# =============================================================================
# COMPREHENSIVE BUILD SCRIPT FOR DJANGO TEAM MANAGEMENT APPLICATION
# Single-strategy approach with complete package installation
# =============================================================================

set -o errexit  # Exit on any error

echo "🚀 Starting Django Team Management Build Process..."
echo "Build timestamp: $(date)"
echo "Python version: $(python --version)"

# =============================================================================
# PHASE 1: ENVIRONMENT SETUP
# =============================================================================

echo "📁 Phase 1: Setting up environment..."

# Create necessary directories
mkdir -p logs media/submissions media/task_submissions static staticfiles
chmod 755 logs media static staticfiles

echo "✅ Environment setup completed"

# =============================================================================
# PHASE 2: PACKAGE INSTALLATION
# =============================================================================

echo "📦 Phase 2: Installing packages..."

# Upgrade pip and install build tools
python -m pip install --upgrade pip setuptools wheel

# Install all required packages from requirements.txt
echo "📦 Installing complete package set from requirements.txt..."
pip install -r requirements.txt

echo "✅ All packages installed successfully"

# =============================================================================
# PHASE 3: PACKAGE VERIFICATION
# =============================================================================

echo "🔍 Phase 3: Verifying critical packages..."

# Verify critical packages
python -c "
critical_packages = [
    'django', 'gunicorn', 'whitenoise', 'decouple', 
    'psycopg2', 'allauth', 'rest_framework', 'corsheaders', 'PIL'
]

missing_packages = []
for pkg in critical_packages:
    try:
        if pkg == 'PIL':
            import PIL
        else:
            __import__(pkg)
        print(f'✅ {pkg} available')
    except ImportError:
        print(f'❌ {pkg} MISSING')
        missing_packages.append(pkg)

if missing_packages:
    print(f'⚠️  Missing packages: {missing_packages}')
    print('Attempting to install missing packages...')
    import subprocess
    for pkg in missing_packages:
        if pkg == 'PIL':
            subprocess.run(['pip', 'install', 'Pillow==9.5.0'])
        elif pkg == 'psycopg2':
            subprocess.run(['pip', 'install', 'psycopg2-binary==2.9.6'])
        elif pkg == 'allauth':
            subprocess.run(['pip', 'install', 'django-allauth==0.54.0'])
        elif pkg == 'rest_framework':
            subprocess.run(['pip', 'install', 'djangorestframework==3.14.0'])
        elif pkg == 'corsheaders':
            subprocess.run(['pip', 'install', 'django-cors-headers==4.3.1'])
        elif pkg == 'decouple':
            subprocess.run(['pip', 'install', 'python-decouple==3.8'])
else:
    print('✅ All critical packages verified')
"

echo "✅ Package verification completed"

# =============================================================================
# PHASE 4: DJANGO APPLICATION SETUP
# =============================================================================

echo "🎨 Phase 4: Setting up Django application..."

# Collect static files
echo "🎨 Collecting static files..."
python manage.py collectstatic --noinput --clear

# Apply database migrations
echo "🗄️  Applying database migrations..."
python manage.py migrate

# Create superuser if environment variables are set
if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_EMAIL" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
    echo "👤 Creating superuser..."
    python manage.py createsuperuser --noinput --username "$DJANGO_SUPERUSER_USERNAME" --email "$DJANGO_SUPERUSER_EMAIL" || echo "⚠️  Superuser creation failed (might already exist)"
fi

echo "✅ Django application setup completed"

# =============================================================================
# BUILD COMPLETE
# =============================================================================

echo ""
echo "🎉 BUILD COMPLETED SUCCESSFULLY!"
echo "=================================="
echo "Build timestamp: $(date)"
echo "All packages installed and verified"
echo "Database migrations applied"
echo "Static files collected"
echo "🚀 Application is ready for deployment!"
echo "=================================="
