# Quick Render Deployment Steps

## 1. Push to GitHub
Make sure your code is in a GitHub repository and all changes are pushed.

## 2. Sign up for Render
Go to https://render.com and create an account.

## 3. Create Web Service
1. Click "New +" → "Web Service"
2. Connect your GitHub repository
3. Select your team management repository

## 4. Configure Service
**Basic Settings:**
- Name: `team-management`
- Environment: `Python 3`
- Build Command: `./build.sh`
- Start Command: `gunicorn team_management.wsgi:application`

**Environment Variables (Essential):**
```
DEBUG=False
SECRET_KEY=[Let Render auto-generate this]
ALLOWED_HOSTS=*
```

## 5. Add PostgreSQL Database
1. Click "New +" → "PostgreSQL"
2. Name: `team-management-db`
3. Copy the "External Database URL" 
4. Add it as `DATABASE_URL` in your web service environment variables

## 6. Deploy
Click "Create Web Service" and wait for deployment to complete.

Your app will be available at: `https://your-app-name.onrender.com`

## Optional: Create Admin User
After deployment, use Render's shell to create a superuser:
```bash
python manage.py createsuperuser
```

That's it! Your Django app should now be live on Render.
