#!/bin/bash

# =============================================================================
# PRODUCTION BUILD SCRIPT FOR RENDER DEPLOYMENT
# Single file optimized for Supabase + Google Drive integration
# =============================================================================

set -o errexit  # Exit on any error

echo "🚀 Starting Production Build for Django Team Management..."
echo "Build timestamp: $(date)"
echo "Python version: $(python --version)"

# =============================================================================
# PHASE 1: ENVIRONMENT SETUP
# =============================================================================

echo "📁 Phase 1: Setting up environment..."

# Create necessary directories
mkdir -p logs media/submissions media/task_submissions static staticfiles
chmod 755 logs media static staticfiles

# Set proper permissions
find . -name "*.sh" -exec chmod +x {} \;

echo "✅ Environment setup completed"

# =============================================================================
# PHASE 2: PACKAGE INSTALLATION
# =============================================================================

echo "📦 Phase 2: Installing Python packages..."

# Upgrade pip first
python -m pip install --upgrade pip

# Detect Python version and choose requirements accordingly
PYTHON_VERSION=$(python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "Detected Python version: $PYTHON_VERSION"

# Install requirements with version-specific fallbacks
if [[ "$PYTHON_VERSION" == "3.13" ]]; then
    echo "Using Python 3.13 compatible requirements..."
    if [ -f "requirements-python313.txt" ]; then
        echo "Installing from requirements-python313.txt..."
        pip install -r requirements-python313.txt || {
            echo "❌ Python 3.13 requirements failed, trying core requirements..."
            if [ -f "requirements-core.txt" ]; then
                pip install -r requirements-core.txt || {
                    echo "❌ All requirements failed"
                    exit 1
                }
            else
                echo "❌ No core requirements available"
                exit 1
            fi
        }
    else
        echo "❌ No Python 3.13 requirements found, trying production..."
        pip install -r requirements-production.txt || {
            echo "❌ Production requirements failed"
            exit 1
        }
    fi
else
    echo "Using standard requirements for Python $PYTHON_VERSION..."
    if [ -f "requirements-production.txt" ]; then
        echo "Installing from requirements-production.txt..."
        pip install -r requirements-production.txt || {
            echo "❌ Production requirements failed, trying standard requirements..."
            if [ -f "requirements.txt" ]; then
                pip install -r requirements.txt || {
                    echo "❌ Standard requirements failed, trying minimal requirements..."
                    if [ -f "requirements-minimal.txt" ]; then
                        pip install -r requirements-minimal.txt || {
                            echo "❌ Minimal requirements failed, trying core requirements..."
                            if [ -f "requirements-core.txt" ]; then
                                pip install -r requirements-core.txt || {
                                    echo "❌ All requirements failed"
                                    exit 1
                                }
                            else
                                echo "❌ No core requirements available"
                                exit 1
                            fi
                        }
                    else
                        echo "❌ No minimal requirements available"
                        exit 1
                    fi
                }
            else
                echo "❌ No standard requirements available"
                exit 1
            fi
        }
    else
        echo "❌ No production requirements found"
        exit 1
    fi
fi

echo "✅ Python packages installed successfully"

# =============================================================================
# PHASE 3: NODE.JS AND CSS BUILD
# =============================================================================

echo "🎨 Phase 3: Building CSS assets..."

# Check if Node.js build is needed
if [ -f "package.json" ]; then
    echo "Installing Node.js dependencies..."
    npm install
    
    echo "Building Tailwind CSS..."
    npm run build
    
    echo "✅ CSS build completed"
else
    echo "⚠️  No package.json found, using fallback CSS..."
    # Use fallback CSS if available
    if [ -f "static/css/fallback.css" ]; then
        cp static/css/fallback.css static/css/output.css
        echo "✅ Fallback CSS applied"
    fi
fi

# =============================================================================
# PHASE 4: DJANGO SETUP
# =============================================================================

echo "🐍 Phase 4: Django configuration..."

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "✅ Static files collected"

# Run database migrations
echo "Running database migrations..."
python manage.py migrate --noinput

echo "✅ Database migrations completed"

# Create superuser if environment variables are provided
echo "Creating superuser (if configured)..."
if [ -n "$DJANGO_SUPERUSER_EMAIL" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
    python manage.py create_superuser
    echo "✅ Superuser creation attempted"
else
    echo "ℹ️  Superuser creation skipped (DJANGO_SUPERUSER_EMAIL and DJANGO_SUPERUSER_PASSWORD not set)"
fi

# =============================================================================
# PHASE 5: VERIFICATION
# =============================================================================

echo "🔍 Phase 5: Verification..."

# Check Django configuration
python manage.py check --deploy

echo "✅ Django deployment checks passed"

# =============================================================================
# BUILD COMPLETION
# =============================================================================

echo "🎉 Build completed successfully!"
echo "Application is ready for deployment"
echo "Build completed at: $(date)"
