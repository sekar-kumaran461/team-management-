# URGENT: Service Account Setup Required

## Current Issue
You have OAuth credentials (for user login) but you need SERVICE ACCOUNT credentials for Google Drive API access.

## Quick Fix Steps:

### Step 1: Create Service Account
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project: **visioninnovateforge**
3. Go to **IAM & Admin** > **Service Accounts**
4. Click **"Create Service Account"**
5. Name it: `django-drive-service`
6. Click **"Create and Continue"**
7. Skip role assignment for now (click **"Continue"**)
8. Click **"Done"**

### Step 2: Create Service Account Key
1. Click on the newly created service account
2. Go to **"Keys"** tab
3. Click **"Add Key"** > **"Create new key"**
4. Choose **"JSON"** format
5. Click **"Create"**
6. A JSON file will be downloaded (e.g., `visioninnovateforge-abc123.json`)

### Step 3: Place the File
1. Move the downloaded JSON file to your project directory:
   ```
   d:\team management\service-account-key.json
   ```

### Step 4: Update .env File
Update your `.env` file with:
```env
GOOGLE_SERVICE_ACCOUNT_FILE=d:/team management/service-account-key.json
```

### Step 5: Share Google Drive Folder
1. Open the service account JSON file
2. Copy the "client_email" value (e.g., `django-drive-service@visioninnovateforge.iam.gserviceaccount.com`)
3. Go to your Google Drive folder: https://drive.google.com/drive/folders/1BsE86v6KTnYNKID_AkPstX3JTP_8t0ZD
4. Right-click > **"Share"**
5. Add the service account email
6. Give it **"Editor"** permissions
7. Click **"Send"**

### Step 6: Enable APIs (if not already done)
1. In Google Cloud Console, go to **"APIs & Services"** > **"Library"**
2. Search and enable:
   - **Google Drive API**
   - **Google Sheets API**

### Step 7: Test Again
```bash
cd "d:\team management"
python test_google_drive.py
```

## What You Currently Have vs What You Need:

### ✅ You Have (OAuth Client):
- File: `client_secret_741944772993-kpc7megk23mnpukht27r0v226vso4hpn.apps.googleusercontent.com.json`
- Purpose: User authentication (login with Google)
- Status: ✅ Working

### ❌ You Need (Service Account):
- File: `service-account-key.json` (to be created)
- Purpose: Server-to-server API access
- Status: ❌ Missing

## Expected Service Account JSON Format:
```json
{
  "type": "service_account",
  "project_id": "visioninnovateforge",
  "private_key_id": "...",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
  "client_email": "django-drive-service@visioninnovateforge.iam.gserviceaccount.com",
  "client_id": "...",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "..."
}
```

Note: The "type" field should be "service_account", not "web" like your current file.
