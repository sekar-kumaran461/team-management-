# Fallback settings for deployment without psycopg2
import os
from pathlib import Path
from decouple import config

# For emergency deployment without psycopg2
if config('USE_SQLITE_FALLBACK', default=False, cast=bool):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': '/tmp/db.sqlite3',  # Use tmp directory on Render
        }
    }
    print("WARNING: Using SQLite fallback database!")
else:
    # Normal Supabase configuration
    if config('DATABASE_URL', default=None):
        import dj_database_url
        DATABASES = {
            'default': dj_database_url.parse(
                config('DATABASE_URL'),
                conn_max_age=600,
                conn_health_checks=True,
            )
        }
    else:
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': BASE_DIR / 'db.sqlite3',
            }
        }
