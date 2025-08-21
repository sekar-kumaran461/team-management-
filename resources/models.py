from django.db import models
from django.conf import settings
from users.models import User

class ResourceCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Resource(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.ForeignKey(ResourceCategory, on_delete=models.SET_NULL, null=True, related_name='resources')
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploaded_resources')
    file_url = models.URLField(blank=True, null=True)  # Google Drive file link
    drive_file_id = models.CharField(max_length=128, blank=True, null=True)  # Google Drive file ID
    is_public = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    tags = models.CharField(max_length=255, blank=True)
    likes = models.ManyToManyField(User, through='ResourceLike', related_name='liked_resources')
    downloads = models.ManyToManyField(User, through='ResourceDownload', related_name='downloaded_resources')

    def __str__(self):
        return self.title

class ResourceFile(models.Model):
    """File attachments for resources with Google Drive integration"""
    
    FILE_TYPES = [
        ('pdf', 'PDF Document'),
        ('image', 'Image'),
        ('video', 'Video'),
        ('audio', 'Audio'),
        ('document', 'Document'),
        ('spreadsheet', 'Spreadsheet'),
        ('presentation', 'Presentation'),
        ('archive', 'Archive'),
        ('code', 'Code File'),
        ('other', 'Other'),
    ]
    
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, related_name='files')
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploaded_resource_files')
    
    # File information
    filename = models.CharField(max_length=255)
    original_filename = models.CharField(max_length=255)
    file_type = models.CharField(max_length=20, choices=FILE_TYPES, default='other')
    file_size = models.PositiveIntegerField(help_text="File size in bytes")
    mime_type = models.CharField(max_length=100, blank=True)
    
    # Google Drive integration
    drive_file_id = models.CharField(max_length=128, unique=True, null=True, blank=True)
    drive_file_url = models.URLField(blank=True)
    drive_thumbnail_url = models.URLField(blank=True)
    drive_embed_url = models.URLField(blank=True)
    
    # Local storage fallback
    local_file_path = models.CharField(max_length=500, blank=True)
    
    # File metadata
    description = models.TextField(blank=True)
    is_public = models.BooleanField(default=True, help_text="Whether file is publicly accessible")
    is_featured = models.BooleanField(default=False, help_text="Featured file for the resource")
    
    # Download tracking
    download_count = models.PositiveIntegerField(default=0)
    view_count = models.PositiveIntegerField(default=0)
    
    # Timestamps
    uploaded_at = models.DateTimeField(auto_now_add=True)
    last_accessed = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'resource_files'
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['resource', 'file_type']),
            models.Index(fields=['drive_file_id']),
            models.Index(fields=['is_public']),
        ]
    
    def __str__(self):
        return f"{self.filename} - {self.resource.title}"
    
    @property
    def file_size_formatted(self):
        """Return human-readable file size"""
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    
    @property
    def is_image(self):
        """Check if file is an image"""
        return self.file_type == 'image'
    
    @property
    def is_video(self):
        """Check if file is a video"""
        return self.file_type == 'video'
    
    @property
    def can_preview(self):
        """Check if file can be previewed"""
        return self.file_type in ['pdf', 'image', 'video', 'document', 'spreadsheet', 'presentation']
    
    @property
    def download_url(self):
        """Get the appropriate download URL"""
        if self.drive_file_url:
            return self.drive_file_url
        return self.local_file_path

class ResourceFileAccess(models.Model):
    """Track file access for analytics"""
    resource_file = models.ForeignKey(ResourceFile, on_delete=models.CASCADE, related_name='access_logs')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='resource_file_accesses')
    access_type = models.CharField(max_length=20, choices=[
        ('view', 'View'),
        ('download', 'Download'),
        ('preview', 'Preview'),
        ('share', 'Share'),
    ], default='view')
    accessed_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        db_table = 'resource_file_access'
        ordering = ['-accessed_at']

class StudyMaterial(models.Model):
    resource = models.OneToOneField(Resource, on_delete=models.CASCADE, related_name='study_material')
    notes = models.TextField(blank=True)
    summary = models.TextField(blank=True)
    reference_links = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class ResourceComment(models.Model):
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_resolved = models.BooleanField(default=False)

class ResourceLike(models.Model):
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('resource', 'user')

class ResourceDownload(models.Model):
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    downloaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('resource', 'user')

class BulkResourceUpload(models.Model):
    """Enhanced bulk resource upload with Excel/CSV support"""
    
    UPLOAD_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('partial', 'Partially Completed'),
    ]
    
    FILE_TYPE_CHOICES = [
        ('csv', 'CSV File'),
        ('excel', 'Excel File (.xlsx)'),
        ('json', 'JSON File'),
    ]
    
    # File information
    file = models.FileField(upload_to='bulk_resource_uploads/')
    original_filename = models.CharField(max_length=255)
    file_type = models.CharField(max_length=10, choices=FILE_TYPE_CHOICES, default='csv')
    file_size = models.PositiveIntegerField(help_text="File size in bytes")
    
    # Upload metadata
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bulk_resource_uploads')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    # Processing status
    status = models.CharField(max_length=20, choices=UPLOAD_STATUS_CHOICES, default='pending')
    processed_at = models.DateTimeField(null=True, blank=True)
    
    # Results
    total_rows = models.PositiveIntegerField(default=0)
    successful_imports = models.PositiveIntegerField(default=0)
    failed_imports = models.PositiveIntegerField(default=0)
    error_log = models.TextField(blank=True)
    success_log = models.TextField(blank=True)
    
    # Batch tracking
    batch_id = models.CharField(max_length=100, unique=True, help_text="Unique batch identifier")
    
    # Processing options
    skip_duplicates = models.BooleanField(default=True, help_text="Skip duplicate resources based on title")
    default_category = models.ForeignKey(ResourceCategory, on_delete=models.SET_NULL, null=True, blank=True)
    make_public = models.BooleanField(default=True, help_text="Make imported resources public by default")
    
    class Meta:
        db_table = 'bulk_resource_uploads'
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"Bulk Resource Upload: {self.original_filename} ({self.status})"
    
    @property
    def success_rate(self):
        """Calculate success rate percentage"""
        if self.total_rows == 0:
            return 0
        return (self.successful_imports / self.total_rows) * 100


class ResourceFileUploadBatch(models.Model):
    """Batch upload for multiple resource files"""
    
    BATCH_STATUS_CHOICES = [
        ('uploading', 'Uploading'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, related_name='file_upload_batches')
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='resource_file_batches')
    
    batch_id = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=20, choices=BATCH_STATUS_CHOICES, default='uploading')
    
    total_files = models.PositiveIntegerField(default=0)
    uploaded_files = models.PositiveIntegerField(default=0)
    failed_files = models.PositiveIntegerField(default=0)
    
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    error_log = models.TextField(blank=True)
    
    # Upload options
    make_files_public = models.BooleanField(default=True)
    auto_generate_thumbnails = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'resource_file_upload_batches'
        ordering = ['-started_at']
    
    def __str__(self):
        return f"File Batch for {self.resource.title}: {self.uploaded_files}/{self.total_files}"
    
    @property
    def upload_progress(self):
        """Calculate upload progress percentage"""
        if self.total_files == 0:
            return 0
        return (self.uploaded_files / self.total_files) * 100


class ResourceBulkOperation(models.Model):
    """Advanced bulk operations using OperationLog structure"""
    # operation_log = models.OneToOneField('common.OperationLog', on_delete=models.CASCADE, related_name='resource_operation')
    
    # Resource-specific operation data
    default_category = models.ForeignKey(ResourceCategory, on_delete=models.SET_NULL, null=True, blank=True)
    make_public = models.BooleanField(default=True, help_text="Make resources public by default")
    
    class Meta:
        db_table = 'resource_bulk_operations'
        # ordering = ['-operation_log__started_at']
    
    def __str__(self):
        # return f"Resource {self.operation_log.operation_name}: {self.operation_log.successful_items}/{self.operation_log.total_items}"
        return "Resource Bulk Operation"

class GoogleDriveSyncStatus(models.Model):
    resource = models.OneToOneField(Resource, on_delete=models.CASCADE, related_name='drive_sync_status')
    last_synced = models.DateTimeField(auto_now=True)
    sync_success = models.BooleanField(default=True)
    sync_message = models.TextField(blank=True)

    def __str__(self):
        return f"Drive Sync for {self.resource.title}: {'Success' if self.sync_success else 'Failed'}"

class ResourceFileVersion(models.Model):
    """Version control for resource files"""
    resource_file = models.ForeignKey(ResourceFile, on_delete=models.CASCADE, related_name='versions')
    version_number = models.PositiveIntegerField()
    
    # Version-specific information
    drive_file_id = models.CharField(max_length=128, blank=True)
    file_size = models.PositiveIntegerField()
    upload_notes = models.TextField(blank=True)
    
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'resource_file_versions'
        unique_together = ('resource_file', 'version_number')
        ordering = ['-version_number']
    
    def __str__(self):
        return f"{self.resource_file.filename} v{self.version_number}"

class ResourceFileDriveSync(models.Model):
    """Track Google Drive sync status for resource files"""
    resource_file = models.OneToOneField(ResourceFile, on_delete=models.CASCADE, related_name='drive_sync')
    
    last_synced = models.DateTimeField(auto_now=True)
    sync_success = models.BooleanField(default=True)
    sync_message = models.TextField(blank=True)
    retry_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        db_table = 'resource_file_drive_sync'
    
    def __str__(self):
        status = "Success" if self.sync_success else "Failed"
        return f"Drive Sync for {self.resource_file.filename}: {status}"
