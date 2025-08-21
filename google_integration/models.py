"""
Models for Google Drive Integration
"""
from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.conf import settings
import json

User = get_user_model()


class GoogleDriveConfig(models.Model):
    """Configuration for Google Drive integration"""
    
    CONFIG_TYPE_CHOICES = [
        ('service_account', 'Service Account'),
        ('oauth', 'OAuth'),
    ]
    
    name = models.CharField(max_length=200, unique=True)
    config_type = models.CharField(max_length=20, choices=CONFIG_TYPE_CHOICES)
    is_active = models.BooleanField(default=True)
    
    # Service Account fields
    service_account_file = models.FileField(upload_to='google_credentials/', null=True, blank=True)
    
    # OAuth fields
    client_id = models.CharField(max_length=500, null=True, blank=True)
    client_secret = models.CharField(max_length=500, null=True, blank=True)
    redirect_uri = models.URLField(null=True, blank=True)
    
    # Database configuration
    database_spreadsheet_id = models.CharField(max_length=200, null=True, blank=True)
    drive_folder_id = models.CharField(max_length=200, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Google Drive Configuration"
        verbose_name_plural = "Google Drive Configurations"
    
    def __str__(self):
        return f"{self.name} ({self.get_config_type_display()})"


class GoogleDriveFolder(models.Model):
    """Google Drive folder mapping"""
    
    name = models.CharField(max_length=200)
    drive_id = models.CharField(max_length=200, unique=True)
    parent_folder = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
    local_path = models.CharField(max_length=500, null=True, blank=True)
    
    # Metadata
    size = models.BigIntegerField(null=True, blank=True)
    created_time = models.DateTimeField(null=True, blank=True)
    modified_time = models.DateTimeField(null=True, blank=True)
    
    # Sync information
    last_synced = models.DateTimeField(null=True, blank=True)
    sync_status = models.CharField(max_length=50, default='pending')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Google Drive Folder"
        verbose_name_plural = "Google Drive Folders"
    
    def __str__(self):
        return self.name


class GoogleDriveFile(models.Model):
    """Google Drive file mapping"""
    
    FILE_TYPE_CHOICES = [
        ('document', 'Document'),
        ('spreadsheet', 'Spreadsheet'),
        ('presentation', 'Presentation'),
        ('image', 'Image'),
        ('video', 'Video'),
        ('pdf', 'PDF'),
        ('other', 'Other'),
    ]
    
    name = models.CharField(max_length=200)
    drive_id = models.CharField(max_length=200, unique=True)
    folder = models.ForeignKey(GoogleDriveFolder, on_delete=models.CASCADE, null=True, blank=True)
    
    # File information
    mime_type = models.CharField(max_length=100)
    file_type = models.CharField(max_length=20, choices=FILE_TYPE_CHOICES, default='other')
    size = models.BigIntegerField(null=True, blank=True)
    web_view_link = models.URLField(null=True, blank=True)
    web_content_link = models.URLField(null=True, blank=True)
    
    # Local reference
    local_file = models.FileField(upload_to='google_drive_cache/', null=True, blank=True)
    local_path = models.CharField(max_length=500, null=True, blank=True)
    
    # Metadata
    created_time = models.DateTimeField(null=True, blank=True)
    modified_time = models.DateTimeField(null=True, blank=True)
    
    # Sync information
    last_synced = models.DateTimeField(null=True, blank=True)
    sync_status = models.CharField(max_length=50, default='pending')
    checksum = models.CharField(max_length=100, null=True, blank=True)
    
    # User associations
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Google Drive File"
        verbose_name_plural = "Google Drive Files"
    
    def __str__(self):
        return self.name
    
    def get_file_type(self):
        """Determine file type from mime type"""
        mime_mappings = {
            'application/vnd.google-apps.document': 'document',
            'application/vnd.google-apps.spreadsheet': 'spreadsheet',
            'application/vnd.google-apps.presentation': 'presentation',
            'application/pdf': 'pdf',
            'image/': 'image',
            'video/': 'video',
        }
        
        for mime_prefix, file_type in mime_mappings.items():
            if self.mime_type.startswith(mime_prefix):
                return file_type
        
        return 'other'


class GoogleSheetsTable(models.Model):
    """Google Sheets as database table mapping"""
    
    name = models.CharField(max_length=100)
    spreadsheet_id = models.CharField(max_length=200)
    sheet_name = models.CharField(max_length=100)
    range_name = models.CharField(max_length=50, default='A:Z')
    
    # Django model mapping
    django_model = models.CharField(max_length=200, null=True, blank=True)  # e.g., 'tasks.Task'
    
    # Column mapping (JSON field)
    column_mapping = models.JSONField(default=dict)  # Maps Django fields to sheet columns
    
    # Sync settings
    auto_sync = models.BooleanField(default=True)
    sync_interval_minutes = models.PositiveIntegerField(default=30)
    last_synced = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Google Sheets Table"
        verbose_name_plural = "Google Sheets Tables"
        unique_together = ['spreadsheet_id', 'sheet_name']
    
    def __str__(self):
        return f"{self.name} ({self.sheet_name})"


class GoogleDriveSyncLog(models.Model):
    """Log of sync operations with Google Drive"""
    
    SYNC_TYPE_CHOICES = [
        ('upload', 'Upload'),
        ('download', 'Download'),
        ('delete', 'Delete'),
        ('sync', 'Bidirectional Sync'),
        ('backup', 'Backup'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    sync_type = models.CharField(max_length=20, choices=SYNC_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # File/folder information
    file = models.ForeignKey(GoogleDriveFile, on_delete=models.CASCADE, null=True, blank=True)
    folder = models.ForeignKey(GoogleDriveFolder, on_delete=models.CASCADE, null=True, blank=True)
    
    # Operation details
    operation_data = models.JSONField(default=dict)
    error_message = models.TextField(null=True, blank=True)
    
    # Timing
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # User
    initiated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        verbose_name = "Google Drive Sync Log"
        verbose_name_plural = "Google Drive Sync Logs"
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.get_sync_type_display()} - {self.get_status_display()}"
    
    def mark_completed(self):
        """Mark the sync operation as completed"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()
    
    def mark_failed(self, error_message):
        """Mark the sync operation as failed"""
        self.status = 'failed'
        self.error_message = error_message
        self.completed_at = timezone.now()
        self.save()


class UserGoogleAuth(models.Model):
    """Store user's Google OAuth credentials"""
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    access_token = models.TextField()
    refresh_token = models.TextField(null=True, blank=True)
    token_expiry = models.DateTimeField(null=True, blank=True)
    
    # Scopes granted
    scopes = models.JSONField(default=list)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "User Google Authentication"
        verbose_name_plural = "User Google Authentications"
    
    def __str__(self):
        return f"{self.user.username} - Google Auth"
    
    def is_expired(self):
        """Check if the token is expired"""
        if self.token_expiry:
            return timezone.now() >= self.token_expiry
        return True
    
    def get_credentials(self):
        """Get Google OAuth credentials object"""
        from google.oauth2.credentials import Credentials
        
        return Credentials(
            token=self.access_token,
            refresh_token=self.refresh_token,
            token_uri='https://oauth2.googleapis.com/token',
            client_id=getattr(settings, 'GOOGLE_OAUTH_CLIENT_ID', ''),
            client_secret=getattr(settings, 'GOOGLE_OAUTH_CLIENT_SECRET', ''),
            scopes=self.scopes
        )
