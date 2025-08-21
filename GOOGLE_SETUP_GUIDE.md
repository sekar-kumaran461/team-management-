# Google Drive Integration Setup Guide

## Overview
This Django application supports Google Drive integration for file storage and Google Sheets as a database backend. You need to configure Google API credentials to enable these features.

## Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the following APIs:
   - Google Drive API
   - Google Sheets API
   - Google+ API (for OAuth)

## Step 2: Create OAuth 2.0 Credentials (for User Authentication)

1. In Google Cloud Console, go to "Credentials"
2. Click "Create Credentials" > "OAuth 2.0 Client IDs"
3. Choose "Web application"
4. Add authorized redirect URIs:
   - `http://127.0.0.1:8000/accounts/google/login/callback/`
   - `http://localhost:8000/accounts/google/login/callback/`
   - Add your production domain if deploying
5. Copy the Client ID and Client Secret

## Step 3: Create Service Account (for Server-to-Server Access)

1. In Google Cloud Console, go to "Credentials"
2. Click "Create Credentials" > "Service Account"
3. Fill in the service account details
4. Click "Create and Continue"
5. Grant the service account the following roles:
   - Editor (for Drive access)
   - Or create custom roles with specific permissions
6. Click "Done"
7. Click on the created service account
8. Go to "Keys" tab
9. Click "Add Key" > "Create new key" > "JSON"
10. Download the JSON file - this is your service account key

## Step 4: Configure Your .env File

Update your `.env` file with the following values:

```env
# Google OAuth 2.0 Credentials
GOOGLE_OAUTH2_CLIENT_ID=your-oauth-client-id-from-step-2
GOOGLE_OAUTH2_CLIENT_SECRET=your-oauth-client-secret-from-step-2

# Google Service Account
GOOGLE_SERVICE_ACCOUNT_FILE=path/to/your/downloaded-service-account-key.json
GOOGLE_SERVICE_ACCOUNT_JSON=paste-entire-json-content-here-as-single-line

# Google Drive Settings
GOOGLE_DRIVE_FOLDER_ID=your-target-drive-folder-id
GOOGLE_DRIVE_STORAGE_JSON_KEY_FILE=path/to/your/downloaded-service-account-key.json

# Google Sheets Database
GOOGLE_DATABASE_SPREADSHEET_ID=your-google-spreadsheet-id-for-database
```

### How to get Google Drive Folder ID:
1. Go to Google Drive
2. Create or navigate to the folder you want to use
3. The folder ID is in the URL: `https://drive.google.com/drive/folders/FOLDER_ID_HERE`

### How to get Google Spreadsheet ID:
1. Create a Google Spreadsheet
2. The spreadsheet ID is in the URL: `https://docs.google.com/spreadsheets/d/SPREADSHEET_ID_HERE/edit`

## Step 5: Share Resources with Service Account

### For Google Drive:
1. Go to the Google Drive folder you want to use
2. Right-click > "Share"
3. Add the service account email (found in the JSON file as "client_email")
4. Give it "Editor" permissions

### For Google Sheets:
1. Open your Google Spreadsheet
2. Click "Share" button
3. Add the service account email
4. Give it "Editor" permissions

## Step 6: Test Configuration

1. Restart your Django server
2. Try to login with Google OAuth
3. Test file uploads to verify Drive integration
4. Check if data syncs with Google Sheets

## Example .env Configuration

```env
# Django Settings
SECRET_KEY=your-django-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Google OAuth 2.0 Credentials
GOOGLE_OAUTH2_CLIENT_ID=123456789-abcdefghijklmnop.apps.googleusercontent.com
GOOGLE_OAUTH2_CLIENT_SECRET=GOCSPX-AbCdEfGhIjKlMnOpQrStUvWxYz

# Google Service Account
GOOGLE_SERVICE_ACCOUNT_FILE=D:/team management/google-service-account.json
GOOGLE_SERVICE_ACCOUNT_JSON={"type":"service_account","project_id":"your-project",...}

# Google Drive Settings
GOOGLE_DRIVE_FOLDER_ID=1AbCdEfGhIjKlMnOpQrStUvWxYz123456
GOOGLE_DRIVE_STORAGE_JSON_KEY_FILE=D:/team management/google-service-account.json

# Google Sheets Database
GOOGLE_DATABASE_SPREADSHEET_ID=1AbCdEfGhIjKlMnOpQrStUvWxYz123456789
```

## Troubleshooting

### Common Issues:

1. **"Access denied" errors**
   - Make sure the service account has been shared with the Drive folder/Spreadsheet
   - Check that the APIs are enabled in Google Cloud Console

2. **"Invalid client" errors**
   - Verify OAuth client ID and secret are correct
   - Check redirect URIs match your domain exactly

3. **"Permission denied" for Drive**
   - Ensure the service account email has edit access to the Drive folder
   - Verify the folder ID is correct

4. **File not found errors**
   - Check the path to your service account JSON file
   - Make sure the file exists and is readable

### Testing Commands:

```bash
# Test Google Drive connection
python manage.py shell
from google_integration.services import GoogleDriveService
service = GoogleDriveService()
service.test_connection()

# Test Google Sheets connection
from google_integration.services import GoogleSheetsService
sheets = GoogleSheetsService()
sheets.test_connection()
```

## Security Notes

1. **Never commit credentials to version control**
2. **Use environment variables for all sensitive data**
3. **Rotate service account keys regularly**
4. **Use least privilege principle for API permissions**
5. **Monitor API usage in Google Cloud Console**

## Production Deployment

For production deployment:
1. Use a secure secret management service
2. Set up proper domain redirects for OAuth
3. Enable audit logging
4. Use HTTPS for all OAuth redirects
5. Consider using Google Cloud IAM for better security

## Support

If you encounter issues:
1. Check Django logs
2. Check Google Cloud Console API usage and errors
3. Verify all configuration values
4. Test with a simple API call first
