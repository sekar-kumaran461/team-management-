"""
Custom Google Drive storage backend for Django
Handles media files upload to Google Drive
"""

import os
import json
import tempfile
from django.core.files.storage import Storage
from django.core.files.base import ContentFile
from django.conf import settings
from django.utils.deconstruct import deconstructible
from django.utils import timezone
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload
import io


@deconstructible
class GoogleDriveStorage(Storage):
    """
    Custom storage backend for Google Drive integration
    """
    
    def __init__(self, option=None):
        if not option:
            option = settings.GOOGLE_DRIVE_STORAGE_JSON_KEY_FILE
        self._option = option
        self.service = None
        self.folder_id = getattr(settings, 'GOOGLE_DRIVE_FOLDER_ID', None)
        
    def _get_service(self):
        """Initialize Google Drive service"""
        if self.service is None:
            try:
                # Try to get service account JSON from settings
                service_account_json = getattr(settings, 'GOOGLE_SERVICE_ACCOUNT_JSON', '')
                
                if service_account_json:
                    # Parse JSON string
                    service_account_info = json.loads(service_account_json)
                    credentials = service_account.Credentials.from_service_account_info(
                        service_account_info,
                        scopes=['https://www.googleapis.com/auth/drive.file']
                    )
                elif self._option and os.path.exists(self._option):
                    # Use file path
                    credentials = service_account.Credentials.from_service_account_file(
                        self._option,
                        scopes=['https://www.googleapis.com/auth/drive.file']
                    )
                else:
                    raise ValueError("No valid Google Drive credentials found")
                
                self.service = build('drive', 'v3', credentials=credentials)
                
            except Exception as e:
                print(f"Error initializing Google Drive service: {e}")
                raise
                
        return self.service
    
    def _save(self, name, content):
        """Save file to Google Drive"""
        try:
            service = self._get_service()
            
            # Prepare file metadata
            file_metadata = {
                'name': name,
                'parents': [self.folder_id] if self.folder_id else []
            }
            
            # Create media upload
            media = MediaIoBaseUpload(
                io.BytesIO(content.read()),
                mimetype='application/octet-stream',
                resumable=True
            )
            
            # Upload file
            file = service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id,name,webViewLink,webContentLink'
            ).execute()
            
            return file.get('id')  # Return file ID as the "name"
            
        except Exception as e:
            print(f"Error saving file to Google Drive: {e}")
            raise
    
    def _open(self, name, mode='rb'):
        """Open file from Google Drive"""
        try:
            service = self._get_service()
            
            # Download file content
            request = service.files().get_media(fileId=name)
            file_content = io.BytesIO()
            downloader = MediaIoBaseDownload(file_content, request)
            
            done = False
            while done is False:
                status, done = downloader.next_chunk()
            
            file_content.seek(0)
            return ContentFile(file_content.read())
            
        except Exception as e:
            print(f"Error opening file from Google Drive: {e}")
            raise
    
    def delete(self, name):
        """Delete file from Google Drive"""
        try:
            service = self._get_service()
            service.files().delete(fileId=name).execute()
            
        except Exception as e:
            print(f"Error deleting file from Google Drive: {e}")
            # Don't raise error for delete operations
            pass
    
    def exists(self, name):
        """Check if file exists in Google Drive"""
        try:
            service = self._get_service()
            file = service.files().get(fileId=name, fields='id').execute()
            return bool(file.get('id'))
            
        except Exception:
            return False
    
    def size(self, name):
        """Get file size from Google Drive"""
        try:
            service = self._get_service()
            file = service.files().get(fileId=name, fields='size').execute()
            return int(file.get('size', 0))
            
        except Exception:
            return 0
    
    def url(self, name):
        """Get public URL for Google Drive file"""
        try:
            # For public files, use direct download link
            return f"https://drive.google.com/uc?id={name}&export=download"
            
        except Exception:
            return f"https://drive.google.com/file/d/{name}/view"
    
    def get_modified_time(self, name):
        """Get file modification time"""
        try:
            service = self._get_service()
            file = service.files().get(fileId=name, fields='modifiedTime').execute()
            
            # Parse ISO format time
            from datetime import datetime
            modified_time = datetime.fromisoformat(
                file.get('modifiedTime', '').replace('Z', '+00:00')
            )
            return timezone.make_aware(modified_time)
            
        except Exception:
            return timezone.now()
    
    def listdir(self, path):
        """List directory contents"""
        try:
            service = self._get_service()
            
            # Get folder contents
            query = f"'{self.folder_id}' in parents" if self.folder_id else ""
            results = service.files().list(
                q=query,
                fields='files(id,name,mimeType)'
            ).execute()
            
            files = results.get('files', [])
            
            # Separate directories and files
            directories = [f['name'] for f in files if f['mimeType'] == 'application/vnd.google-apps.folder']
            file_names = [f['name'] for f in files if f['mimeType'] != 'application/vnd.google-apps.folder']
            
            return directories, file_names
            
        except Exception:
            return [], []
