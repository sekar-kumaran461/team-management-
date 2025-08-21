#!/bin/bash

# Startup script to ensure gunicorn is properly accessible
echo "🚀 Starting Django Team Management Application..."

# Try different ways to find and run gunicorn
if command -v gunicorn &> /dev/null; then
    echo "✅ Found gunicorn in PATH: $(which gunicorn)"
    exec gunicorn team_management.wsgi:application --bind 0.0.0.0:$PORT --workers 1 --timeout 120
elif python -m gunicorn --version &> /dev/null; then
    echo "✅ Found gunicorn via python -m"
    exec python -m gunicorn team_management.wsgi:application --bind 0.0.0.0:$PORT --workers 1 --timeout 120
elif [ -f "/opt/render/project/src/.venv/bin/gunicorn" ]; then
    echo "✅ Found gunicorn in venv"
    exec /opt/render/project/src/.venv/bin/gunicorn team_management.wsgi:application --bind 0.0.0.0:$PORT --workers 1 --timeout 120
elif [ -f "$HOME/.local/bin/gunicorn" ]; then
    echo "✅ Found gunicorn in user bin"
    exec $HOME/.local/bin/gunicorn team_management.wsgi:application --bind 0.0.0.0:$PORT --workers 1 --timeout 120
else
    echo "❌ Gunicorn not found, trying to install and run..."
    pip install gunicorn==20.1.0
    exec python -m gunicorn team_management.wsgi:application --bind 0.0.0.0:$PORT --workers 1 --timeout 120
fi
