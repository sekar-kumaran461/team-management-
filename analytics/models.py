from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class UserActivity(models.Model):
    """Track user activities for analytics"""
    ACTIVITY_TYPES = [
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('task_created', 'Task Created'),
        ('task_completed', 'Task Completed'),
        ('project_created', 'Project Created'),
        ('project_completed', 'Project Completed'),
        ('points_earned', 'Points Earned'),
        ('badge_earned', 'Badge Earned'),
        ('resource_uploaded', 'Resource Uploaded'),
        ('resource_downloaded', 'Resource Downloaded'),
        ('other', 'Other'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=50, choices=ACTIVITY_TYPES)
    description = models.TextField(blank=True)
    points_earned = models.PositiveIntegerField(default=0)
    
    # Structured metadata fields instead of JSON
    related_object_id = models.PositiveIntegerField(null=True, blank=True, help_text="ID of related object (task, project, etc.)")
    related_object_type = models.CharField(max_length=50, blank=True, help_text="Type of related object")
    session_id = models.CharField(max_length=50, blank=True, help_text="User session identifier")
    ip_address = models.GenericIPAddressField(null=True, blank=True, help_text="User's IP address")
    user_agent = models.TextField(blank=True, help_text="User's browser information")
    additional_info = models.TextField(blank=True, help_text="Additional context information")
    
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'user_activities'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'activity_type']),
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.activity_type} at {self.timestamp}"