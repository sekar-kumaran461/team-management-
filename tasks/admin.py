from django.contrib import admin
from django.contrib.auth.models import User
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    Task, TaskCategory, TaskSubmission, TaskFile, 
    TaskComment, TaskTemplate, TaskRecurringSelection
)
from analytics.models import UserActivity


@admin.register(TaskCategory)
class TaskCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'color', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'description']


class TaskFileInline(admin.TabularInline):
    model = TaskFile
    extra = 0
    readonly_fields = ['file_size', 'mime_type', 'uploaded_at']
    fields = ['filename', 'file_type', 'uploaded_by', 'file_size', 'description']


class TaskSubmissionInline(admin.TabularInline):
    model = TaskSubmission
    extra = 0
    readonly_fields = ['submitted_at', 'submitted_by']
    fields = ['title', 'submission_type', 'submitted_by', 'submitted_at', 'is_reviewed', 'grade']


class TaskCommentInline(admin.TabularInline):
    model = TaskComment
    extra = 0
    readonly_fields = ['created_at']
    fields = ['user', 'comment', 'created_at']


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'status_badge', 'priority_badge', 'assigned_to_display', 
        'category', 'due_date', 'progress_bar', 'created_at'
    ]
    list_filter = [
        'status', 'priority', 'category', 'assigned_to_all', 
        'is_recurring', 'is_template', 'recurrence_type',
        'created_at', 'due_date'
    ]
    search_fields = ['title', 'description', 'assigned_to__username', 'created_by__username']
    readonly_fields = ['created_at', 'updated_at', 'progress_display']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'category', 'tags')
        }),
        ('Assignment & Scheduling', {
            'fields': (
                'assigned_to', 'assigned_to_all', 'created_by',
                'due_date', 'estimated_hours', 'priority'
            )
        }),
        ('Recurring Task Settings', {
            'fields': (
                'is_recurring', 'is_template', 'recurrence_type', 'recurrence_days',
                'allow_member_selection', 'max_assignees', 'template_task', 'instance_date'
            ),
            'classes': ('collapse',)
        }),
        ('Task Details', {
            'fields': (
                'requirements', 'acceptance_criteria', 'deliverables',
                'status', 'progress_percentage'
            )
        }),
        ('Advanced Options', {
            'fields': ('parent_task', 'project'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    inlines = [TaskFileInline, TaskSubmissionInline, TaskCommentInline]
    
    # Custom actions
    actions = ['mark_as_pending', 'mark_as_in_progress', 'mark_as_completed', 'assign_to_all_students']
    
    def status_badge(self, obj):
        colors = {
            'pending': '#fbbf24',  # yellow
            'in_progress': '#3b82f6',  # blue
            'completed': '#10b981',  # green
            'cancelled': '#ef4444',  # red
            'review': '#8b5cf6'  # purple
        }
        color = colors.get(obj.status, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 12px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def priority_badge(self, obj):
        colors = {
            'low': '#10b981',  # green
            'medium': '#f59e0b',  # amber
            'high': '#ef4444',  # red
            'urgent': '#dc2626'  # red-600
        }
        color = colors.get(obj.priority, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 12px;">{}</span>',
            color,
            obj.get_priority_display()
        )
    priority_badge.short_description = 'Priority'
    
    def assigned_to_display(self, obj):
        if obj.assigned_to:
            return obj.assigned_to.get_full_name() or obj.assigned_to.username
        elif obj.assigned_to_all:
            return "All Students"
        else:
            return format_html('<span style="color: #6b7280;">Unassigned</span>')
    assigned_to_display.short_description = 'Assigned To'
    
    def progress_bar(self, obj):
        percentage = obj.progress_percentage or 0
        color = '#10b981' if percentage == 100 else '#3b82f6' if percentage >= 50 else '#f59e0b'
        return format_html(
            '<div style="width: 100px; background-color: #e5e7eb; border-radius: 4px; overflow: hidden;">'
            '<div style="width: {}%; height: 8px; background-color: {}; border-radius: 4px;"></div>'
            '</div>'
            '<span style="font-size: 11px; margin-left: 8px;">{}%</span>',
            percentage, color, percentage
        )
    progress_bar.short_description = 'Progress'
    
    def progress_display(self, obj):
        return self.progress_bar(obj)
    progress_display.short_description = 'Progress'
    
    # Custom actions
    def mark_as_pending(self, request, queryset):
        queryset.update(status='pending')
        self.message_user(request, f'{queryset.count()} tasks marked as pending.')
    mark_as_pending.short_description = 'Mark selected tasks as pending'
    
    def mark_as_in_progress(self, request, queryset):
        queryset.update(status='in_progress')
        self.message_user(request, f'{queryset.count()} tasks marked as in progress.')
    mark_as_in_progress.short_description = 'Mark selected tasks as in progress'
    
    def mark_as_completed(self, request, queryset):
        queryset.update(status='completed', progress_percentage=100)
        self.message_user(request, f'{queryset.count()} tasks marked as completed.')
    mark_as_completed.short_description = 'Mark selected tasks as completed'
    
    def assign_to_all_students(self, request, queryset):
        queryset.update(assigned_to_all=True, assigned_to=None)
        self.message_user(request, f'{queryset.count()} tasks assigned to all students.')
    assign_to_all_students.short_description = 'Assign selected tasks to all students'


@admin.register(TaskSubmission)
class TaskSubmissionAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'task_link', 'submission_type_badge', 'submitted_by', 
        'submitted_at', 'review_status', 'grade_display'
    ]
    list_filter = [
        'submission_type', 'is_reviewed', 'submitted_at', 
        'task__category', 'task__status'
    ]
    search_fields = [
        'title', 'description', 'submitted_by__username', 
        'task__title', 'external_url'
    ]
    readonly_fields = ['submitted_at']
    date_hierarchy = 'submitted_at'
    
    fieldsets = (
        ('Submission Information', {
            'fields': ('task', 'submitted_by', 'title', 'submission_type')
        }),
        ('Content', {
            'fields': ('description', 'file_path', 'external_url', 'notes')
        }),
        ('Review & Grading', {
            'fields': ('is_reviewed', 'reviewer', 'review_notes', 'grade', 'reviewed_at')
        }),
        ('Timestamps', {
            'fields': ('submitted_at',),
            'classes': ('collapse',)
        })
    )
    
    actions = ['mark_as_reviewed', 'mark_as_unreviewed']
    
    def task_link(self, obj):
        url = reverse('admin:tasks_task_change', args=[obj.task.id])
        return format_html('<a href="{}">{}</a>', url, obj.task.title)
    task_link.short_description = 'Task'
    
    def submission_type_badge(self, obj):
        colors = {
            'code': '#3b82f6',
            'document': '#10b981',
            'design': '#8b5cf6',
            'video': '#f59e0b',
            'link': '#ef4444',
            'other': '#6b7280'
        }
        color = colors.get(obj.submission_type, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 12px;">{}</span>',
            color,
            obj.get_submission_type_display()
        )
    submission_type_badge.short_description = 'Type'
    
    def review_status(self, obj):
        if obj.is_reviewed:
            return format_html(
                '<span style="background-color: #10b981; color: white; padding: 2px 8px; border-radius: 12px; font-size: 12px;">Reviewed</span>'
            )
        else:
            return format_html(
                '<span style="background-color: #f59e0b; color: white; padding: 2px 8px; border-radius: 12px; font-size: 12px;">Pending</span>'
            )
    review_status.short_description = 'Review Status'
    
    def grade_display(self, obj):
        if obj.grade is not None:
            color = '#10b981' if obj.grade >= 80 else '#f59e0b' if obj.grade >= 60 else '#ef4444'
            return format_html(
                '<span style="color: {}; font-weight: bold;">{}/100</span>',
                color, obj.grade
            )
        return '-'
    grade_display.short_description = 'Grade'
    
    def mark_as_reviewed(self, request, queryset):
        queryset.update(is_reviewed=True, reviewer=request.user)
        self.message_user(request, f'{queryset.count()} submissions marked as reviewed.')
    mark_as_reviewed.short_description = 'Mark selected submissions as reviewed'
    
    def mark_as_unreviewed(self, request, queryset):
        queryset.update(is_reviewed=False, reviewer=None)
        self.message_user(request, f'{queryset.count()} submissions marked as unreviewed.')
    mark_as_unreviewed.short_description = 'Mark selected submissions as unreviewed'


@admin.register(TaskFile)
class TaskFileAdmin(admin.ModelAdmin):
    list_display = [
        'filename', 'task_link', 'file_type_badge', 'file_size_display', 
        'uploaded_by', 'uploaded_at'
    ]
    list_filter = ['file_type', 'uploaded_at', 'task__category']
    search_fields = ['filename', 'original_filename', 'description', 'task__title']
    readonly_fields = ['uploaded_at', 'file_size', 'mime_type']
    
    def task_link(self, obj):
        url = reverse('admin:tasks_task_change', args=[obj.task.id])
        return format_html('<a href="{}">{}</a>', url, obj.task.title)
    task_link.short_description = 'Task'
    
    def file_type_badge(self, obj):
        colors = {
            'document': '#10b981',
            'image': '#8b5cf6',
            'video': '#f59e0b',
            'audio': '#ef4444',
            'archive': '#6b7280',
            'code': '#3b82f6',
            'other': '#9ca3af'
        }
        color = colors.get(obj.file_type, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 12px;">{}</span>',
            color,
            obj.get_file_type_display()
        )
    file_type_badge.short_description = 'Type'
    
    def file_size_display(self, obj):
        if obj.file_size:
            if obj.file_size < 1024:
                return f'{obj.file_size} B'
            elif obj.file_size < 1024 * 1024:
                return f'{obj.file_size / 1024:.1f} KB'
            else:
                return f'{obj.file_size / (1024 * 1024):.1f} MB'
        return '-'
    file_size_display.short_description = 'Size'


@admin.register(TaskComment)
class TaskCommentAdmin(admin.ModelAdmin):
    list_display = ['task_link', 'user', 'comment_preview', 'created_at']
    list_filter = ['created_at', 'task__category', 'task__status']
    search_fields = ['comment', 'user__username', 'task__title']
    readonly_fields = ['created_at']
    
    def task_link(self, obj):
        url = reverse('admin:tasks_task_change', args=[obj.task.id])
        return format_html('<a href="{}">{}</a>', url, obj.task.title)
    task_link.short_description = 'Task'
    
    def comment_preview(self, obj):
        return obj.comment[:50] + '...' if len(obj.comment) > 50 else obj.comment
    comment_preview.short_description = 'Comment'


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ['user', 'activity_type_badge', 'description_preview', 'timestamp']
    list_filter = ['activity_type', 'timestamp']
    search_fields = ['user__username', 'description', 'activity_type']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'
    
    def activity_type_badge(self, obj):
        colors = {
            'task_create': '#10b981',
            'task_update': '#3b82f6',
            'task_complete': '#8b5cf6',
            'task_submit': '#f59e0b',
            'file_upload': '#ef4444',
            'comment_add': '#6b7280'
        }
        color = colors.get(obj.activity_type, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 12px;">{}</span>',
            color,
            obj.activity_type.replace('_', ' ').title()
        )
    activity_type_badge.short_description = 'Activity Type'
    
    def description_preview(self, obj):
        return obj.description[:60] + '...' if len(obj.description) > 60 else obj.description
    description_preview.short_description = 'Description'


@admin.register(TaskTemplate)
class TaskTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'created_at']
    list_filter = ['category', 'created_at']


@admin.register(TaskRecurringSelection)
class TaskRecurringSelectionAdmin(admin.ModelAdmin):
    list_display = ['user', 'task_template', 'selection_type', 'selected_days', 'is_active', 'selected_at']
    list_filter = ['selection_type', 'is_active', 'selected_at']
    search_fields = ['user__username', 'task_template__title']
    readonly_fields = ['selected_at', 'updated_at']
    
    fieldsets = (
        ('Selection Details', {
            'fields': ('user', 'task_template', 'selection_type', 'selected_days', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('selected_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    search_fields = ['name', 'description']


# Custom admin site configuration
admin.site.site_header = "TeamLearn Administration"
admin.site.site_title = "TeamLearn Admin"
admin.site.index_title = "Welcome to TeamLearn Administration"
