"""
Alternative database configuration for Supabase
Use this if the main DATABASE_URL parsing fails
"""

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'postgres',
        'USER': 'postgres.xvwwawadfeqnrwmozeai',
        'PASSWORD': 'Vif2025team$',
        'HOST': 'aws-1-ap-southeast-1.pooler.supabase.com',
        'PORT': '6543',
        'OPTIONS': {
            'sslmode': 'require',
        },
        'CONN_MAX_AGE': 600,
        'CONN_HEALTH_CHECKS': True,
    }
}
