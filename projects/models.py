from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import uuid

User = get_user_model()

class ProjectCategory(models.Model):
    """Categories for organizing projects"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)
    color = models.CharField(max_length=7, default='#007cba')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        db_table = 'project_categories'
        ordering = ['name']
    def __str__(self):
        return self.name

class Project(models.Model):
    """Main project model for team management"""
    STATUS_CHOICES = [
        ('planning', 'Planning'),
        ('in_progress', 'In Progress'),
        ('review', 'Under Review'),
        ('completed', 'Completed'),
        ('on_hold', 'On Hold'),
        ('cancelled', 'Cancelled'),
    ]
    DIFFICULTY_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('expert', 'Expert'),
    ]
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(ProjectCategory, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planning')
    difficulty_level = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='beginner')
    estimated_duration_weeks = models.IntegerField(default=1)
    project_manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_projects')
    team_members = models.ManyToManyField(User, related_name='assigned_projects', blank=True)
    # Advanced skill and technology management - replaced JSON fields
    required_skills = models.ManyToManyField('users.Skill', blank=True, related_name='required_projects')
    technologies = models.ManyToManyField('users.Technology', blank=True, related_name='projects')
    tags = models.ManyToManyField('users.Tag', blank=True, related_name='projects')
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    actual_start_date = models.DateField(null=True, blank=True)
    actual_end_date = models.DateField(null=True, blank=True)
    repository_url = models.URLField(blank=True, null=True)
    documentation_url = models.URLField(blank=True, null=True)
    demo_url = models.URLField(blank=True, null=True)
    progress_percentage = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        db_table = 'projects'
        ordering = ['-created_at']
    def __str__(self):
        return self.title

class ProjectMilestone(models.Model):
    """Project milestones/phases"""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='milestones')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    due_date = models.DateField()
    is_completed = models.BooleanField(default=False)
    completion_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        db_table = 'project_milestones'
        ordering = ['due_date']
    def __str__(self):
        return f"{self.project.title} - {self.title}"

# Temporarily commenting out ProjectTask to allow migrations
# class ProjectTask(models.Model):
#     """Tasks within a project"""
#     project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='project_tasks')
#     task = models.ForeignKey('tasks.Task', on_delete=models.CASCADE, related_name='project_tasks')
#     assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
#     assigned_at = models.DateTimeField(auto_now_add=True)
#     class Meta:
#         db_table = 'project_tasks'
#         unique_together = ('project', 'task')
#     def __str__(self):
#         return f"{self.project.title} - {self.task.title}"

class ProjectSubmission(models.Model):
    """Project submissions and deliverables"""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='submissions')
    submitted_by = models.ForeignKey(User, on_delete=models.CASCADE)
    submission_type = models.CharField(max_length=20, default='code')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    file_path = models.CharField(max_length=500, blank=True)
    external_url = models.URLField(blank=True)
    notes = models.TextField(blank=True)
    is_reviewed = models.BooleanField(default=False)
    reviewer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_project_submissions')
    review_notes = models.TextField(blank=True)
    grade = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(100)])
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    class Meta:
        db_table = 'project_submissions'
        ordering = ['-submitted_at']
    def __str__(self):
        return f"{self.title} - {self.project.title}"

class WeeklyProjectReview(models.Model):
    """Weekly review for project progress"""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='weekly_reviews')
    reviewer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    week_ending = models.DateField()
    accomplishments = models.TextField(blank=True)
    challenges = models.TextField(blank=True)
    progress_rating = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    submitted_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = 'weekly_project_reviews'
        ordering = ['-week_ending']
    def __str__(self):
        return f"{self.project.title} - Week ending {self.week_ending}"
