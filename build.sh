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

# Install requirements
if [ -f "requirements.txt" ]; then
    echo "Installing from requirements.txt..."
    pip install -r requirements.txt || {
        echo "❌ Main requirements failed, trying minimal requirements..."
        if [ -f "requirements-minimal.txt" ]; then
            pip install -r requirements-minimal.txt
        else
            echo "❌ No fallback requirements available"
            exit 1
        fi
    }
elif [ -f "requirements-minimal.txt" ]; then
    echo "Installing from requirements-minimal.txt..."
    pip install -r requirements-minimal.txt
else
    echo "❌ No requirements file found!"
    exit 1
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
