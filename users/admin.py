from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User, UserProfile

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom User Admin with team management features"""
    
    list_display = ('email', 'full_name', 'role', 'is_active', 'total_points', 'date_joined')
    list_filter = ('role', 'is_active', 'date_joined')
    search_fields = ('email', 'first_name', 'last_name', 'username')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'phone', 'bio', 'profile_picture')}),
        ('Permissions', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Progress', {'fields': ('total_tasks_completed', 'total_resources_shared', 'total_points')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'first_name', 'last_name', 'role', 'password1', 'password2'),
        }),
    )
    
    readonly_fields = ('date_joined', 'last_login')
    
    def full_name(self, obj):
        return obj.full_name
    full_name.short_description = 'Full Name'
    
    actions = ['make_admin', 'make_member', 'activate_users', 'deactivate_users']
    
    def make_admin(self, request, queryset):
        queryset.update(role='admin')
        self.message_user(request, f"Successfully made {queryset.count()} users admins.")
    make_admin.short_description = "Make selected users admins"
    
    def make_member(self, request, queryset):
        queryset.update(role='member')
        self.message_user(request, f"Successfully made {queryset.count()} users members.")
    make_member.short_description = "Make selected users members"
    
    def activate_users(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f"Successfully activated {queryset.count()} users.")
    activate_users.short_description = "Activate selected users"
    
    def deactivate_users(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f"Successfully deactivated {queryset.count()} users.")
    deactivate_users.short_description = "Deactivate selected users"

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """User Profile Admin"""
    list_display = ('user', 'current_job_title', 'education_level')
    list_filter = ('education_level',)
    search_fields = ('user__email', 'user__full_name', 'current_job_title')
