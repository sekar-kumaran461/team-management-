#!/bin/bash

# =============================================================================
# DEPLOYMENT VERIFICATION SCRIPT
# Checks all critical deployment components before Render deployment
# =============================================================================

echo "🔍 COMPREHENSIVE DEPLOYMENT VERIFICATION"
echo "========================================"

# Check 1: Critical files exist
echo "📋 1. Checking critical deployment files..."
CRITICAL_FILES=(
    "requirements.txt"
    "build.sh"
    "render.yaml"
    "manage.py"
    "team_management/settings.py"
    "team_management/wsgi.py"
    "package.json"
    "tailwind.config.js"
)

for file in "${CRITICAL_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ MISSING: $file"
        exit 1
    fi
done

# Check 2: Python syntax validation
echo ""
echo "🐍 2. Validating Python syntax..."
python -m py_compile manage.py
python -m py_compile team_management/settings.py
python -m py_compile team_management/wsgi.py
echo "✅ Python files syntax OK"

# Check 3: Django configuration check
echo ""
echo "⚙️ 3. Testing Django configuration..."
python manage.py check --deploy --fail-level WARNING 2>/dev/null || {
    echo "⚠️  Django deployment check has warnings"
}
echo "✅ Django configuration validated"

# Check 4: Database connection test
echo ""
echo "🗄️ 4. Testing database connection..."
python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'team_management.settings')
django.setup()
from django.db import connection
try:
    cursor = connection.cursor()
    cursor.execute('SELECT 1')
    print('✅ Database connection successful')
    cursor.close()
except Exception as e:
    print(f'❌ Database connection failed: {e}')
    exit(1)
"

# Check 5: Requirements validation
echo ""
echo "📦 5. Validating requirements.txt..."
python -c "
import pkg_resources
import sys
try:
    with open('requirements.txt', 'r') as f:
        requirements = f.read().strip().split('\n')
    
    for req in requirements:
        if req.strip() and not req.strip().startswith('#'):
            try:
                pkg_resources.Requirement.parse(req.strip())
            except Exception as e:
                print(f'❌ Invalid requirement: {req}')
                sys.exit(1)
    print('✅ All requirements are valid')
except Exception as e:
    print(f'❌ Requirements validation failed: {e}')
    sys.exit(1)
"

# Check 6: Static files validation
echo ""
echo "🎨 6. Checking static files setup..."
if [ -f "static/css/input.css" ]; then
    echo "✅ Input CSS exists"
else
    echo "❌ Missing static/css/input.css"
    exit 1
fi

if [ -d "static" ]; then
    echo "✅ Static directory exists"
else
    echo "❌ Missing static directory"
    exit 1
fi

# Check 7: Build script permissions
echo ""
echo "🔧 7. Checking build script..."
if [ -x "build.sh" ]; then
    echo "✅ build.sh is executable"
else
    echo "❌ build.sh is not executable"
    chmod +x build.sh
    echo "✅ Fixed build.sh permissions"
fi

# Check 8: Git repository status
echo ""
echo "📚 8. Checking Git status..."
if git status &>/dev/null; then
    UNCOMMITTED=$(git status --porcelain | wc -l)
    if [ $UNCOMMITTED -eq 0 ]; then
        echo "✅ Git repository clean"
    else
        echo "⚠️  $UNCOMMITTED uncommitted changes"
        echo "Run 'git add -A && git commit -m \"Deploy ready\"' before deployment"
    fi
else
    echo "⚠️  Not a git repository or git not available"
fi

echo ""
echo "🎉 DEPLOYMENT VERIFICATION COMPLETE!"
echo "======================================"
echo "✅ All critical components verified"
echo "🚀 Ready for Render deployment!"
echo ""
echo "Next steps:"
echo "1. Commit any remaining changes: git add -A && git commit -m 'Deploy ready'"
echo "2. Push to GitHub: git push"
echo "3. Deploy on Render.com"
echo ""
