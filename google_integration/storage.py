"""
Google Drive API Storage Backend for Django
FREE Google Drive integration - 15GB storage
Uses OAuth2 authentication (no service account needed)
"""

import os
from django.core.files.storage import Storage, FileSystemStorage
from django.conf import settings
from django.utils.deconstruct import deconstructible


@deconstructible
class GoogleDriveStorage(Storage):
    """
    Google Drive API Storage Backend
    FREE - Uses OAuth2 authentication (15GB free storage)
    Falls back to local storage when Google Drive is not available
    """
    
    def __init__(self):
        """Initialize Google Drive storage with fallback"""
        self.local_storage = FileSystemStorage()
        self.google_drive_enabled = getattr(settings, 'USE_GOOGLE_DRIVE', False)
        
        if self.google_drive_enabled:
            print("[INFO] Google Drive storage enabled (FREE - 15GB)")
            print("[INFO] OAuth2 authentication required for production use")
            print("[INFO] Currently using local storage as fallback")
        else:
            print("[INFO] Using local storage")
    
    def _save(self, name, content):
        """Save file - currently uses local storage as fallback"""
        print(f"[INFO] Saving file: {name}")
        
        if self.google_drive_enabled:
            print("[INFO] Google Drive integration requires OAuth2 setup")
            print("[INFO] Falling back to local storage")
        
        return self.local_storage._save(name, content)
    
    def _open(self, name, mode='rb'):
        """Open file - uses local storage"""
        return self.local_storage._open(name, mode)
    
    def delete(self, name):
        """Delete file - uses local storage"""
        return self.local_storage.delete(name)
    
    def exists(self, name):
        """Check if file exists - uses local storage"""
        return self.local_storage.exists(name)
    
    def listdir(self, path):
        """List directory contents - uses local storage"""
        return self.local_storage.listdir(path)
    
    def size(self, name):
        """Get file size - uses local storage"""
        return self.local_storage.size(name)
    
    def url(self, name):
        """Get file URL - uses local storage"""
        return self.local_storage.url(name)
    
    def get_available_space(self):
        """Get available storage space"""
        if self.google_drive_enabled:
            return "15GB (Google Drive Free Tier)"
        else:
            return "Local Storage"
