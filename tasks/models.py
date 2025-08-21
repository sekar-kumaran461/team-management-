from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from datetime import timedelta
import uuid

User = get_user_model()


class TaskCategory(models.Model):
    """Categories for organizing tasks"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default='#007cba', help_text="Hex color code")
    icon = models.CharField(max_length=50, blank=True, help_text="Font Awesome icon class")
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'task_categories'
        verbose_name_plural = 'Task Categories'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Task(models.Model):
    """Comprehensive task model with advanced relationships instead of JSON fields"""
    
    STATUS_CHOICES = [
        ('todo', 'To Do'),
        ('in_progress', 'In Progress'),
        ('review', 'Under Review'),
        ('testing', 'Testing'),
        ('completed', 'Completed'),
        ('blocked', 'Blocked'),
        ('cancelled', 'Cancelled'),
        ('on_hold', 'On Hold'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
        ('critical', 'Critical'),
    ]
    
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
        ('expert', 'Expert'),
    ]
    
    TYPE_CHOICES = [
        ('feature', 'Feature Development'),
        ('bug', 'Bug Fix'),
        ('research', 'Research'),
        ('documentation', 'Documentation'),
        ('testing', 'Testing'),
        ('learning', 'Learning Task'),
        ('maintenance', 'Maintenance'),
        ('meeting', 'Meeting'),
        ('other', 'Other'),
    ]
    
    # Basic information
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(TaskCategory, on_delete=models.SET_NULL, null=True, blank=True)
    task_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='feature')
    
    # Status and priority
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='todo')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='medium')
    
    # Assignment and ownership
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_tasks')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tasks')
    reviewer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='review_tasks')
    # Flag to indicate if task is assigned to all users (learning tasks)
    assigned_to_all = models.BooleanField(default=False, help_text="If true, this task is visible and submittable by all users")
    
    # Time management
    estimated_hours = models.DecimalField(max_digits=6, decimal_places=2, default=1.0)
    actual_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0.0)
    due_date = models.DateTimeField(null=True, blank=True)
    start_date = models.DateTimeField(null=True, blank=True)
    completion_date = models.DateTimeField(null=True, blank=True)
    
    # Progress tracking
    progress_percentage = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    # Task relationships
    parent_task = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subtasks')
    dependencies = models.ManyToManyField('self', blank=True, symmetrical=False, related_name='dependent_tasks')
    
    # Advanced relationships instead of JSON fields
    tags = models.ManyToManyField('users.Tag', blank=True, related_name='tasks')
    required_skills = models.ManyToManyField('users.Skill', blank=True, related_name='tasks')
    technologies = models.ManyToManyField('users.Technology', blank=True, related_name='tasks')
    # reference_links = models.ManyToManyField('common.Reference', blank=True, related_name='tasks')
    
    # Additional metadata
    acceptance_criteria = models.TextField(blank=True, help_text="Criteria for task completion")
    blocking_reason = models.TextField(blank=True, help_text="Reason if task is blocked")
    
    # Gamification
    points_value = models.PositiveIntegerField(default=10, help_text="Points awarded upon completion")
    
    # Recurring task settings
    is_recurring = models.BooleanField(default=False, help_text="Whether this task repeats")
    recurrence_type = models.CharField(
        max_length=20,
        choices=[
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
            ('both', 'Both Daily and Weekly'),
        ],
        blank=True,
        null=True,
        help_text="How often this task repeats"
    )
    recurrence_days = models.CharField(
        max_length=20,
        blank=True,
        help_text="Days of week for weekly tasks (e.g., 'mon,wed,fri')"
    )
    is_template = models.BooleanField(default=False, help_text="Whether this is a template for recurring tasks")
    template_task = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='recurring_instances',
        help_text="The template task this instance was created from"
    )
    instance_date = models.DateField(
        null=True,
        blank=True,
        help_text="The date this recurring task instance is for"
    )
    
    # Team member selection for recurring tasks
    allow_member_selection = models.BooleanField(
        default=False,
        help_text="Allow team members to choose this recurring task"
    )
    max_assignees = models.PositiveIntegerField(
        default=1,
        help_text="Maximum number of team members who can take this recurring task"
    )
    
    # Bulk import tracking
    import_batch = models.CharField(max_length=100, blank=True, help_text="Batch ID for bulk imports")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'tasks'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['priority']),
            models.Index(fields=['assigned_to']),
            models.Index(fields=['due_date']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        # Auto-set completion date when status changes to completed
        if self.status == 'completed' and not self.completion_date:
            self.completion_date = timezone.now()
            self.progress_percentage = 100
        elif self.status != 'completed':
            self.completion_date = None
        
        # Auto-set start date when status changes from todo
        if self.status != 'todo' and not self.start_date:
            self.start_date = timezone.now()
        
        super().save(*args, **kwargs)
        
        # Award points if task is completed
        if self.status == 'completed' and self.assigned_to:
            self.assigned_to.add_points(self.points_value, f"Completed task: {self.title}")
    
    @property
    def is_overdue(self):
        """Check if task is overdue"""
        if not self.due_date or self.status == 'completed':
            return False
        return timezone.now() > self.due_date
    
    @property
    def time_spent(self):
        """Calculate total time spent on task"""
        return self.actual_hours
    
    @property
    def efficiency_ratio(self):
        """Calculate efficiency (estimated vs actual hours)"""
        if self.actual_hours == 0:
            return 0
        return float(self.estimated_hours) / float(self.actual_hours)
    
    def can_be_started(self):
        """Check if all dependencies are completed"""
        return not self.dependencies.exclude(status='completed').exists()
    
    def get_subtask_progress(self):
        """Calculate progress based on subtasks"""
        subtasks = self.subtasks.all()
        if not subtasks:
            return self.progress_percentage
        
        completed_subtasks = subtasks.filter(status='completed').count()
        return (completed_subtasks / subtasks.count()) * 100
    
    def get_progress_percentage(self):
        """Get the current progress percentage for the task"""
        if self.status == 'completed':
            return 100
        elif self.status == 'cancelled':
            return 0
        elif self.status == 'in_progress':
            # Calculate based on subtasks if available, otherwise use manual progress
            subtasks = self.subtasks.all()
            if subtasks:
                return self.get_subtask_progress()
            return max(self.progress_percentage, 10)  # At least 10% if in progress
        elif self.status == 'review':
            return max(self.progress_percentage, 80)  # At least 80% if under review
        else:
            return self.progress_percentage
    
    def create_recurring_instance(self, target_date, assigned_user=None):
        """Create a new instance of this recurring task for a specific date"""
        if not self.is_template:
            return None
            
        # Check if instance already exists for this date
        existing = Task.objects.filter(
            template_task=self,
            instance_date=target_date,
            assigned_to=assigned_user
        ).first()
        
        if existing:
            return existing
            
        # Create new instance
        instance = Task.objects.create(
            title=f"{self.title} - {target_date.strftime('%Y-%m-%d')}",
            description=self.description,
            category=self.category,
            task_type=self.task_type,
            priority=self.priority,
            difficulty=self.difficulty,
            created_by=self.created_by,
            assigned_to=assigned_user,
            estimated_hours=self.estimated_hours,
            points_value=self.points_value,
            acceptance_criteria=self.acceptance_criteria,
            is_recurring=False,
            is_template=False,
            template_task=self,
            instance_date=target_date,
            due_date=timezone.make_aware(
                timezone.datetime.combine(target_date, timezone.datetime.min.time().replace(hour=23, minute=59))
            ) if target_date else None,
        )
        
        # Copy relationships
        instance.tags.set(self.tags.all())
        instance.required_skills.set(self.required_skills.all())
        instance.technologies.set(self.technologies.all())
        
        return instance
    
    def get_available_recurring_tasks(self):
        """Get recurring tasks available for user selection"""
        return Task.objects.filter(
            is_template=True,
            is_recurring=True,
            allow_member_selection=True,
            status='todo'
        )
    
    @classmethod
    def generate_daily_tasks(cls, target_date=None):
        """Generate daily task instances for users who have selected them"""
        from datetime import date
        if target_date is None:
            target_date = date.today()
            
        # Get all daily recurring task templates
        daily_templates = cls.objects.filter(
            is_template=True,
            is_recurring=True,
            recurrence_type__in=['daily', 'both']
        )
        
        created_tasks = []
        for template in daily_templates:
            if template.allow_member_selection:
                # Get users who selected this daily task
                selections = TaskRecurringSelection.objects.filter(
                    task_template=template,
                    selection_type='daily',
                    is_active=True
                )
                
                for selection in selections:
                    task = template.create_recurring_instance(target_date, selection.user)
                    if task:
                        created_tasks.append(task)
            else:
                # Create for assigned user or all users
                if template.assigned_to:
                    task = template.create_recurring_instance(target_date, template.assigned_to)
                    if task:
                        created_tasks.append(task)
                elif template.assigned_to_all:
                    # Create separate instance for each active user
                    for user in User.objects.filter(is_active=True):
                        task = template.create_recurring_instance(target_date, user)
                        if task:
                            created_tasks.append(task)
        
        return created_tasks
    
    @classmethod
    def generate_weekly_tasks(cls, target_date=None):
        """Generate weekly task instances for users who have selected them"""
        from datetime import date
        if target_date is None:
            target_date = date.today()
            
        # Get day of week (0=Monday, 6=Sunday)
        weekday_names = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
        current_day = weekday_names[target_date.weekday()]
        
        # Get all weekly recurring task templates
        weekly_templates = cls.objects.filter(
            is_template=True,
            is_recurring=True,
            recurrence_type__in=['weekly', 'both']
        )
        
        created_tasks = []
        for template in weekly_templates:
            # Check if template should run on this day
            if template.recurrence_days and current_day not in template.recurrence_days.lower():
                continue
                
            if template.allow_member_selection:
                # Get users who selected this weekly task
                selections = TaskRecurringSelection.objects.filter(
                    task_template=template,
                    selection_type='weekly',
                    is_active=True
                )
                
                for selection in selections:
                    # Check if user selected this day
                    if selection.selected_days and current_day in selection.selected_days.lower():
                        task = template.create_recurring_instance(target_date, selection.user)
                        if task:
                            created_tasks.append(task)
            else:
                # Create for assigned user or all users
                if template.assigned_to:
                    task = template.create_recurring_instance(target_date, template.assigned_to)
                    if task:
                        created_tasks.append(task)
                elif template.assigned_to_all:
                    # Create separate instance for each active user
                    for user in User.objects.filter(is_active=True):
                        task = template.create_recurring_instance(target_date, user)
                        if task:
                            created_tasks.append(task)
        
        return created_tasks


class TaskTimeLog(models.Model):
    """Track time spent on tasks"""
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='time_logs')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='task_time_logs')
    
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    duration_minutes = models.PositiveIntegerField(default=0)
    description = models.TextField(blank=True, help_text="What was worked on during this time")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'task_time_logs'
        ordering = ['-start_time']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.task.title} ({self.duration_minutes}min)"
    
    def save(self, *args, **kwargs):
        # Auto-calculate duration if end_time is set
        if self.end_time and self.start_time:
            duration = self.end_time - self.start_time
            self.duration_minutes = int(duration.total_seconds() / 60)
        
        super().save(*args, **kwargs)
        
        # Update task's actual hours
        total_minutes = self.task.time_logs.aggregate(
            total=models.Sum('duration_minutes')
        )['total'] or 0
        self.task.actual_hours = total_minutes / 60
        self.task.save(update_fields=['actual_hours'])


class TaskComment(models.Model):
    """Comments and discussions on tasks"""
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='task_comments')
    
    content = models.TextField()
    is_internal = models.BooleanField(default=False, help_text="Internal team comment, not visible to clients")
    
    # Reply functionality
    parent_comment = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    
    # File attachments handled by TaskFile model with comment reference
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'task_comments'
        ordering = ['created_at']
    
    def __str__(self):
        return f"Comment by {self.user.get_full_name()} on {self.task.title}"


class TaskSubmission(models.Model):
    """Task submissions and deliverables"""
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='submissions')
    submitted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='task_submissions')
    
    SUBMISSION_TYPES = [
        ('code', 'Code/Repository'),
        ('document', 'Document'),
        ('design', 'Design Files'),
        ('video', 'Video Demo'),
        ('link', 'External Link'),
        ('other', 'Other'),
    ]
    
    submission_type = models.CharField(max_length=20, choices=SUBMISSION_TYPES, default='code')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Submission content
    file = models.FileField(upload_to='submissions/', blank=True, null=True)
    external_url = models.URLField(blank=True)
    notes = models.TextField(blank=True)
    
    # Review and grading
    is_reviewed = models.BooleanField(default=False)
    reviewer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_submissions')
    review_notes = models.TextField(blank=True)
    grade = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'task_submissions'
        ordering = ['-submitted_at']
    
    def __str__(self):
        return f"{self.title} - {self.task.title}"


class TaskTemplate(models.Model):
    """Reusable task templates with advanced structure"""
    name = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(TaskCategory, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Template relationships instead of JSON blob
    # template_data = models.OneToOneField('common.TemplateData', on_delete=models.CASCADE, related_name='task_template')
    
    # Usage tracking
    times_used = models.PositiveIntegerField(default=0)
    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_templates')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'task_templates'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def create_task_from_template(self, created_by, **kwargs):
        """Create a new task from this template"""
        template = self.template_data
        
        # Create task with template defaults
        task = Task.objects.create(
            title=template.title_template or self.name,
            description=template.description_template or self.description,
            created_by=created_by,
            priority=template.default_priority or 'medium',
            status=template.default_status or 'todo',
            estimated_hours=template.default_estimated_hours or 1.0,
            **kwargs
        )
        
        # Add related objects
        if template.default_tags.exists():
            task.tags.set(template.default_tags.all())
        if template.required_skills.exists():
            task.required_skills.set(template.required_skills.all())
        if template.recommended_technologies.exists():
            task.technologies.set(template.recommended_technologies.all())
        
        self.times_used += 1
        template.increment_usage()
        self.save(update_fields=['times_used'])
        
        return task


class TaskFile(models.Model):
    """File attachments for tasks with Google Drive integration"""
    
    FILE_TYPES = [
        ('image', 'Image'),
        ('document', 'Document'),
        ('video', 'Video'),
        ('audio', 'Audio'),
        ('archive', 'Archive'),
        ('code', 'Code File'),
        ('other', 'Other'),
    ]
    
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='files')
    comment = models.ForeignKey(TaskComment, on_delete=models.CASCADE, null=True, blank=True, related_name='attachments')
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploaded_task_files')
    
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
    
    # Local storage fallback
    local_file_path = models.CharField(max_length=500, blank=True)
    
    # File metadata
    description = models.TextField(blank=True)
    is_public = models.BooleanField(default=False, help_text="Whether file is publicly accessible")
    
    # Timestamps
    uploaded_at = models.DateTimeField(auto_now_add=True)
    last_accessed = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'task_files'
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['task', 'file_type']),
            models.Index(fields=['drive_file_id']),
        ]
    
    def __str__(self):
        return f"{self.filename} - {self.task.title}"
    
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
    def download_url(self):
        """Get the appropriate download URL"""
        if self.drive_file_url:
            return self.drive_file_url
        return self.local_file_path


class TaskFileAccess(models.Model):
    """Track file access for analytics"""
    task_file = models.ForeignKey(TaskFile, on_delete=models.CASCADE, related_name='access_logs')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='task_file_accesses')
    access_type = models.CharField(max_length=20, choices=[
        ('view', 'View'),
        ('download', 'Download'),
        ('edit', 'Edit'),
    ], default='view')
    accessed_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        db_table = 'task_file_access'
        ordering = ['-accessed_at']


class TaskFileVersion(models.Model):
    """Version control for task files"""
    task_file = models.ForeignKey(TaskFile, on_delete=models.CASCADE, related_name='versions')
    version_number = models.PositiveIntegerField()
    
    # Version-specific information
    drive_file_id = models.CharField(max_length=128, blank=True)
    file_size = models.PositiveIntegerField()
    upload_notes = models.TextField(blank=True)
    
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'task_file_versions'
        unique_together = ('task_file', 'version_number')
        ordering = ['-version_number']
    
    def __str__(self):
        return f"{self.task_file.filename} v{self.version_number}"


class TaskFileDriveSync(models.Model):
    """Track Google Drive sync status for task files"""
    task_file = models.OneToOneField(TaskFile, on_delete=models.CASCADE, related_name='drive_sync')
    
    last_synced = models.DateTimeField(auto_now=True)
    sync_success = models.BooleanField(default=True)
    sync_message = models.TextField(blank=True)
    retry_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        db_table = 'task_file_drive_sync'
    
    def __str__(self):
        status = "Success" if self.sync_success else "Failed"
        return f"Drive Sync for {self.task_file.filename}: {status}"


class BulkTaskUpload(models.Model):
    """Bulk task upload via CSV/Excel files"""
    
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
    file = models.FileField(upload_to='bulk_task_uploads/')
    original_filename = models.CharField(max_length=255)
    file_type = models.CharField(max_length=10, choices=FILE_TYPE_CHOICES, default='csv')
    file_size = models.PositiveIntegerField(help_text="File size in bytes")
    
    # Upload metadata
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bulk_task_uploads')
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
    skip_duplicates = models.BooleanField(default=True, help_text="Skip duplicate tasks based on title")
    default_category = models.ForeignKey(TaskCategory, on_delete=models.SET_NULL, null=True, blank=True)
    default_priority = models.CharField(max_length=20, choices=Task.PRIORITY_CHOICES, default='medium')
    
    class Meta:
        db_table = 'bulk_task_uploads'
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"Bulk Upload: {self.original_filename} ({self.status})"
    
    @property
    def success_rate(self):
        """Calculate success rate percentage"""
        if self.total_rows == 0:
            return 0
        return (self.successful_imports / self.total_rows) * 100


class TaskRecurringSelection(models.Model):
    """Track team member selections for recurring tasks"""
    
    SELECTION_TYPE_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recurring_task_selections')
    task_template = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='member_selections',
        help_text="The template task being selected"
    )
    selection_type = models.CharField(max_length=10, choices=SELECTION_TYPE_CHOICES)
    selected_days = models.CharField(
        max_length=20,
        blank=True,
        help_text="Days of week selected (e.g., 'mon,wed,fri')"
    )
    is_active = models.BooleanField(default=True)
    
    # Track when user opted in/out
    selected_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'task_recurring_selections'
        unique_together = ['user', 'task_template', 'selection_type']
        ordering = ['-selected_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.task_template.title} ({self.selection_type})"


class TaskFileUploadBatch(models.Model):
    """Batch upload for multiple task files"""
    
    BATCH_STATUS_CHOICES = [
        ('uploading', 'Uploading'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='file_upload_batches')
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='task_file_batches')
    
    batch_id = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=20, choices=BATCH_STATUS_CHOICES, default='uploading')
    
    total_files = models.PositiveIntegerField(default=0)
    uploaded_files = models.PositiveIntegerField(default=0)
    failed_files = models.PositiveIntegerField(default=0)
    
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    error_log = models.TextField(blank=True)
    
    class Meta:
        db_table = 'task_file_upload_batches'
        ordering = ['-started_at']
    
    def __str__(self):
        return f"File Batch for {self.task.title}: {self.uploaded_files}/{self.total_files}"
    
    @property
    def upload_progress(self):
        """Calculate upload progress percentage"""
        if self.total_files == 0:
            return 0
        return (self.uploaded_files / self.total_files) * 100


class TaskBulkOperation(models.Model):
    """Advanced bulk operations using OperationLog structure"""
    # operation_log = models.OneToOneField('common.OperationLog', on_delete=models.CASCADE, related_name='task_operation')
    
    # Task-specific operation data
    default_category = models.ForeignKey(TaskCategory, on_delete=models.SET_NULL, null=True, blank=True)
    default_priority = models.CharField(max_length=20, choices=Task.PRIORITY_CHOICES, default='medium')
    
    class Meta:
        db_table = 'task_bulk_operations'
        # ordering = ['-operation_log__started_at']
    
    def __str__(self):
        # return f"Task {self.operation_log.operation_name}: {self.operation_log.successful_items}/{self.operation_log.total_items}"
        return "Task Bulk Operation"


class TaskLabel(models.Model):
    """Labels/tags for tasks"""
    name = models.CharField(max_length=50, unique=True)
    color = models.CharField(max_length=7, default='#007cba')
    description = models.TextField(blank=True)
    
    tasks = models.ManyToManyField(Task, blank=True, related_name='labels')
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'task_labels'
        ordering = ['name']
    
    def __str__(self):
        return self.name
