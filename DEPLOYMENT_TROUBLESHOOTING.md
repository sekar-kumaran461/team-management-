# Emergency Deployment Guide - Python Version Issues

## Problem
Render is using Python 3.13 instead of the specified Python 3.11.6, causing package build failures.

## Solution Options (Try in Order)

### Option 1: Use Emergency Build Script
1. In Render dashboard, change Build Command to: `./build-emergency.sh`
2. This script installs packages one by one with error handling

### Option 2: Manual Build Command
If the script doesn't work, use this manual build command in Render:
```bash
python3.11 -m pip install --upgrade pip && pip install Django==4.2.7 gunicorn==20.1.0 whitenoise==6.5.0 psycopg2-binary==2.9.6 python-decouple==3.8 dj-database-url==2.1.0 && python manage.py collectstatic --no-input && python manage.py migrate
```

### Option 3: Use Blueprint (render.yaml)
The render.yaml file specifies `runtime: python-3.11.6` which should force the correct Python version.

### Option 4: Contact Render Support
If Python version issues persist, contact Render support to ensure Python 3.11.6 is being used.

## Environment Variables Required
```
DEBUG=False
SECRET_KEY=[AUTO-GENERATE]
ALLOWED_HOSTS=*
DATABASE_URL=postgresql://postgres.xvwwawadfeqnrwmozeai:Vif2025team$@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres
PYTHON_VERSION=3.11.6
```

## After Basic Deployment Works
Once the basic app is deployed, you can gradually add more packages:
1. Uncomment packages in requirements.txt
2. Redeploy one section at a time
3. Monitor build logs for any failures

## Package Installation Order
1. Core Django packages ✅
2. Database packages ✅  
3. Static files packages ✅
4. Authentication packages
5. API packages
6. Google integration packages
7. Background task packages

## Current Status
- ✅ Core Django functionality
- ✅ Supabase database connection
- ✅ Static files handling
- ⚠️ Optional packages commented out temporarily
