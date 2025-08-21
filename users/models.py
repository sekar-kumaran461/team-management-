from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import uuid


class Tag(models.Model):
    """Centralized tag system for tasks, projects, and resources"""
    name = models.CharField(max_length=50, unique=True)
    color = models.CharField(max_length=7, default='#007cba')
    description = models.TextField(blank=True)
    category = models.CharField(max_length=50, choices=[
        ('priority', 'Priority'),
        ('status', 'Status'),
        ('technology', 'Technology'),
        ('skill', 'Skill'),
        ('topic', 'Topic'),
        ('general', 'General'),
    ], default='general')
    is_system = models.BooleanField(default=False, help_text="System-created tags")
    usage_count = models.PositiveIntegerField(default=0)
    created_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, blank=True, related_name='created_tags')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['category', 'name']
        indexes = [
            models.Index(fields=['category']),
            models.Index(fields=['name']),
        ]
    
    def __str__(self):
        return self.name
    
    def increment_usage(self):
        self.usage_count += 1
        self.save(update_fields=['usage_count'])


class Technology(models.Model):
    """Technology/Framework tracking"""
    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=50, choices=[
        ('language', 'Programming Language'),
        ('framework', 'Framework'),
        ('library', 'Library'),
        ('database', 'Database'),
        ('cloud', 'Cloud Platform'),
        ('tool', 'Development Tool'),
        ('platform', 'Platform'),
        ('other', 'Other'),
    ], default='other')
    version = models.CharField(max_length=50, blank=True)
    description = models.TextField(blank=True)
    official_url = models.URLField(blank=True)
    popularity_score = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['category', 'name']
        indexes = [
            models.Index(fields=['category']),
            models.Index(fields=['popularity_score']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"


class Skill(models.Model):
    """Skills model for better organization"""
    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=50, choices=[
        ('programming', 'Programming'),
        ('framework', 'Framework'),
        ('database', 'Database'),
        ('cloud', 'Cloud'),
        ('devops', 'DevOps'),
        ('design', 'Design'),
        ('soft_skill', 'Soft Skill'),
        ('other', 'Other'),
    ], default='other')
    description = models.TextField(blank=True)
    related_technologies = models.ManyToManyField(Technology, blank=True)
    difficulty_level = models.CharField(max_length=20, choices=[
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('expert', 'Expert'),
    ], default='beginner')
    icon = models.CharField(max_length=100, blank=True, help_text="Icon class or URL")
    color = models.CharField(max_length=7, default='#007cba')
    is_active = models.BooleanField(default=True)
    demand_score = models.PositiveIntegerField(default=0, help_text="Market demand score")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['category', 'name']
        indexes = [
            models.Index(fields=['category']),
            models.Index(fields=['demand_score']),
        ]
    
    def __str__(self):
        return self.name


class User(AbstractUser):
    """Custom User model with role-based permissions"""
    
    ROLE_CHOICES = [
        ('admin', 'Administrator'),
        ('team_lead', 'Team Lead'),
        ('member', 'Team Member'),
        ('mentor', 'Mentor'),
        ('guest', 'Guest'),
    ]
    
    SKILL_LEVELS = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('expert', 'Expert'),
    ]
    
    # Override username to make it optional and use email as primary
    username = models.CharField(max_length=150, unique=True, blank=True, null=True)
    email = models.EmailField(unique=True)
    
    # Role and permissions
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    is_team_lead = models.BooleanField(default=False)
    
    # Profile information
    full_name = models.CharField(max_length=200, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    github_username = models.CharField(max_length=100, blank=True)
    linkedin_profile = models.URLField(blank=True)
    portfolio_url = models.URLField(blank=True)
    
    # Advanced skill and goal management - replaced JSON fields with proper relationships
    skills = models.ManyToManyField('Skill', through='UserSkill', related_name='users')
    # learning_goals is now handled by the LearningGoal model with FK to User
    skill_level = models.CharField(max_length=20, choices=SKILL_LEVELS, default='beginner')
    years_of_experience = models.PositiveIntegerField(default=0)
    
    # Gamification
    total_points = models.PositiveIntegerField(default=0)
    level = models.PositiveIntegerField(default=1)
    badges_earned = models.PositiveIntegerField(default=0)
    
    # Activity tracking
    last_active = models.DateTimeField(auto_now=True)
    timezone = models.CharField(max_length=50, default='UTC')
    preferred_language = models.CharField(max_length=10, default='en')
    
    # Profile settings
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    is_profile_public = models.BooleanField(default=True)
    email_notifications = models.BooleanField(default=True)
    task_notifications = models.BooleanField(default=True)
    project_notifications = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username'] if username else []
    
    class Meta:
        db_table = 'users'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['role']),
            models.Index(fields=['is_active']),
            models.Index(fields=['total_points']),
        ]
    
    def __str__(self):
        return self.get_full_name() or self.email
    
    def get_full_name(self):
        return self.full_name or f"{self.first_name} {self.last_name}".strip()
    
    def get_role_display_formatted(self):
        return self.get_role_display().title()
    
    def add_points(self, points, reason=""):
        """Add points to user and update level"""
        self.total_points += points
        # Simple level calculation: every 1000 points = 1 level
        self.level = (self.total_points // 1000) + 1
        self.save()
        
        # Log the activity (will be imported later to avoid circular imports)
        try:
            from analytics.models import UserActivity
            UserActivity.objects.create(
                user=self,
                activity_type='points_earned',
                description=f"Earned {points} points: {reason}",
                points_earned=points
            )
        except ImportError:
            pass  # Analytics models not yet available
    
    def can_manage_users(self):
        """Check if user can manage other users"""
        return self.role in ['admin', 'team_lead']
    
    def can_create_projects(self):
        """Check if user can create projects"""
        return self.role in ['admin', 'team_lead', 'mentor']
    
    def can_assign_tasks(self):
        """Check if user can assign tasks to others"""
        return self.role in ['admin', 'team_lead']
    
    def can_manage_tasks(self):
        """Check if user can create, update, or delete tasks (admin only)"""
        return self.role == 'admin'


class UserProfile(models.Model):
    """Extended user profile information"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Education background
    education_level = models.CharField(max_length=50, blank=True)
    institution = models.CharField(max_length=200, blank=True)
    graduation_year = models.PositiveIntegerField(blank=True, null=True)
    field_of_study = models.CharField(max_length=100, blank=True)
    
    # Work experience
    current_job_title = models.CharField(max_length=100, blank=True)
    current_company = models.CharField(max_length=200, blank=True)
    work_experience_years = models.PositiveIntegerField(default=0)
    
    # Learning preferences
    preferred_learning_style = models.CharField(
        max_length=20,
        choices=[
            ('visual', 'Visual'),
            ('auditory', 'Auditory'),
            ('kinesthetic', 'Kinesthetic'),
            ('reading', 'Reading/Writing'),
        ],
        blank=True
    )
    
    study_hours_per_week = models.PositiveIntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(168)]
    )
    
    # Team preferences
    preferred_team_size = models.PositiveIntegerField(default=4)
    leadership_interest = models.BooleanField(default=False)
    mentoring_interest = models.BooleanField(default=False)
    
    # Additional information - replaced JSON fields with proper relationships
    interests = models.ManyToManyField('Tag', blank=True, related_name='interested_users')
    # achievements is now handled by the Achievement model with reverse FK
    certifications = models.ManyToManyField('Technology', blank=True, related_name='certified_users')
    
    # Emergency contact
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    emergency_contact_relationship = models.CharField(max_length=50, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_profiles'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.get_full_name()}'s Profile"


class UserSkill(models.Model):
    """Through model for user skills with proficiency levels"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    skill = models.ForeignKey('Skill', on_delete=models.CASCADE)
    proficiency_level = models.CharField(max_length=20, choices=[
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('expert', 'Expert'),
    ], default='beginner')
    years_experience = models.PositiveIntegerField(default=0)
    last_used = models.DateField(null=True, blank=True)
    is_primary = models.BooleanField(default=False, help_text="Primary skill for this user")
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'skill')
        ordering = ['-is_primary', '-proficiency_level', 'skill__name']
    
    def __str__(self):
        return f"{self.user.username} - {self.skill.name} ({self.proficiency_level})"


class LearningGoal(models.Model):
    """Learning goals model for structured goal tracking"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='learning_objectives')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    target_date = models.DateField(null=True, blank=True)
    priority = models.CharField(max_length=20, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ], default='medium')
    status = models.CharField(max_length=20, choices=[
        ('planned', 'Planned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('paused', 'Paused'),
        ('cancelled', 'Cancelled'),
    ], default='planned')
    progress_percentage = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    skills_to_learn = models.ManyToManyField('Skill', blank=True, related_name='learning_goals')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-priority', 'target_date']
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"


class Achievement(models.Model):
    """User achievements model for structured achievement tracking"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_achievements')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    achievement_type = models.CharField(max_length=50, choices=[
        ('certification', 'Certification'),
        ('project', 'Project Completion'),
        ('skill', 'Skill Mastery'),
        ('milestone', 'Milestone'),
        ('award', 'Award'),
        ('other', 'Other'),
    ], default='other')
    date_achieved = models.DateField()
    verification_url = models.URLField(blank=True)
    certificate_file = models.CharField(max_length=500, blank=True)  # Google Drive file ID
    skills_demonstrated = models.ManyToManyField('Skill', blank=True, related_name='achievements')
    points_awarded = models.PositiveIntegerField(default=0)
    is_verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_achievements')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date_achieved']
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"


class UserSettings(models.Model):
    """User application settings and preferences"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='settings')
    
    # Dashboard preferences
    dashboard_layout = models.CharField(
        max_length=20,
        choices=[
            ('grid', 'Grid Layout'),
            ('list', 'List Layout'),
            ('card', 'Card Layout'),
        ],
        default='grid'
    )
    
    items_per_page = models.PositiveIntegerField(default=20)
    dark_mode = models.BooleanField(default=False)
    sidebar_collapsed = models.BooleanField(default=False)
    
    # Notification preferences
    email_frequency = models.CharField(
        max_length=20,
        choices=[
            ('immediate', 'Immediate'),
            ('daily', 'Daily Digest'),
            ('weekly', 'Weekly Summary'),
            ('never', 'Never'),
        ],
        default='daily'
    )
    
    push_notifications = models.BooleanField(default=True)
    desktop_notifications = models.BooleanField(default=True)
    
    # Privacy settings
    profile_visibility = models.CharField(
        max_length=20,
        choices=[
            ('public', 'Public'),
            ('team_only', 'Team Members Only'),
            ('private', 'Private'),
        ],
        default='team_only'
    )
    
    show_email = models.BooleanField(default=False)
    show_phone = models.BooleanField(default=False)
    show_activity = models.BooleanField(default=True)
    
    # Google Drive integration
    google_drive_enabled = models.BooleanField(default=False)
    google_drive_folder_id = models.CharField(max_length=100, blank=True)
    auto_backup = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_settings'
    
    def __str__(self):
        return f"{self.user.get_full_name()}'s Settings"


class TeamMembership(models.Model):
    """Track team memberships and roles within teams"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='team_memberships')
    team_name = models.CharField(max_length=100)
    role_in_team = models.CharField(
        max_length=50,
        choices=[
            ('lead', 'Team Lead'),
            ('developer', 'Developer'),
            ('designer', 'Designer'),
            ('tester', 'Tester'),
            ('analyst', 'Business Analyst'),
            ('mentor', 'Mentor'),
        ]
    )
    
    joined_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    # Performance in this team
    tasks_completed = models.PositiveIntegerField(default=0)
    projects_contributed = models.PositiveIntegerField(default=0)
    team_rating = models.DecimalField(
        max_digits=3, 
        decimal_places=2, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    
    class Meta:
        db_table = 'team_memberships'
        unique_together = ('user', 'team_name')
        ordering = ['-joined_at']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.team_name} ({self.role_in_team})"
