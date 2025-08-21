# Supabase Database Configuration Guide

This guide explains how to configure your Django application to work with Supabase database.

## Supabase Database Details

Your Supabase database configuration:
- **Host**: `aws-1-ap-southeast-1.pooler.supabase.com`
- **Port**: `6543`
- **Database**: `postgres`
- **User**: `postgres.xvwwawadfeqnrwmozeai`
- **Pool Mode**: `transaction`

## Environment Variables

Set these environment variables in your deployment platform (Render):

### Required Variables:
```bash
DATABASE_URL=postgresql://postgres.xvwwawadfeqnrwmozeai:[YOUR-PASSWORD]@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres
SUPABASE_HOST=aws-1-ap-southeast-1.pooler.supabase.com
SUPABASE_PORT=6543
SUPABASE_DATABASE=postgres
SUPABASE_USER=postgres.xvwwawadfeqnrwmozeai
SUPABASE_PASSWORD=[YOUR-SUPABASE-PASSWORD]
SUPABASE_POOL_MODE=transaction
```

### Standard Django Variables:
```bash
DEBUG=False
SECRET_KEY=[AUTO-GENERATE]
ALLOWED_HOSTS=*
PYTHON_VERSION=3.11.5
```

## Getting Your Supabase Password

1. Go to your [Supabase Dashboard](https://supabase.com/dashboard)
2. Select your project
3. Go to **Settings** → **Database**
4. Find the **Connection string** section
5. Copy the password from the connection string

## Connection String Format

The complete DATABASE_URL should look like:
```
postgresql://postgres.xvwwawadfeqnrwmozeai:your_actual_password@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres
```

## Supabase-Specific Features

### Connection Pooling
- Your database uses **transaction** pool mode
- This is optimal for Django applications
- No additional configuration needed

### SSL Connection
- Supabase requires SSL connections
- This is automatically configured in the Django settings

### Connection Health Checks
- Enabled for better reliability
- Automatically reconnects on connection issues

## Testing the Connection

### Local Testing:
1. Create a `.env` file with your Supabase credentials
2. Run: `python manage.py dbshell`
3. If successful, you'll see PostgreSQL prompt

### Production Testing:
1. Deploy to Render with environment variables set
2. Check logs for successful database migrations
3. Visit your app to test database functionality

## Common Issues and Solutions

### Issue: SSL Certificate Verification Failed
**Solution**: Make sure `sslmode=require` is in your connection string

### Issue: Connection Timeout
**Solution**: Check that port 6543 is correct and accessible

### Issue: Authentication Failed
**Solution**: Verify your username and password are correct

### Issue: Database Does Not Exist
**Solution**: Use `postgres` as the database name (default Supabase database)

## Migration Commands

When deploying, these commands will run automatically:
```bash
python manage.py migrate
python manage.py collectstatic --no-input
```

## Security Notes

1. **Never commit passwords** to your repository
2. **Use environment variables** for all sensitive data
3. **Regularly rotate** your database passwords
4. **Monitor connection usage** in Supabase dashboard

## Supabase Dashboard Access

- **URL**: https://supabase.com/dashboard
- **Project**: Your team management project
- **Database**: Go to Table Editor to view your Django tables
- **Logs**: Monitor database queries and performance

Your Django application is now configured to use Supabase as the database backend!
