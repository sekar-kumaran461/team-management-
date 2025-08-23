# 🆓 Google Drive API Setup Guide (FREE - 15GB Storage)

## ✅ What You Get
- **15GB completely FREE storage** (vs 5GB for paid Google Cloud)
- **No credit card required**
- **No billing account needed**
- **Uses your personal Google account**
- **Files appear in your Google Drive**

## 📋 Required Credentials
You need these 2 credentials (both FREE):
1. `GOOGLE_DRIVE_CLIENT_ID`
2. `GOOGLE_DRIVE_CLIENT_SECRET`

## 🚀 Step-by-Step Setup

### Step 1: Create Google Cloud Project (FREE)
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a project" → "New Project"
3. Enter project name: `VisionInnovateForge`
4. Click "Create" (no billing required)

### Step 2: Enable Google Drive API (FREE)
1. In your project, go to "APIs & Services" → "Library"
2. Search for "Google Drive API"
3. Click on "Google Drive API"
4. Click "Enable" (no cost)

### Step 3: Create OAuth2 Credentials (FREE)
1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth 2.0 Client IDs"
3. If prompted, configure OAuth consent screen:
   - User Type: **External** (free)
   - App name: `VisionInnovateForge`
   - User support email: Your email
   - Developer contact: Your email
   - Click "Save and Continue" through all steps
4. Back to "Credentials" → "Create Credentials" → "OAuth 2.0 Client IDs"
5. Application type: **Web application**
6. Name: `Team Management Storage`
7. Authorized redirect URIs: Add these URLs:
   ```
   http://localhost:8000/google-auth/callback/
   https://your-render-app.onrender.com/google-auth/callback/
   ```
8. Click "Create"
9. **Copy the Client ID and Client Secret** (you'll need these)

### Step 4: Update .env File
Add these to your `.env` file:
```env
USE_GOOGLE_DRIVE=True
GOOGLE_DRIVE_CLIENT_ID=your-actual-client-id-here
GOOGLE_DRIVE_CLIENT_SECRET=your-actual-client-secret-here
```

### Step 5: Test the Configuration
Run this command to verify setup:
```bash
python check_google_apis.py
```

## 🔧 What's Different from Paid Google Cloud Storage

| Feature | Google Drive API (FREE) | Google Cloud Storage (PAID) |
|---------|------------------------|------------------------------|
| **Storage** | 15GB FREE | 5GB free, then $0.020/GB/month |
| **Setup** | OAuth2 only | Service account + billing |
| **Cost** | $0 forever | Starts charging after 5GB |
| **Authentication** | User login | Service account JSON |
| **Credit Card** | Not required | Required for billing |

## 🎯 Current Status
- ✅ **Removed**: All paid Google Cloud Storage code
- ✅ **Updated**: Settings to use FREE Google Drive API
- ✅ **Ready**: For OAuth2 credentials setup
- ✅ **Fallback**: Local storage while setting up

## 🔗 Next Steps
1. Follow the setup steps above to get your credentials
2. Add them to your `.env` file
3. Restart Django server
4. Test file uploads

## 💡 Pro Tips
- **No billing**: Google Drive API is completely free for 15GB
- **Personal account**: Uses your regular Google account
- **File access**: Files appear in your Google Drive
- **Sharing**: Easy to share files with team members
- **Backup**: Your files are automatically backed up

## 🆘 Need Help?
If you need help with any step, just ask! The setup is much simpler than the paid Google Cloud Storage.
