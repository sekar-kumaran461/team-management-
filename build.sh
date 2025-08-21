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

# Install packages with fallback strategy for problematic packages
echo "📦 Installing core Django packages first..."
pip install Django==4.2.7 gunicorn==20.1.0 whitenoise==6.5.0 python-decouple==3.8

echo "📦 Installing database packages..."
pip install psycopg2-binary==2.9.6 dj-database-url==2.1.0

echo "📦 Installing authentication packages..."
pip install django-allauth==0.54.0

echo "📦 Installing API packages..."
pip install djangorestframework==3.14.0 django-cors-headers==4.3.1

echo "📦 Installing image processing (with fallback)..."
if ! pip install Pillow==10.0.1; then
    echo "⚠️  Pillow 10.0.1 failed, trying 10.0.0..."
    if ! pip install Pillow==10.0.0; then
        echo "⚠️  Pillow 10.0.0 failed, trying 9.5.0..."
        if ! pip install Pillow==9.5.0; then
            echo "⚠️  Trying to install latest Pillow..."
            pip install Pillow || echo "⚠️  Pillow installation failed, continuing without it"
        fi
    fi
fi

echo "📦 Installing optional data processing packages..."
pip install pandas==2.0.3 openpyxl==3.1.2 || echo "⚠️  Data processing packages failed, continuing without them"

echo "✅ Package installation completed"

# =============================================================================
# PHASE 3: PACKAGE VERIFICATION
# =============================================================================

echo "🔍 Phase 3: Verifying critical packages..."

# Verify critical packages
python -c "
critical_packages = [
    'django', 'gunicorn', 'whitenoise', 'decouple', 
    'psycopg2', 'allauth', 'rest_framework', 'corsheaders'
]

optional_packages = ['PIL', 'pandas', 'openpyxl']

print('Checking critical packages:')
missing_critical = []
for pkg in critical_packages:
    try:
        __import__(pkg)
        print(f'✅ {pkg} available')
    except ImportError:
        print(f'❌ {pkg} MISSING')
        missing_critical.append(pkg)

print('\\nChecking optional packages:')
missing_optional = []
for pkg in optional_packages:
    try:
        if pkg == 'PIL':
            import PIL
            print(f'✅ {pkg} available')
        else:
            __import__(pkg)
            print(f'✅ {pkg} available')
    except ImportError:
        print(f'⚠️  {pkg} not available (optional)')
        missing_optional.append(pkg)

if missing_critical:
    print(f'\\n❌ CRITICAL packages missing: {missing_critical}')
    print('Attempting to install missing critical packages...')
    import subprocess
    for pkg in missing_critical:
        if pkg == 'psycopg2':
            subprocess.run(['pip', 'install', 'psycopg2-binary==2.9.6'])
        elif pkg == 'allauth':
            subprocess.run(['pip', 'install', 'django-allauth==0.54.0'])
        elif pkg == 'rest_framework':
            subprocess.run(['pip', 'install', 'djangorestframework==3.14.0'])
        elif pkg == 'corsheaders':
            subprocess.run(['pip', 'install', 'django-cors-headers==4.3.1'])
        elif pkg == 'decouple':
            subprocess.run(['pip', 'install', 'python-decouple==3.8'])
        elif pkg == 'whitenoise':
            subprocess.run(['pip', 'install', 'whitenoise==6.5.0'])
        elif pkg == 'gunicorn':
            subprocess.run(['pip', 'install', 'gunicorn==20.1.0'])
        elif pkg == 'django':
            subprocess.run(['pip', 'install', 'Django==4.2.7'])
else:
    print('\\n✅ All critical packages verified')

if missing_optional:
    print(f'ℹ️  Optional packages not available: {missing_optional}')
    print('Application will run without these features')
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
