# Django Team Management - Render Deployment Guide

This guide will help you deploy your Django Team Management application to Render.

## Prerequisites

1. **GitHub Repository**: Your code must be in a GitHub repository
2. **Render Account**: Sign up at [render.com](https://render.com)
3. **Environment Variables**: Prepare your environment variables

## Step 1: Prepare Your Repository

1. Make sure all your code is committed and pushed to GitHub
2. Ensure your repository is public or you have a paid Render plan for private repos

## Step 2: Create a New Web Service on Render

1. Go to [render.com](https://render.com) and sign in
2. Click "New +" and select "Web Service"
3. Connect your GitHub repository
4. Select your team management repository

## Step 3: Configure Your Web Service

### Basic Settings:
- **Name**: `team-management` (or your preferred name)
- **Environment**: `Python 3`
- **Build Command**: `./build.sh`
- **Start Command**: `gunicorn team_management.wsgi:application`
- **Plan**: `Free` (for testing) or `Starter` (for production)

### Environment Variables:
Add these environment variables in the Render dashboard:

#### Required Variables:
```
DEBUG=False
SECRET_KEY=[Generate a new secret key - Render can auto-generate this]
ALLOWED_HOSTS=*
DATABASE_URL=postgresql://postgres.xvwwawadfeqnrwmozeai:[YOUR-SUPABASE-PASSWORD]@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres
SUPABASE_HOST=aws-1-ap-southeast-1.pooler.supabase.com
SUPABASE_PORT=6543
SUPABASE_DATABASE=postgres
SUPABASE_USER=postgres.xvwwawadfeqnrwmozeai
SUPABASE_PASSWORD=[YOUR-SUPABASE-PASSWORD]
PYTHON_VERSION=3.11.5
DISABLE_COLLECTSTATIC=0
```

#### If Build Fails - Use Minimal Setup:
If you encounter build errors, try these alternatives:
1. **Use minimal requirements**: Change build command to `./build-minimal.sh`
2. **Use minimal requirements.txt**: Rename `requirements-minimal.txt` to `requirements.txt`
3. **Skip Node.js**: Remove or rename `package.json` temporarily

#### Optional Variables (for full functionality):
```
# Google OAuth (if using Google login)
GOOGLE_OAUTH2_CLIENT_ID=your_google_client_id
GOOGLE_OAUTH2_CLIENT_SECRET=your_google_client_secret

# Google Drive Integration (if using file uploads to Drive)
GOOGLE_SERVICE_ACCOUNT_JSON=your_service_account_json
GOOGLE_DRIVE_FOLDER_ID=your_drive_folder_id
GOOGLE_DATABASE_SPREADSHEET_ID=your_spreadsheet_id

# Email Settings (for notifications)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password

# Redis (for Celery tasks - only if you need background tasks)
CELERY_BROKER_URL=redis://your-redis-url
CELERY_RESULT_BACKEND=redis://your-redis-url
```

## Step 4: Configure Environment Variables (Using Supabase)

Since you're using Supabase as your database, you don't need to create a separate PostgreSQL service on Render. Instead:

1. In Render dashboard, go to your web service
2. Go to "Environment" tab
3. Add the Supabase environment variables listed above
4. Make sure to replace `[YOUR-SUPABASE-PASSWORD]` with your actual Supabase password

**Note**: You can find your Supabase password in your Supabase dashboard under Settings → Database → Connection string.

## Step 5: Deploy

1. Click "Create Web Service"
2. Render will automatically:
   - Clone your repository
   - Run the build script (`build.sh`)
   - Install dependencies
   - Collect static files
   - Run database migrations
   - Start your application

## Step 6: Post-Deployment Setup

### Create a Superuser (Optional)
You can create a Django superuser by connecting to your service via SSH:
1. Go to your service dashboard
2. Click "Shell" tab
3. Run: `python manage.py createsuperuser`

### Test Your Application
1. Visit your Render URL (e.g., `https://your-app-name.onrender.com`)
2. Test user registration and login
3. Verify that static files are loading correctly

## Common Issues and Solutions

### Static Files Not Loading
- Make sure `whitenoise` is in your requirements.txt
- Verify `STATIC_ROOT` and `STATICFILES_STORAGE` settings
- Check that `python manage.py collectstatic` runs without errors

### Database Connection Issues
- Verify `DATABASE_URL` environment variable is set correctly
- Make sure migrations have run successfully
- Check that PostgreSQL service is running

### Environment Variables
- Double-check all environment variable names and values
- Use Render's environment variable tab, don't put secrets in code
- Some variables are case-sensitive

### Build Failures
- Check the build logs in Render dashboard
- Ensure all dependencies are in requirements.txt
- Verify that build.sh has execute permissions (chmod +x build.sh)

## Security Considerations

1. **Never commit secrets** to your repository
2. **Use environment variables** for all sensitive data
3. **Set DEBUG=False** in production
4. **Use a strong SECRET_KEY** (let Render generate one)
5. **Configure proper ALLOWED_HOSTS**

## Scaling and Performance

- Start with the Free plan for testing
- Upgrade to Starter ($7/month) for production use
- Consider upgrading PostgreSQL for better performance
- Add Redis for caching and background tasks if needed

## Monitoring

- Use Render's built-in logs and metrics
- Set up error monitoring (Sentry, etc.)
- Monitor database performance
- Set up uptime monitoring

Your Django Team Management application should now be successfully deployed on Render!
