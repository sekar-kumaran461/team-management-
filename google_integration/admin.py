"""
Admin interface for Google Drive Integration
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import (
    GoogleDriveConfig, GoogleDriveFolder, GoogleDriveFile,
    GoogleSheetsTable, GoogleDriveSyncLog, UserGoogleAuth
)


@admin.register(GoogleDriveConfig)
class GoogleDriveConfigAdmin(admin.ModelAdmin):
    list_display = ['name', 'config_type', 'is_active', 'created_at']
    list_filter = ['config_type', 'is_active']
    search_fields = ['name']
    
    fieldsets = (
        ('Basic Configuration', {
            'fields': ('name', 'config_type', 'is_active')
        }),
        ('Service Account Settings', {
            'fields': ('service_account_file',),
            'classes': ('collapse',),
        }),
        ('OAuth Settings', {
            'fields': ('client_id', 'client_secret', 'redirect_uri'),
            'classes': ('collapse',),
        }),
        ('Database Configuration', {
            'fields': ('database_spreadsheet_id', 'drive_folder_id'),
        }),
    )


@admin.register(GoogleDriveFolder)
class GoogleDriveFolderAdmin(admin.ModelAdmin):
    list_display = ['name', 'drive_id', 'parent_folder', 'sync_status', 'last_synced']
    list_filter = ['sync_status', 'last_synced']
    search_fields = ['name', 'drive_id']
    raw_id_fields = ['parent_folder']


@admin.register(GoogleDriveFile)
class GoogleDriveFileAdmin(admin.ModelAdmin):
    list_display = ['name', 'file_type', 'size_display', 'sync_status', 'uploaded_by', 'last_synced']
    list_filter = ['file_type', 'sync_status', 'uploaded_by']
    search_fields = ['name', 'drive_id']
    raw_id_fields = ['folder', 'uploaded_by']
    readonly_fields = ['drive_id', 'web_view_link', 'web_content_link']
    
    def size_display(self, obj):
        if obj.size:
            if obj.size < 1024:
                return f"{obj.size} B"
            elif obj.size < 1024 * 1024:
                return f"{obj.size / 1024:.1f} KB"
            else:
                return f"{obj.size / (1024 * 1024):.1f} MB"
        return "Unknown"
    size_display.short_description = "Size"


@admin.register(GoogleSheetsTable)
class GoogleSheetsTableAdmin(admin.ModelAdmin):
    list_display = ['name', 'sheet_name', 'django_model', 'auto_sync', 'last_synced']
    list_filter = ['auto_sync', 'last_synced']
    search_fields = ['name', 'sheet_name', 'django_model']


@admin.register(GoogleDriveSyncLog)
class GoogleDriveSyncLogAdmin(admin.ModelAdmin):
    list_display = ['sync_type', 'status', 'file_or_folder', 'initiated_by', 'started_at', 'duration']
    list_filter = ['sync_type', 'status', 'started_at']
    search_fields = ['file__name', 'folder__name', 'initiated_by__username']
    readonly_fields = ['started_at', 'completed_at', 'duration']
    
    def file_or_folder(self, obj):
        if obj.file:
            return format_html('<span style="color: blue;">📄 {}</span>', obj.file.name)
        elif obj.folder:
            return format_html('<span style="color: green;">📁 {}</span>', obj.folder.name)
        return "N/A"
    file_or_folder.short_description = "File/Folder"
    
    def duration(self, obj):
        if obj.completed_at and obj.started_at:
            duration = obj.completed_at - obj.started_at
            return str(duration).split('.')[0]  # Remove microseconds
        return "In progress" if obj.status == 'in_progress' else "N/A"
    duration.short_description = "Duration"


@admin.register(UserGoogleAuth)
class UserGoogleAuthAdmin(admin.ModelAdmin):
    list_display = ['user', 'scopes_display', 'is_expired_display', 'created_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['access_token', 'refresh_token', 'token_expiry', 'scopes']
    
    def scopes_display(self, obj):
        return ', '.join(obj.scopes) if obj.scopes else 'None'
    scopes_display.short_description = "Scopes"
    
    def is_expired_display(self, obj):
        expired = obj.is_expired()
        color = 'red' if expired else 'green'
        text = 'Expired' if expired else 'Valid'
        return format_html('<span style="color: {};">{}</span>', color, text)
    is_expired_display.short_description = "Token Status"
