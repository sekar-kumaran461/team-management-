#!/bin/bash

# Post-build verification script
echo "🔍 Post-build verification..."

# Check if gunicorn is available
if command -v gunicorn &> /dev/null; then
    echo "✅ Gunicorn is available at: $(which gunicorn)"
    echo "✅ Gunicorn version: $(gunicorn --version)"
else
    echo "❌ Gunicorn not found"
    echo "📍 Current PATH: $PATH"
    echo "📍 Python executable: $(which python)"
    echo "📍 Pip packages:"
    pip list | grep -i gunicorn || echo "Gunicorn not in pip list"
    
    # Try to find gunicorn manually
    find /opt/render -name "gunicorn" 2>/dev/null || echo "Gunicorn executable not found"
    
    # Check Python site-packages
    python -c "import sys; print('Python path:', sys.path)"
    python -c "import gunicorn; print('Gunicorn module found')" 2>/dev/null || echo "Gunicorn module not importable"
fi

# Test Django
echo "🔍 Testing Django..."
python manage.py check --deploy || echo "Django check failed"

# Test database configuration
echo "🔍 Testing database configuration..."
python -c "
import os
import sys
sys.path.append('/opt/render/project/src')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'team_management.settings')
import django
django.setup()
from django.conf import settings
print(f'Database engine: {settings.DATABASES[\"default\"][\"ENGINE\"]}')
if 'postgresql' in settings.DATABASES['default']['ENGINE']:
    print('✅ PostgreSQL configured')
else:
    print('ℹ️  SQLite configured')
" || echo "Database configuration test failed"

echo "🔍 Verification complete"
