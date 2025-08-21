from django.contrib.admin.views.decorators import staff_member_required
# Admin file preview view
from django.http import Http404
@staff_member_required
def admin_view_file(request, submission_id):
    submission = get_object_or_404(TaskSubmission, id=submission_id)
    if not submission.file_path:
        raise Http404("No file uploaded for this submission.")
    # Only allow admin access
    if not request.user.is_staff and not getattr(request.user, 'is_admin', False):
        raise PermissionDenied()
    from django.conf import settings
    return render(request, 'admin/view_file.html', {
        'submission': submission,
        'MEDIA_URL': settings.MEDIA_URL,
    })
# Admin file preview view
from django.http import Http404
@staff_member_required
def admin_view_file(request, submission_id):
    submission = get_object_or_404(TaskSubmission, id=submission_id)
    if not submission.file_path:
        raise Http404("No file uploaded for this submission.")
    # Only allow admin access
    if not request.user.is_staff and not getattr(request.user, 'is_admin', False):
        raise PermissionDenied()
    return render(request, 'admin/view_file.html', {
        'submission': submission,
        'file_url': submission.file_path,
    })
from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from users.models import User
from django.core.mail import send_mail
# Admin view to review all task submissions
@staff_member_required
def task_submissions_admin(request):
    submissions = TaskSubmission.objects.select_related('task', 'submitted_by').order_by('-submitted_at')
    # Filtering (by user, status, date)
    user_id = request.GET.get('user')
    status = request.GET.get('status')
    if user_id:
        submissions = submissions.filter(submitted_by_id=user_id)
    if status:
        submissions = submissions.filter(task__status=status)
    paginator = Paginator(submissions, 20)
    page = request.GET.get('page')
    submissions_page = paginator.get_page(page)
    users = User.objects.all()
    return render(request, 'admin/task_submissions.html', {
        'submissions': submissions_page,
        'users': users,
        'status_choices': Task.STATUS_CHOICES,
    })
import json
import csv
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False
from datetime import datetime, timedelta
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.db.models import Q, Count, Avg, Sum, F, Case, When, Value, IntegerField
from django.http import JsonResponse, HttpResponse, Http404, HttpResponseNotAllowed
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.conf import settings
import uuid
import os
from io import BytesIO

from .models import (
    Task, TaskCategory, TaskFile, TaskComment, TaskSubmission, 
    BulkTaskUpload, TaskTimeLog, TaskTemplate, TaskLabel,
    TaskFileUploadBatch, TaskFileAccess
)
from .forms import TaskCreateForm, TaskFileUploadForm, TaskSubmissionForm
from users.models import User
from analytics.models import UserActivity
from google_integration.services import GoogleDriveService


class TaskListView(LoginRequiredMixin, ListView):
    """Advanced task list view with filtering, sorting, and search"""
    model = Task
    template_name = 'tasks/task_list.html'
    context_object_name = 'tasks'
    paginate_by = 25

    def get_queryset(self):
        queryset = Task.objects.select_related(
            'category', 'assigned_to', 'created_by', 'reviewer'
        ).prefetch_related(
            'tags', 'required_skills', 'technologies', 'comments', 'files'
        )

        # Team management visibility logic
        user = self.request.user
        
        # Base visibility: tasks visible to user
        visibility_filter = Q()
        
        # 1. Tasks assigned to the user
        visibility_filter |= Q(assigned_to=user)
        
        # 2. Tasks created by the user
        visibility_filter |= Q(created_by=user)
        
        # 3. Tasks where user is reviewer
        visibility_filter |= Q(reviewer=user)
        
        # 4. Tasks with assigned_to_all=True (public tasks)
        visibility_filter |= Q(assigned_to_all=True)
        
        # 5. Tasks created by administrators (visible to all by default)
        admin_users = User.objects.filter(
            Q(is_superuser=True) | 
            Q(groups__name='Admin') |
            Q(is_staff=True)
        )
        visibility_filter |= Q(created_by__in=admin_users)
        
        # 6. Tasks in user's team projects (if user has team memberships)
        if hasattr(user, 'team_memberships') and user.team_memberships.exists():
            team_names = user.team_memberships.values_list('team_name', flat=True)
            # Find projects associated with these teams (by project title or team assignments)
            from projects.models import Project
            team_projects = Project.objects.filter(
                Q(title__in=team_names) |
                Q(team_members__in=[user])
            ).values_list('id', flat=True)
            if team_projects:
                visibility_filter |= Q(project_id__in=team_projects)
        
        # Apply the visibility filter unless user is admin
        if not (user.is_superuser or user.groups.filter(name='Admin').exists()):
            queryset = queryset.filter(visibility_filter).distinct()

        # Search functionality
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(tags__name__icontains=search_query) |
                Q(category__name__icontains=search_query)
            ).distinct()

        # Filter by status
        status_filter = self.request.GET.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # Filter by priority
        priority_filter = self.request.GET.get('priority')
        if priority_filter:
            queryset = queryset.filter(priority=priority_filter)

        # Filter by category
        category_filter = self.request.GET.get('category')
        if category_filter:
            queryset = queryset.filter(category_id=category_filter)

        # Filter by assigned user
        assigned_filter = self.request.GET.get('assigned_to')
        if assigned_filter:
            queryset = queryset.filter(assigned_to_id=assigned_filter)

        # Filter by due date
        due_filter = self.request.GET.get('due_date')
        if due_filter:
            today = timezone.now().date()
            if due_filter == 'overdue':
                queryset = queryset.filter(due_date__lt=today, status__in=['todo', 'in_progress'])
            elif due_filter == 'today':
                queryset = queryset.filter(due_date=today)
            elif due_filter == 'this_week':
                week_end = today + timedelta(days=7)
                queryset = queryset.filter(due_date__range=[today, week_end])

        # Sorting
        sort_by = self.request.GET.get('sort', '-created_at')
        if sort_by in ['title', '-title', 'due_date', '-due_date', 'priority', '-priority', 
                       'status', '-status', 'created_at', '-created_at', 'progress_percentage', '-progress_percentage']:
            queryset = queryset.order_by(sort_by)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add filter options
        context['categories'] = TaskCategory.objects.all()
        context['users'] = User.objects.filter(is_active=True)
        context['status_choices'] = Task.STATUS_CHOICES
        context['priority_choices'] = Task.PRIORITY_CHOICES
        
        # Current filter values
        context['current_filters'] = {
            'search': self.request.GET.get('search', ''),
            'status': self.request.GET.get('status', ''),
            'priority': self.request.GET.get('priority', ''),
            'category': self.request.GET.get('category', ''),
            'assigned_to': self.request.GET.get('assigned_to', ''),
            'due_date': self.request.GET.get('due_date', ''),
            'sort': self.request.GET.get('sort', '-created_at'),
        }

        # Task statistics
        tasks = self.get_queryset()
        context['task_stats'] = {
            'total': tasks.count(),
            'todo': tasks.filter(status='todo').count(),
            'in_progress': tasks.filter(status='in_progress').count(),
            'completed': tasks.filter(status='completed').count(),
            'overdue': tasks.filter(
                due_date__lt=timezone.now().date(),
                status__in=['todo', 'in_progress']
            ).count(),
        }

        # User's task summary - focus on team management
        user_tasks = tasks.filter(
            Q(assigned_to=self.request.user) | 
            Q(created_by=self.request.user)
        )
        context['my_task_stats'] = {
            'total_assigned': tasks.filter(assigned_to=self.request.user).count(),
            'total_created': tasks.filter(created_by=self.request.user).count(),
            'pending_review': tasks.filter(
                created_by=self.request.user, 
                status='review'
            ).count(),
            'team_collaboration': tasks.filter(
                assigned_to_all=True,
                status__in=['todo', 'in_progress']
            ).count(),
        }

        # Team insights
        context['team_insights'] = {
            'public_tasks': tasks.filter(assigned_to_all=True).count(),
            'admin_created': tasks.filter(
                created_by__in=User.objects.filter(
                    Q(is_superuser=True) | Q(groups__name='Admin')
                )
            ).count(),
            'team_tasks': tasks.filter(assigned_to__isnull=False).count(),
        }

        return context


class TaskDetailView(LoginRequiredMixin, DetailView):
    """Comprehensive task detail view with comments, files, and submissions"""
    model = Task
    template_name = 'tasks/task_detail.html'
    context_object_name = 'task'

    def get_queryset(self):
        return Task.objects.select_related(
            'category', 'assigned_to', 'created_by', 'reviewer', 'parent_task'
        ).prefetch_related(
            'tags', 'required_skills', 'technologies', 'subtasks',
            'comments__user', 'files__uploaded_by', 'submissions__submitted_by',
            'time_logs__user', 'dependencies', 'dependent_tasks'
        )

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        
        # Temporarily commented out permission check for debugging
        # # Check permissions
        # user = self.request.user
        # if not self.can_view_task(user, obj):
        #     raise PermissionDenied("You don't have permission to view this task.")
        
        # # Log task view activity
        # UserActivity.objects.create(
        #     user=user,
        #     activity_type='other',  # 'task_view' is not in the choices
        #     description=f"Viewed task: {obj.title}",
        #     related_object_id=obj.id,
        #     related_object_type='task',
        #     additional_info=f"Task: {obj.title}"
        # )
        
        return obj

    def can_view_task(self, user, task):
        """Team management visibility rules"""
        if user.is_superuser:
            return True
        
        # Task assignee, creator, or reviewer can always view
        if task.assigned_to == user or task.created_by == user or task.reviewer == user:
            return True
        
        # Public tasks (assigned_to_all=True) are visible to everyone
        if task.assigned_to_all:
            return True
        
        # Tasks created by administrators are visible to all by default
        admin_users = User.objects.filter(
            Q(is_superuser=True) | 
            Q(groups__name='Admin') |
            Q(is_staff=True)
        )
        if task.created_by in admin_users:
            return True
        
        # Team-based visibility (if user is in same team/project)
        if hasattr(task, 'project') and hasattr(user, 'team_memberships'):
            user_projects = user.team_memberships.values_list('project_id', flat=True)
            if task.project_id in user_projects:
                return True
        
        # Department/category-based visibility for team leads
        if user.groups.filter(name__in=['Team Lead', 'Manager']).exists():
            if hasattr(user, 'managed_categories'):
                return task.category in user.managed_categories.all()
        
        return False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        task = self.object
        user = self.request.user

        # Add today's date for template comparisons
        context['today'] = timezone.now().date()

        # Submissions (check if submissions model exists)
        try:
            context['submissions'] = task.submissions.select_related(
                'submitted_by'
            ).order_by('-submitted_at')
        except:
            context['submissions'] = []

        # User's submission if exists
        try:
            context['user_submission'] = task.submissions.filter(
                submitted_by=user
            ).first()
        except:
            context['user_submission'] = None

        # Time logs and progress
        try:
            from django.db.models import Sum
            context['time_logs'] = task.time_logs.select_related('user').order_by('-start_time')
            context['total_time_spent'] = task.time_logs.aggregate(
                total=Sum('duration_minutes')
            )['total'] or 0
        except:
            context['time_logs'] = []
            context['total_time_spent'] = 0

        # Progress data
        context['progress_data'] = self.get_task_progress_data(task)

        # Basic permissions
        context['can_edit'] = self.can_edit_task(user, task)
        context['can_submit'] = self.can_submit_task(user, task)
        context['can_review'] = self.can_review_task(user, task)
        context['can_manage_visibility'] = self.can_manage_visibility(user, task)
        context['can_assign_team'] = self.can_assign_team(user, task)
        context['can_clone_task'] = self.can_clone_task(user, task)

        return context

    def build_comment_tree(self, comments):
        """Build hierarchical comment structure"""
        comment_dict = {}
        root_comments = []

        for comment in comments:
            comment_dict[comment.id] = comment
            comment.replies = []

        for comment in comments:
            if comment.parent_comment_id:
                parent = comment_dict.get(comment.parent_comment_id)
                if parent:
                    parent.replies.append(comment)
            else:
                root_comments.append(comment)

        return root_comments

    def get_task_progress_data(self, task):
        """Get comprehensive progress data for task"""
        data = {
            'progress_percentage': task.progress_percentage,
            'estimated_hours': float(task.estimated_hours),
            'actual_hours': float(task.actual_hours),
            'efficiency_ratio': task.efficiency_ratio,
            'is_overdue': task.is_overdue,
            'days_remaining': None,
            'subtask_progress': task.get_subtask_progress(),
        }

        if task.due_date:
            days_remaining = (task.due_date.date() - timezone.now().date()).days
            data['days_remaining'] = days_remaining

        return data

    def can_edit_task(self, user, task):
        """Team management edit permissions"""
        return (user == task.created_by or 
                user == task.assigned_to or 
                user.groups.filter(name__in=['Admin', 'Manager', 'Team Lead']).exists())

    def can_submit_task(self, user, task):
        """Team management submission permissions"""
        return (user == task.assigned_to or 
                (task.assigned_to_all and user.is_authenticated) or
                user.groups.filter(name__in=['Team Member', 'Contributor']).exists())

    def can_review_task(self, user, task):
        """Team management review permissions"""
        return (user == task.reviewer or 
                user == task.created_by or
                user.groups.filter(name__in=['Admin', 'Manager', 'Team Lead', 'Senior Developer']).exists())

    def can_manage_visibility(self, user, task):
        """Check if user can manage task visibility"""
        return (user == task.created_by or 
                user.groups.filter(name__in=['Admin', 'Manager']).exists())

    def can_assign_team(self, user, task):
        """Check if user can assign team members to task"""
        return (user == task.created_by or 
                user.groups.filter(name__in=['Admin', 'Manager', 'Team Lead']).exists())

    def can_clone_task(self, user, task):
        """Check if user can clone the task"""
        return (self.can_view_task(user, task) and 
                user.groups.filter(name__in=['Admin', 'Manager', 'Team Lead', 'Senior Developer']).exists())


class TaskCreateView(LoginRequiredMixin, CreateView):
    """Advanced task creation with file upload and templates"""
    model = Task
    form_class = TaskCreateForm
    template_name = 'tasks/task_create.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['templates'] = TaskTemplate.objects.filter(
            created_by=self.request.user
        ).order_by('name')
        return context

    def form_valid(self, form):
        # Set the creator
        form.instance.created_by = self.request.user

        # Team management: Auto-set visibility for admin-created tasks
        if self.request.user.groups.filter(name__in=['Admin', 'Manager']).exists():
            if not form.cleaned_data.get('assigned_to'):
                form.instance.assigned_to_all = True  # Admin tasks visible to all by default

        # Generate batch ID for bulk operations
        if not form.instance.import_batch:
            form.instance.import_batch = str(uuid.uuid4())[:8]

        # Save the task
        response = super().form_valid(form)
        task = self.object

        # Handle file uploads
        files = self.request.FILES.getlist('files')
        if files:
            self.handle_file_uploads(task, files)

        # Create initial activity log
        UserActivity.objects.create(
            user=self.request.user,
            activity_type='task_create',
            description=f"Created task: {task.title}",
            metadata={
                'task_id': task.id,
                'task_title': task.title,
                'category': task.category.name if task.category else None
            }
        )

        messages.success(
            self.request, 
            f'Task "{task.title}" created successfully with {len(files)} files attached.'
        )
        return response

    def handle_file_uploads(self, task, files):
        """Handle multiple file uploads for task"""
        batch_id = str(uuid.uuid4())
        drive_service = GoogleDriveService()

        # Create upload batch
        batch = TaskFileUploadBatch.objects.create(
            task=task,
            uploaded_by=self.request.user,
            batch_id=batch_id,
            total_files=len(files),
            status='uploading'
        )

        uploaded_count = 0
        for file in files:
            try:
                # Determine file type
                file_type = self.determine_file_type(file.name)
                
                # Upload to Google Drive if configured
                drive_file_id = None
                drive_url = None
                if hasattr(settings, 'GOOGLE_DRIVE_ENABLED') and settings.GOOGLE_DRIVE_ENABLED:
                    try:
                        drive_result = drive_service.upload_file(
                            file, 
                            f"tasks/{task.id}/",
                            description=f"File for task: {task.title}"
                        )
                        drive_file_id = drive_result.get('id')
                        drive_url = drive_result.get('webViewLink')
                    except Exception as e:
                        print(f"Drive upload failed: {e}")

                # Create TaskFile record
                task_file = TaskFile.objects.create(
                    task=task,
                    uploaded_by=self.request.user,
                    filename=file.name,
                    original_filename=file.name,
                    file_type=file_type,
                    file_size=file.size,
                    mime_type=file.content_type,
                    drive_file_id=drive_file_id,
                    drive_file_url=drive_url,
                    local_file_path=f"task_files/{task.id}/{file.name}",
                )

                # Save file locally as backup
                self.save_file_locally(file, task_file.local_file_path)
                uploaded_count += 1

            except Exception as e:
                batch.error_log += f"Failed to upload {file.name}: {str(e)}\n"
                batch.failed_files += 1

        # Update batch status
        batch.uploaded_files = uploaded_count
        batch.status = 'completed' if uploaded_count == len(files) else 'partial'
        batch.completed_at = timezone.now()
        batch.save()

    def determine_file_type(self, filename):
        """Determine file type based on extension"""
        ext = filename.lower().split('.')[-1]
        
        if ext in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg']:
            return 'image'
        elif ext in ['pdf', 'doc', 'docx', 'txt', 'rtf']:
            return 'document'
        elif ext in ['mp4', 'avi', 'mov', 'wmv', 'flv']:
            return 'video'
        elif ext in ['mp3', 'wav', 'aac', 'flac']:
            return 'audio'
        elif ext in ['zip', 'rar', '7z', 'tar', 'gz']:
            return 'archive'
        elif ext in ['py', 'js', 'html', 'css', 'java', 'cpp', 'c', 'php']:
            return 'code'
        else:
            return 'other'

    def save_file_locally(self, file, file_path):
        """Save file to local storage as backup"""
        full_path = os.path.join(settings.MEDIA_ROOT, file_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        with open(full_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)

    def get_success_url(self):
        return reverse('tasks:task-detail', kwargs={'pk': self.object.pk})


class TaskEditView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Advanced task editing with change tracking"""
    model = Task
    form_class = TaskCreateForm
    template_name = 'tasks/task_edit.html'

    def test_func(self):
        task = self.get_object()
        user = self.request.user
        return (user == task.created_by or 
                user == task.assigned_to or 
                user.groups.filter(name__in=['Teacher', 'Admin']).exists())

    def form_valid(self, form):
        # Track changes
        old_task = Task.objects.get(pk=self.object.pk)
        changes = self.track_changes(old_task, form.instance)

        response = super().form_valid(form)

        # Log changes
        if changes:
            UserActivity.objects.create(
                user=self.request.user,
                activity_type='task_update',
                description=f"Updated task: {self.object.title}",
                metadata={
                    'task_id': self.object.id,
                    'changes': changes
                }
            )

        messages.success(self.request, f'Task "{self.object.title}" updated successfully.')
        return response

    def track_changes(self, old_task, new_task):
        """Track what fields were changed"""
        changes = {}
        fields_to_track = [
            'title', 'description', 'status', 'priority', 'due_date',
            'assigned_to', 'estimated_hours', 'progress_percentage'
        ]

        for field in fields_to_track:
            old_value = getattr(old_task, field)
            new_value = getattr(new_task, field)
            if old_value != new_value:
                changes[field] = {
                    'old': str(old_value),
                    'new': str(new_value)
                }

        return changes

    def get_success_url(self):
        return reverse('tasks:task-detail', kwargs={'pk': self.object.pk})


class TaskDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Task deletion with confirmation"""
    model = Task
    template_name = 'tasks/task_delete.html'
    success_url = reverse_lazy('tasks:task-list')

    def test_func(self):
        task = self.get_object()
        user = self.request.user
        return (user == task.created_by or 
                user.groups.filter(name__in=['Admin']).exists())

    def delete(self, request, *args, **kwargs):
        task = self.get_object()
        
        # Log deletion
        UserActivity.objects.create(
            user=request.user,
            activity_type='task_delete',
            description=f"Deleted task: {task.title}",
            metadata={
                'task_id': task.id,
                'task_title': task.title
            }
        )

        messages.success(request, f'Task "{task.title}" deleted successfully.')
        return super().delete(request, *args, **kwargs)


class BulkTaskUploadView(LoginRequiredMixin, CreateView):
    """Advanced bulk task upload with CSV/Excel support"""
    model = BulkTaskUpload
    fields = ['file', 'file_type', 'default_category', 'default_priority', 'skip_duplicates']
    template_name = 'tasks/bulk_upload.html'
    success_url = reverse_lazy('tasks:task-list')

    def form_valid(self, form):
        form.instance.uploaded_by = self.request.user
        form.instance.batch_id = str(uuid.uuid4())[:12]
        form.instance.original_filename = form.instance.file.name
        form.instance.file_size = form.instance.file.size

        response = super().form_valid(form)
        
        # Process the file asynchronously (or synchronously for demo)
        self.process_bulk_upload(self.object)

        messages.success(
            self.request, 
            f'Bulk upload started. Check back in a few minutes for results.'
        )
        return response

    def process_bulk_upload(self, upload):
        """Process the uploaded file and create tasks"""
        try:
            upload.status = 'processing'
            upload.save()

            if upload.file_type == 'csv':
                tasks_data = self.read_csv_file(upload.file)
            elif upload.file_type == 'excel':
                tasks_data = self.read_excel_file(upload.file)
            else:
                raise ValueError("Unsupported file type")

            upload.total_rows = len(tasks_data)
            upload.save()

            success_count = 0
            error_messages = []
            success_messages = []

            for row_num, task_data in enumerate(tasks_data, 1):
                try:
                    task = self.create_task_from_row(task_data, upload)
                    success_count += 1
                    success_messages.append(f"Row {row_num}: Created task '{task.title}'")
                except Exception as e:
                    error_messages.append(f"Row {row_num}: {str(e)}")

            upload.successful_imports = success_count
            upload.failed_imports = len(tasks_data) - success_count
            upload.error_log = '\n'.join(error_messages)
            upload.success_log = '\n'.join(success_messages)
            upload.status = 'completed' if error_messages == [] else 'partial'
            upload.processed_at = timezone.now()
            upload.save()

        except Exception as e:
            upload.status = 'failed'
            upload.error_log = str(e)
            upload.processed_at = timezone.now()
            upload.save()

    def read_csv_file(self, file):
        """Read CSV file and return task data"""
        file.seek(0)
        decoded_file = file.read().decode('utf-8')
        reader = csv.DictReader(decoded_file.splitlines())
        return list(reader)

    def read_excel_file(self, file):
        """Read Excel file and return task data"""
        if not HAS_PANDAS:
            raise ValueError("Excel files require pandas. Please install pandas or use CSV format.")
        file.seek(0)
        df = pd.read_excel(file)
        return df.to_dict('records')

    def create_task_from_row(self, row_data, upload):
        """Create a task from a row of data"""
        # Map CSV columns to task fields
        title = row_data.get('title') or row_data.get('Title')
        if not title:
            raise ValueError("Title is required")

        # Check for duplicates if enabled
        if upload.skip_duplicates and Task.objects.filter(title=title).exists():
            raise ValueError(f"Task with title '{title}' already exists")

        # Parse other fields
        description = row_data.get('description', '')
        priority = row_data.get('priority', upload.default_priority)
        estimated_hours = float(row_data.get('estimated_hours', 1.0))
        
        # Parse due date
        due_date = None
        due_date_str = row_data.get('due_date')
        if due_date_str:
            try:
                due_date = parse_datetime(due_date_str)
            except:
                pass

        # Get or create category
        category = upload.default_category
        category_name = row_data.get('category')
        if category_name:
            category, _ = TaskCategory.objects.get_or_create(
                name=category_name,
                defaults={'description': f'Auto-created from bulk upload'}
            )

        # Create the task
        task = Task.objects.create(
            title=title,
            description=description,
            category=category,
            priority=priority,
            estimated_hours=estimated_hours,
            due_date=due_date,
            created_by=upload.uploaded_by,
            import_batch=upload.batch_id,
            assigned_to_all=True  # Bulk uploaded tasks are usually for all students
        )

        return task

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = TaskCategory.objects.all()
        context['recent_uploads'] = BulkTaskUpload.objects.filter(
            uploaded_by=self.request.user
        ).order_by('-uploaded_at')[:5]
        return context


@login_required
def submit_task(request, task_id):
    """Handle task submission with files and external links"""
    task = get_object_or_404(Task, id=task_id)
    
    # Check permissions - allow submission if:
    # 1. User is assigned to the task
    # 2. Task is assigned to all students and user is a student
    # 3. Task is unassigned (anyone can submit)
    if not (request.user == task.assigned_to or 
            (task.assigned_to_all and request.user.groups.filter(name='Student').exists()) or
            task.assigned_to is None):
        raise PermissionDenied("You cannot submit to this task.")

    if request.method == 'POST':
        # For inline submissions, we'll handle files separately since they're not part of the form
        form_data = request.POST.copy()
        form_files = request.FILES.copy()
        
        # Remove file from FILES for form validation if it exists
        if 'file' in form_files:
            form_files.pop('file')
            
        form = TaskSubmissionForm(form_data, form_files)
        if form.is_valid():
            submission = form.save(commit=False)
            submission.task = task
            submission.submitted_by = request.user
            submission.save()

            # Handle file uploads - check for both single file and multiple files
            files = []
            
            # Check for single file upload (inline form)
            if 'file' in request.FILES:
                files.append(request.FILES['file'])
            
            # Check for multiple file upload (separate form)
            if 'submission_files' in request.FILES:
                files.extend(request.FILES.getlist('submission_files'))
            
            uploaded_files = []
            
            for file in files:
                # Save file to media directory
                import os
                from django.core.files.storage import default_storage
                from django.core.files.base import ContentFile
                
                # Create submission directory
                submission_dir = f"submissions/{task.id}/{submission.id}/"
                os.makedirs(os.path.join(settings.MEDIA_ROOT, submission_dir), exist_ok=True)
                
                # Save file
                file_path = default_storage.save(
                    f"{submission_dir}{file.name}",
                    ContentFile(file.read())
                )
                
                # Create TaskFile record
                task_file = TaskFile.objects.create(
                    task=task,
                    uploaded_by=request.user,
                    filename=file.name,
                    original_filename=file.name,
                    file_type=get_file_type_from_extension(file.name),
                    file_size=file.size,
                    mime_type=file.content_type,
                    local_file_path=file_path,
                    description=f"Submission file for: {submission.title}"
                )
                uploaded_files.append(task_file)

            # Update submission with file if files were uploaded
            if uploaded_files:
                # Save the first file to the submission's file field
                if 'file' in request.FILES:
                    submission.file = request.FILES['file']
                elif 'submission_files' in request.FILES:
                    submission.file = request.FILES.getlist('submission_files')[0]
                    
                submission.save()

            # Update task status and progress based on completion
            completion_percentage = request.POST.get('completion_percentage')
            if completion_percentage:
                task.progress_percentage = int(completion_percentage)
                
                # Update status based on progress
                if int(completion_percentage) == 100:
                    task.status = 'review'
                elif int(completion_percentage) >= 75:
                    task.status = 'in_progress'
                elif int(completion_percentage) >= 25:
                    task.status = 'in_progress'
                
                task.save()

            # Log activity
            UserActivity.objects.create(
                user=request.user,
                activity_type='task_submit',
                description=f"Submitted solution for task: {task.title} | Submission ID: {submission.id} | Files: {len(uploaded_files)} | External URL: {bool(submission.external_url)} | Completion: {completion_percentage}",
                related_object_id=submission.id,
                related_object_type='TaskSubmission'
            )

            messages.success(request, f'Task submitted successfully! {len(uploaded_files)} file(s) uploaded.')
            
            # Check if this is an inline submission from task detail page
            if request.POST.get('inline_submission'):
                return redirect('tasks:task-detail', pk=task.id)
            else:
                return redirect('tasks:task-detail', pk=task.id)
        else:
            messages.error(request, 'Please correct the errors below.')
            
            # If this is an inline submission with errors, redirect back to task detail
            if request.POST.get('inline_submission'):
                return redirect('tasks:task-detail', pk=task.id)
    else:
        # Check if this is an inline request (shouldn't happen, but handle gracefully)
        if request.GET.get('inline'):
            return redirect('tasks:task-detail', pk=task.id)
        
        form = TaskSubmissionForm()

    return render(request, 'tasks/submit_task.html', {
        'task': task,
        'form': form
    })


def get_file_type_from_extension(filename):
    """Determine file type from extension"""
    ext = filename.split('.')[-1].lower() if '.' in filename else ''
    type_mapping = {
        'pdf': 'document',
        'doc': 'document', 'docx': 'document', 'txt': 'document',
        'py': 'code', 'js': 'code', 'html': 'code', 'css': 'code', 'java': 'code', 'cpp': 'code', 'c': 'code',
        'png': 'image', 'jpg': 'image', 'jpeg': 'image', 'gif': 'image',
        'zip': 'archive', 'rar': 'archive',
        'mp4': 'video', 'avi': 'video', 'mov': 'video'
    }
    return type_mapping.get(ext, 'other')


@login_required
def task_progress(request, task_id):
    """Update task progress"""
    task = get_object_or_404(Task, id=task_id)
    
    # Check permissions
    if not (request.user == task.assigned_to or 
            request.user == task.created_by or
            request.user.groups.filter(name__in=['Teacher', 'Admin']).exists()):
        return JsonResponse({'error': 'Permission denied'}, status=403)

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            new_progress = int(data.get('progress', 0))
            
            if 0 <= new_progress <= 100:
                task.progress_percentage = new_progress
                
                # Auto-update status based on progress
                if new_progress == 0:
                    task.status = 'todo'
                elif new_progress == 100:
                    task.status = 'completed'
                    task.completion_date = timezone.now()
                elif task.status == 'todo':
                    task.status = 'in_progress'
                    task.start_date = timezone.now()
                
                task.save()

                # Log activity
                UserActivity.objects.create(
                    user=request.user,
                    activity_type='task_progress_update',
                    description=f"Updated progress for task: {task.title} to {new_progress}%",
                    metadata={
                        'task_id': task.id,
                        'old_progress': task.progress_percentage,
                        'new_progress': new_progress
                    }
                )

                return JsonResponse({
                    'success': True,
                    'progress': new_progress,
                    'status': task.status
                })
            else:
                return JsonResponse({'error': 'Invalid progress value'}, status=400)
                
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Invalid request method'}, status=405)


@login_required
def my_tasks(request):
    """Team member's personal task dashboard"""
    user = request.user
    
    # Get user's tasks with team management focus
    assigned_tasks = Task.objects.filter(assigned_to=user)
    created_tasks = Task.objects.filter(created_by=user)
    public_tasks = Task.objects.filter(assigned_to_all=True)
    
    # Admin-created tasks visible to all
    admin_tasks = Task.objects.filter(
        created_by__in=User.objects.filter(
            Q(is_superuser=True) | Q(groups__name='Admin')
        )
    ).exclude(assigned_to=user).exclude(created_by=user)
    
    # Combine all visible tasks
    all_tasks = (assigned_tasks | created_tasks | public_tasks | admin_tasks).distinct()
    
    # Apply additional filters
    status_filter = request.GET.get('status')
    if status_filter:
        all_tasks = all_tasks.filter(status=status_filter)

    # Team management statistics
    stats = {
        'assigned_to_me': assigned_tasks.count(),
        'created_by_me': created_tasks.count(),
        'public_tasks': public_tasks.count(),
        'admin_tasks': admin_tasks.count(),
        'pending_my_review': Task.objects.filter(reviewer=user, status='review').count(),
        'overdue_assigned': assigned_tasks.filter(
            due_date__lt=timezone.now().date(),
            status__in=['todo', 'in_progress']
        ).count(),
    }

    # Recent activity and upcoming deadlines
    recent_tasks = all_tasks.order_by('-updated_at')[:5]
    
    # Upcoming deadlines
    upcoming_deadlines = all_tasks.filter(
        due_date__gte=timezone.now().date(),
        status__in=['todo', 'in_progress']
    ).order_by('due_date')[:5]

    # Time tracking
    total_time_this_week = TaskTimeLog.objects.filter(
        user=user,
        start_time__gte=timezone.now().date() - timedelta(days=7)
    ).aggregate(total=Sum('duration_minutes'))['total'] or 0

    context = {
        'all_tasks': all_tasks,
        'assigned_tasks': assigned_tasks,
        'created_tasks': created_tasks,
        'public_tasks': public_tasks,
        'admin_tasks': admin_tasks,
        'stats': stats,
        'recent_tasks': recent_tasks,
        'upcoming_deadlines': upcoming_deadlines,
        'total_time_this_week': total_time_this_week / 60,  # Convert to hours
        'status_choices': Task.STATUS_CHOICES,
        'current_status': status_filter
    }

    return render(request, 'tasks/my_tasks.html', context)


@login_required
def my_submissions(request):
    """User's submission history"""
    user = request.user
    
    submissions = TaskSubmission.objects.filter(
        submitted_by=user
    ).select_related('task', 'reviewer').order_by('-submitted_at')

    # Pagination
    paginator = Paginator(submissions, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Statistics
    stats = {
        'total': submissions.count(),
        'pending_review': submissions.filter(is_reviewed=False).count(),
        'reviewed': submissions.filter(is_reviewed=True).count(),
        'average_grade': submissions.filter(grade__isnull=False).aggregate(
            avg=Avg('grade')
        )['avg'] or 0,
    }

    context = {
        'submissions': page_obj,
        'stats': stats,
        'page_obj': page_obj
    }

    return render(request, 'tasks/my_submissions.html', context)


@login_required
def export_tasks(request):
    """Export tasks to CSV"""
    # Get tasks based on user permissions
    user = request.user
    tasks = Task.objects.select_related('category', 'assigned_to', 'created_by')
    
    if user.groups.filter(name='Student').exists():
        tasks = tasks.filter(Q(assigned_to=user) | Q(assigned_to_all=True))
    elif user.groups.filter(name='Teacher').exists():
        tasks = tasks.filter(
            Q(category__in=user.teachable_categories.all()) |
            Q(assigned_to=user) |
            Q(created_by=user)
        )

    # Apply filters
    status_filter = request.GET.get('status')
    if status_filter:
        tasks = tasks.filter(status=status_filter)

    category_filter = request.GET.get('category')
    if category_filter:
        tasks = tasks.filter(category_id=category_filter)

    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="tasks_export_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'ID', 'Title', 'Description', 'Category', 'Status', 'Priority',
        'Assigned To', 'Created By', 'Due Date', 'Progress', 'Estimated Hours',
        'Actual Hours', 'Created At', 'Updated At'
    ])

    for task in tasks:
        writer.writerow([
            task.id,
            task.title,
            task.description,
            task.category.name if task.category else '',
            task.get_status_display(),
            task.get_priority_display(),
            task.assigned_to.get_full_name() if task.assigned_to else 'All Students',
            task.created_by.get_full_name(),
            task.due_date.strftime('%Y-%m-%d %H:%M') if task.due_date else '',
            f"{task.progress_percentage}%",
            task.estimated_hours,
            task.actual_hours,
            task.created_at.strftime('%Y-%m-%d %H:%M'),
            task.updated_at.strftime('%Y-%m-%d %H:%M')
        ])

    return response


@login_required
def task_calendar(request):
    """Calendar view of tasks"""
    user = request.user
    
    # Get tasks with due dates
    tasks = Task.objects.filter(due_date__isnull=False)
    
    # Apply user permissions
    if user.groups.filter(name='Student').exists():
        tasks = tasks.filter(Q(assigned_to=user) | Q(assigned_to_all=True))
    elif user.groups.filter(name='Teacher').exists():
        tasks = tasks.filter(
            Q(category__in=user.teachable_categories.all()) |
            Q(assigned_to=user) |
            Q(created_by=user)
        )

    # Get date range for calendar (current month by default)
    today = timezone.now().date()
    start_date = request.GET.get('start', today.replace(day=1))
    end_date = request.GET.get('end', (today.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1))

    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

    # Filter tasks by date range
    tasks_in_range = tasks.filter(
        due_date__date__range=[start_date, end_date]
    ).select_related('category', 'assigned_to')

    # Format tasks for calendar
    calendar_events = []
    for task in tasks_in_range:
        calendar_events.append({
            'id': task.id,
            'title': task.title,
            'start': task.due_date.isoformat(),
            'url': reverse('tasks:task-detail', kwargs={'pk': task.id}),
            'color': get_task_color(task),
            'description': task.description[:100] + '...' if len(task.description) > 100 else task.description,
            'status': task.status,
            'priority': task.priority,
            'progress': task.progress_percentage
        })

    context = {
        'calendar_events': json.dumps(calendar_events),
        'start_date': start_date,
        'end_date': end_date,
        'current_month': today.strftime('%Y-%m')
    }

    return render(request, 'tasks/task_calendar.html', context)


def get_task_color(task):
    """Get color for task based on status and priority"""
    if task.status == 'completed':
        return '#10B981'  # Green
    elif task.status == 'in_progress':
        return '#F59E0B'  # Yellow
    elif task.status == 'review':
        return '#8B5CF6'  # Purple
    elif task.is_overdue:
        return '#EF4444'  # Red
    elif task.priority in ['high', 'urgent', 'critical']:
        return '#F97316'  # Orange
    else:
        return '#6B7280'  # Gray


# API Views for AJAX calls

@login_required
@require_http_methods(["POST"])
def add_comment(request, task_id):
    """Add comment to task via AJAX"""
    task = get_object_or_404(Task, id=task_id)
    
    try:
        data = json.loads(request.body)
        content = data.get('content', '').strip()
        parent_id = data.get('parent_id')
        
        if not content:
            return JsonResponse({'error': 'Comment cannot be empty'}, status=400)

        parent_comment = None
        if parent_id:
            parent_comment = TaskComment.objects.get(id=parent_id, task=task)

        comment = TaskComment.objects.create(
            task=task,
            user=request.user,
            content=content,
            parent_comment=parent_comment
        )

        return JsonResponse({
            'success': True,
            'comment': {
                'id': comment.id,
                'content': comment.content,
                'user': comment.user.get_full_name(),
                'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M'),
                'parent_id': comment.parent_comment_id
            }
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
def task_stats_api(request):
    """Get task statistics for dashboard"""
    user = request.user
    
    # Base queryset based on user permissions
    if user.groups.filter(name='Student').exists():
        tasks = Task.objects.filter(Q(assigned_to=user) | Q(assigned_to_all=True))
    elif user.groups.filter(name='Teacher').exists():
        tasks = Task.objects.filter(
            Q(category__in=user.teachable_categories.all()) |
            Q(assigned_to=user) |
            Q(created_by=user)
        )
    else:
        tasks = Task.objects.all()

    # Calculate statistics
    stats = {
        'total_tasks': tasks.count(),
        'completed_tasks': tasks.filter(status='completed').count(),
        'in_progress_tasks': tasks.filter(status='in_progress').count(),
        'overdue_tasks': tasks.filter(
            due_date__lt=timezone.now().date(),
            status__in=['todo', 'in_progress']
        ).count(),
        'tasks_by_priority': {
            priority[0]: tasks.filter(priority=priority[0]).count()
            for priority in Task.PRIORITY_CHOICES
        },
        'tasks_by_status': {
            status[0]: tasks.filter(status=status[0]).count()
            for status in Task.STATUS_CHOICES
        },
        'completion_rate': 0
    }

    if stats['total_tasks'] > 0:
        stats['completion_rate'] = round(
            (stats['completed_tasks'] / stats['total_tasks']) * 100, 2
        )

    return JsonResponse(stats)


@login_required
def search_tasks_api(request):
    """Search tasks via AJAX"""
    query = request.GET.get('q', '').strip()
    
    if len(query) < 3:
        return JsonResponse({'results': []})

    user = request.user
    tasks = Task.objects.select_related('category', 'assigned_to')

    # Apply user permissions
    if user.groups.filter(name='Student').exists():
        tasks = tasks.filter(Q(assigned_to=user) | Q(assigned_to_all=True))
    elif user.groups.filter(name='Teacher').exists():
        tasks = tasks.filter(
            Q(category__in=user.teachable_categories.all()) |
            Q(assigned_to=user) |
            Q(created_by=user)
        )

    # Search
    tasks = tasks.filter(
        Q(title__icontains=query) |
        Q(description__icontains=query)
    )[:10]

    results = []
    for task in tasks:
        results.append({
            'id': task.id,
            'title': task.title,
            'description': task.description[:100] + '...' if len(task.description) > 100 else task.description,
            'status': task.get_status_display(),
            'priority': task.get_priority_display(),
            'url': reverse('tasks:task-detail', kwargs={'pk': task.id})
        })

    return JsonResponse({'results': results})


# Utility functions for the views

def get_user_task_permissions(user, task):
    """Get user permissions for a specific task"""
    permissions = {
        'can_view': False,
        'can_edit': False,
        'can_delete': False,
        'can_submit': False,
        'can_review': False,
        'can_comment': False,
        'can_manage_visibility': False,
        'can_assign_team': False,
        'can_clone': False,
        'can_watch': False
    }

    if user.is_superuser:
        permissions.update({k: True for k in permissions.keys()})
        return permissions

    # Basic view permission - team management focus
    if (task.assigned_to == user or task.created_by == user or 
        task.reviewer == user or task.assigned_to_all):
        permissions['can_view'] = True
        permissions['can_comment'] = True
        permissions['can_watch'] = True

    # Admin-created tasks are visible to all
    admin_users = User.objects.filter(
        Q(is_superuser=True) | Q(groups__name='Admin')
    )
    if task.created_by in admin_users:
        permissions['can_view'] = True
        permissions['can_comment'] = True

    # Edit permission
    if (user == task.created_by or user == task.assigned_to or 
        user.groups.filter(name__in=['Admin', 'Manager', 'Team Lead']).exists()):
        permissions['can_edit'] = True

    # Delete permission
    if (user == task.created_by or 
        user.groups.filter(name__in=['Admin', 'Manager']).exists()):
        permissions['can_delete'] = True

    # Submit permission
    if (user == task.assigned_to or 
        (task.assigned_to_all and user.is_authenticated)):
        permissions['can_submit'] = True

    # Review permission
    if (user == task.reviewer or 
        user.groups.filter(name__in=['Admin', 'Manager', 'Team Lead', 'Senior Developer']).exists()):
        permissions['can_review'] = True

    # Team management permissions
    if user.groups.filter(name__in=['Admin', 'Manager']).exists():
        permissions['can_manage_visibility'] = True
        permissions['can_assign_team'] = True
        permissions['can_clone'] = True

    return permissions


# Additional Team Management Views (Placeholders for future implementation)

@login_required
def clone_task(request, pk):
    """Clone a task for reuse - Team Management Feature"""
    original_task = get_object_or_404(Task, pk=pk)
    
    # Check permission
    if not get_user_task_permissions(request.user, original_task)['can_clone']:
        raise PermissionDenied("You don't have permission to clone this task.")
    
    # Clone the task
    cloned_task = Task.objects.create(
        title=f"Copy of {original_task.title}",
        description=original_task.description,
        category=original_task.category,
        task_type=original_task.task_type,
        priority=original_task.priority,
        difficulty=original_task.difficulty,
        created_by=request.user,
        estimated_hours=original_task.estimated_hours,
        acceptance_criteria=original_task.acceptance_criteria,
        points_value=original_task.points_value,
        status='todo',  # Reset status for cloned task
        progress_percentage=0,  # Reset progress
    )
    
    # Copy many-to-many relationships
    cloned_task.tags.set(original_task.tags.all())
    cloned_task.required_skills.set(original_task.required_skills.all())
    cloned_task.technologies.set(original_task.technologies.all())
    
    # Log the activity
    UserActivity.objects.create(
        user=request.user,
        activity_type='other',
        description=f"Cloned task: {original_task.title}",
        related_object_id=cloned_task.id,
        related_object_type='task'
    )
    
    messages.success(request, f"Task '{original_task.title}' has been successfully cloned!")
    return redirect('tasks:task-detail', pk=cloned_task.id)


@login_required
def assign_team(request, pk):
    """Assign team members to task - Team Management Feature"""
    task = get_object_or_404(Task, pk=pk)
    
    # Check permission
    if not get_user_task_permissions(request.user, task)['can_assign_team']:
        raise PermissionDenied("You don't have permission to assign team members.")
    
    if request.method == 'POST':
        action = request.POST.get('action')
        user_id = request.POST.get('user_id')
        
        if action == 'assign_single' and user_id:
            try:
                user = User.objects.get(id=user_id, is_active=True)
                task.assigned_to = user
                task.assigned_to_all = False
                task.save()
                
                # Log the activity
                UserActivity.objects.create(
                    user=request.user,
                    activity_type='other',
                    description=f"Assigned task '{task.title}' to {user.get_full_name()}",
                    related_object_id=task.id,
                    related_object_type='task'
                )
                
                messages.success(request, f"Task assigned to {user.get_full_name()} successfully!")
            except User.DoesNotExist:
                messages.error(request, "Selected user not found.")
        
        elif action == 'assign_all':
            task.assigned_to = None
            task.assigned_to_all = True
            task.save()
            
            # Log the activity
            UserActivity.objects.create(
                user=request.user,
                activity_type='other',
                description=f"Assigned task '{task.title}' to all team members",
                related_object_id=task.id,
                related_object_type='task'
            )
            
            messages.success(request, "Task assigned to all team members successfully!")
        
        elif action == 'unassign':
            task.assigned_to = None
            task.assigned_to_all = False
            task.save()
            
            messages.success(request, "Task assignment removed successfully!")
        
        return redirect('tasks:task-detail', pk=pk)
    
    # Get available users for assignment
    available_users = User.objects.filter(is_active=True).exclude(id=request.user.id)
    
    context = {
        'task': task,
        'available_users': available_users,
        'current_assignment': {
            'user': task.assigned_to,
            'all_users': task.assigned_to_all,
        }
    }
    
    return render(request, 'tasks/assign_team.html', context)


@login_required
def manage_visibility(request, pk):
    """Manage task visibility settings - Team Management Feature"""
    task = get_object_or_404(Task, pk=pk)
    
    # Check permission
    if not get_user_task_permissions(request.user, task)['can_manage_visibility']:
        raise PermissionDenied("You don't have permission to manage task visibility.")
    
    if request.method == 'POST':
        visibility_type = request.POST.get('visibility_type')
        
        if visibility_type == 'public':
            task.assigned_to_all = True
            task.assigned_to = None
            messages.success(request, "Task is now visible to all team members.")
            
        elif visibility_type == 'private':
            task.assigned_to_all = False
            if not task.assigned_to:
                task.assigned_to = request.user
            messages.success(request, "Task is now private to assigned user only.")
            
        elif visibility_type == 'team_leads':
            # Only team leads and admins can see this task
            task.assigned_to_all = False
            task.assigned_to = None
            messages.success(request, "Task is now visible to team leads and admins only.")
        
        task.save()
        
        # Log the activity
        UserActivity.objects.create(
            user=request.user,
            activity_type='other',
            description=f"Changed visibility of task '{task.title}' to {visibility_type}",
            related_object_id=task.id,
            related_object_type='task'
        )
        
        return redirect('tasks:task-detail', pk=pk)
    
    context = {
        'task': task,
        'current_visibility': {
            'is_public': task.assigned_to_all,
            'is_private': not task.assigned_to_all and task.assigned_to,
            'is_team_leads': not task.assigned_to_all and not task.assigned_to,
        }
    }
    
    return render(request, 'tasks/manage_visibility.html', context)


@login_required
def time_log(request, pk):
    """Time logging for tasks - Team Management Feature"""
    task = get_object_or_404(Task, pk=pk)
    
    # Check permission
    if not get_user_task_permissions(request.user, task)['can_view']:
        raise PermissionDenied("You don't have permission to log time for this task.")
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'start_timer':
            # Check if there's already an active timer
            active_log = TaskTimeLog.objects.filter(
                task=task, 
                user=request.user, 
                end_time__isnull=True
            ).first()
            
            if active_log:
                messages.warning(request, "You already have an active timer for this task!")
            else:
                TaskTimeLog.objects.create(
                    task=task,
                    user=request.user,
                    start_time=timezone.now(),
                    description=request.POST.get('description', '')
                )
                messages.success(request, "Timer started successfully!")
        
        elif action == 'stop_timer':
            active_log = TaskTimeLog.objects.filter(
                task=task, 
                user=request.user, 
                end_time__isnull=True
            ).first()
            
            if active_log:
                active_log.end_time = timezone.now()
                active_log.save()  # This will auto-calculate duration
                messages.success(request, f"Timer stopped. Logged {active_log.duration_minutes} minutes.")
            else:
                messages.error(request, "No active timer found for this task!")
        
        elif action == 'add_manual':
            try:
                duration = int(request.POST.get('manual_duration', 0))
                description = request.POST.get('manual_description', '')
                
                if duration > 0:
                    TaskTimeLog.objects.create(
                        task=task,
                        user=request.user,
                        start_time=timezone.now(),
                        end_time=timezone.now(),
                        duration_minutes=duration,
                        description=description
                    )
                    messages.success(request, f"Manual time entry of {duration} minutes added successfully!")
                else:
                    messages.error(request, "Duration must be greater than 0!")
            except ValueError:
                messages.error(request, "Invalid duration value!")
        
        return redirect('tasks:time-log', pk=pk)
    
    # Get time logs for this task by the current user
    user_time_logs = TaskTimeLog.objects.filter(
        task=task, 
        user=request.user
    ).order_by('-start_time')
    
    # Get active timer
    active_timer = TaskTimeLog.objects.filter(
        task=task, 
        user=request.user, 
        end_time__isnull=True
    ).first()
    
    # Calculate total time spent by user
    total_time = user_time_logs.aggregate(
        total=models.Sum('duration_minutes')
    )['total'] or 0
    
    context = {
        'task': task,
        'user_time_logs': user_time_logs[:20],  # Last 20 entries
        'active_timer': active_timer,
        'total_time_minutes': total_time,
        'total_time_hours': round(total_time / 60, 2),
    }
    
    return render(request, 'tasks/time_log.html', context)


@login_required
def manage_watchers(request, pk):
    """Manage task watchers - Team Management Feature"""
    task = get_object_or_404(Task, pk=pk)
    
    # Check permission
    if not get_user_task_permissions(request.user, task)['can_watch']:
        raise PermissionDenied("You don't have permission to manage watchers.")
    
    # TODO: Implement watcher management
    messages.info(request, "Watcher management feature - Coming Soon!")
    return redirect('tasks:task-detail', pk=pk)


@login_required
def task_templates(request):
    """Task templates management - Team Management Feature"""
    
    # Get user's templates
    user_templates = TaskTemplate.objects.filter(created_by=request.user).order_by('-created_at')
    
    # Get public templates (created by admins)
    public_templates = TaskTemplate.objects.filter(
        created_by__is_staff=True
    ).exclude(created_by=request.user).order_by('-times_used')
    
    # Get popular templates
    popular_templates = TaskTemplate.objects.filter(
        times_used__gt=0
    ).order_by('-times_used')[:5]
    
    context = {
        'user_templates': user_templates,
        'public_templates': public_templates,
        'popular_templates': popular_templates,
        'can_create_template': request.user.is_staff or request.user.role in ['admin', 'team_lead']
    }
    
    return render(request, 'tasks/templates.html', context)


@login_required
def create_template(request):
    """Create task template - Team Management Feature"""
    
    # Check permission
    if not (request.user.is_staff or getattr(request.user, 'role', '') in ['admin', 'team_lead']):
        messages.error(request, "You don't have permission to create task templates.")
        return redirect('tasks:task-templates')
    
    if request.method == 'POST':
        # Get task ID to create template from
        task_id = request.POST.get('task_id')
        template_name = request.POST.get('template_name', '').strip()
        template_description = request.POST.get('template_description', '').strip()
        
        if not template_name:
            messages.error(request, "Template name is required.")
            return redirect('tasks:create-template')
        
        if task_id:
            # Create template from existing task
            try:
                source_task = Task.objects.get(id=task_id)
                
                # Check if user can access this task
                if not get_user_task_permissions(request.user, source_task)['can_view']:
                    messages.error(request, "You don't have permission to access this task.")
                    return redirect('tasks:create-template')
                
                template = TaskTemplate.objects.create(
                    name=template_name,
                    description=template_description,
                    category=source_task.category,
                    created_by=request.user
                )
                
                messages.success(request, f"Template '{template_name}' created successfully from task '{source_task.title}'!")
                
            except Task.DoesNotExist:
                messages.error(request, "Selected task not found.")
                return redirect('tasks:create-template')
        else:
            # Create blank template
            template = TaskTemplate.objects.create(
                name=template_name,
                description=template_description,
                created_by=request.user
            )
            
            messages.success(request, f"Blank template '{template_name}' created successfully!")
        
        return redirect('tasks:task-templates')
    
    # Get user's tasks for template creation
    user_tasks = Task.objects.filter(
        Q(created_by=request.user) | Q(assigned_to=request.user)
    ).order_by('-created_at')[:20]
    
    context = {
        'user_tasks': user_tasks,
    }
    
    return render(request, 'tasks/create_template.html', context)


@login_required
def task_analytics(request):
    """Task analytics dashboard - Team Management Feature"""
    
    # Get date range filter
    from datetime import timedelta
    from django.db.models import Avg, Count, Sum, Case, When, IntegerField
    
    # Default to last 30 days
    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)
    
    # Get filter parameters
    date_range = request.GET.get('range', '30')
    if date_range == '7':
        start_date = end_date - timedelta(days=7)
    elif date_range == '90':
        start_date = end_date - timedelta(days=90)
    elif date_range == '365':
        start_date = end_date - timedelta(days=365)
    
    # Base queryset - user's visible tasks
    user = request.user
    if user.is_staff or getattr(user, 'role', '') in ['admin', 'team_lead']:
        tasks_qs = Task.objects.all()
    else:
        tasks_qs = Task.objects.filter(
            Q(assigned_to=user) | Q(created_by=user) | Q(assigned_to_all=True)
        ).distinct()
    
    # Filter by date range
    period_tasks = tasks_qs.filter(created_at__gte=start_date)
    
    # Task metrics
    task_metrics = {
        'total_tasks': tasks_qs.count(),
        'period_tasks': period_tasks.count(),
        'completed_tasks': tasks_qs.filter(status='completed').count(),
        'in_progress_tasks': tasks_qs.filter(status='in_progress').count(),
        'overdue_tasks': tasks_qs.filter(
            due_date__lt=timezone.now(),
            status__in=['todo', 'in_progress']
        ).count(),
        'completion_rate': 0,
    }
    
    if task_metrics['total_tasks'] > 0:
        task_metrics['completion_rate'] = round(
            (task_metrics['completed_tasks'] / task_metrics['total_tasks']) * 100, 1
        )
    
    # Priority distribution
    priority_stats = tasks_qs.aggregate(
        critical=Count(Case(When(priority='critical', then=1), output_field=IntegerField())),
        urgent=Count(Case(When(priority='urgent', then=1), output_field=IntegerField())),
        high=Count(Case(When(priority='high', then=1), output_field=IntegerField())),
        medium=Count(Case(When(priority='medium', then=1), output_field=IntegerField())),
        low=Count(Case(When(priority='low', then=1), output_field=IntegerField())),
    )
    
    # Status distribution
    status_stats = tasks_qs.aggregate(
        todo=Count(Case(When(status='todo', then=1), output_field=IntegerField())),
        in_progress=Count(Case(When(status='in_progress', then=1), output_field=IntegerField())),
        review=Count(Case(When(status='review', then=1), output_field=IntegerField())),
        completed=Count(Case(When(status='completed', then=1), output_field=IntegerField())),
        blocked=Count(Case(When(status='blocked', then=1), output_field=IntegerField())),
    )
    
    # Time tracking metrics
    time_logs = TaskTimeLog.objects.filter(task__in=tasks_qs)
    time_metrics = {
        'total_logged_hours': round((time_logs.aggregate(Sum('duration_minutes'))['duration_minutes__sum'] or 0) / 60, 1),
        'avg_task_duration': round(time_logs.aggregate(Avg('duration_minutes'))['duration_minutes__avg'] or 0, 1),
        'active_timers': time_logs.filter(end_time__isnull=True).count(),
    }
    
    # Team performance (if admin/team lead)
    team_performance = {}
    if user.is_staff or getattr(user, 'role', '') in ['admin', 'team_lead']:
        # Get top performers
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        performers = User.objects.filter(
            assigned_tasks__in=tasks_qs.filter(status='completed')
        ).annotate(
            completed_count=Count('assigned_tasks', filter=Q(assigned_tasks__status='completed')),
            total_points=Sum('assigned_tasks__points_value', filter=Q(assigned_tasks__status='completed'))
        ).order_by('-completed_count')[:5]
        
        team_performance = {
            'top_performers': performers,
            'total_team_points': sum(p.total_points or 0 for p in performers),
        }
    
    # Recent activities
    recent_completed = tasks_qs.filter(
        status='completed',
        completion_date__gte=start_date
    ).order_by('-completion_date')[:10]
    
    context = {
        'task_metrics': task_metrics,
        'priority_stats': priority_stats,
        'status_stats': status_stats,
        'time_metrics': time_metrics,
        'team_performance': team_performance,
        'recent_completed': recent_completed,
        'date_range': date_range,
        'start_date': start_date,
        'end_date': end_date,
        'can_view_team_data': user.is_staff or getattr(user, 'role', '') in ['admin', 'team_lead'],
    }
    
    return render(request, 'tasks/analytics.html', context)


@login_required
def team_dashboard(request):
    """Team-wide task dashboard - Team Management Feature"""
    user = request.user
    
    # Get team-wide statistics
    if user.groups.filter(name__in=['Admin', 'Manager', 'Team Lead']).exists():
        # Team leads see all team tasks
        team_tasks = Task.objects.all()
    else:
        # Regular users see their visible tasks
        team_tasks = Task.objects.filter(
            Q(assigned_to=user) | 
            Q(created_by=user) |
            Q(assigned_to_all=True) |
            Q(created_by__groups__name='Admin')
        ).distinct()
    
    context = {
        'team_tasks': team_tasks,
        'team_stats': {
            'total_tasks': team_tasks.count(),
            'active_tasks': team_tasks.filter(status__in=['todo', 'in_progress']).count(),
            'completed_tasks': team_tasks.filter(status='completed').count(),
        }
    }
    
    # TODO: Implement full team dashboard features
    messages.info(request, "Team dashboard features - Coming Soon!")
    return render(request, 'tasks/team_dashboard.html', context)


# API endpoints for team management

@login_required
@require_http_methods(["POST"])
def assign_task_api(request):
    """Assign task via API - Team Management Feature"""
    try:
        data = json.loads(request.body)
        task_id = data.get('task_id')
        user_id = data.get('user_id')
        
        task = get_object_or_404(Task, id=task_id)
        
        # Check permission
        if not get_user_task_permissions(request.user, task)['can_assign_team']:
            return JsonResponse({'error': 'Permission denied'}, status=403)
        
        # TODO: Implement assignment logic
        return JsonResponse({
            'success': True,
            'message': 'Assignment feature - Coming Soon!'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
@require_http_methods(["POST"])
def bulk_status_update(request):
    """Bulk status update via API - Team Management Feature"""
    try:
        data = json.loads(request.body)
        task_ids = data.get('task_ids', [])
        new_status = data.get('status')
        
        # TODO: Implement bulk status update
        return JsonResponse({
            'success': True,
            'message': 'Bulk operations feature - Coming Soon!',
            'updated_count': len(task_ids)
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
def update_task_status(request, pk):
    """Update task status with notes"""
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    
    try:
        task = get_object_or_404(Task, pk=pk)
        user = request.user
        
        # Check permissions
        if not (user == task.created_by or user == task.assigned_to or 
                user.groups.filter(name__in=['Admin', 'Manager', 'Team Lead']).exists()):
            messages.error(request, "You don't have permission to update this task status.")
            return redirect('tasks:task-detail', pk=pk)
        
        new_status = request.POST.get('status')
        notes = request.POST.get('notes', '')
        
        if new_status and new_status in dict(Task.STATUS_CHOICES):
            old_status = task.status
            task.status = new_status
            
            # Update completion date if completed
            if new_status == 'completed' and old_status != 'completed':
                task.completion_date = timezone.now()
                task.progress_percentage = 100
            elif new_status != 'completed':
                task.completion_date = None
            
            task.save()
            
            # Log the status change
            UserActivity.objects.create(
                user=user,
                activity_type='other',
                description=f"Updated task status: {old_status} → {new_status}",
                related_object_id=task.id,
                related_object_type='task',
                additional_info=f"Task: {task.title}. Notes: {notes}" if notes else f"Task: {task.title}"
            )
            
            messages.success(request, f'Task status updated to {task.get_status_display()}')
        else:
            messages.error(request, 'Invalid status selected.')
            
    except Exception as e:
        messages.error(request, f'Error updating task status: {str(e)}')
    
    return redirect('tasks:task-detail', pk=pk)


@login_required
def recurring_tasks_view(request):
    """Display available recurring tasks for user selection"""
    # Get all recurring task templates that allow member selection
    available_templates = Task.objects.filter(
        is_template=True,
        is_recurring=True,
        allow_member_selection=True,
        status='todo'
    ).order_by('title')
    
    # Get user's current selections
    user_selections = {}
    from .models import TaskRecurringSelection
    
    for selection in TaskRecurringSelection.objects.filter(user=request.user, is_active=True):
        key = f"{selection.task_template.id}_{selection.selection_type}"
        user_selections[key] = {
            'selected_days': selection.selected_days,
            'selection': selection
        }
    
    context = {
        'available_templates': available_templates,
        'user_selections': user_selections,
        'weekdays': [
            ('mon', 'Monday'),
            ('tue', 'Tuesday'),
            ('wed', 'Wednesday'),
            ('thu', 'Thursday'),
            ('fri', 'Friday'),
            ('sat', 'Saturday'),
            ('sun', 'Sunday'),
        ]
    }
    return render(request, 'tasks/recurring_tasks.html', context)


@login_required
@require_http_methods(["POST"])
def select_recurring_task(request):
    """Handle user selection/deselection of recurring tasks"""
    task_id = request.POST.get('task_id')
    selection_type = request.POST.get('selection_type')  # 'daily' or 'weekly'
    selected_days = request.POST.getlist('selected_days[]')  # For weekly tasks
    action = request.POST.get('action')  # 'select' or 'deselect'
    
    try:
        template_task = get_object_or_404(Task, id=task_id, is_template=True, is_recurring=True)
        
        from .models import TaskRecurringSelection
        
        # Get or create selection
        selection, created = TaskRecurringSelection.objects.get_or_create(
            user=request.user,
            task_template=template_task,
            selection_type=selection_type,
            defaults={
                'is_active': action == 'select',
                'selected_days': ','.join(selected_days) if selected_days else ''
            }
        )
        
        if not created:
            # Update existing selection
            selection.is_active = action == 'select'
            selection.selected_days = ','.join(selected_days) if selected_days else ''
            selection.save()
        
        if action == 'select':
            messages.success(
                request, 
                f"Successfully selected {template_task.title} for {selection_type} tasks!"
            )
            
            # Log the activity
            UserActivity.objects.create(
                user=request.user,
                activity_type='other',
                description=f"Selected recurring task: {template_task.title} ({selection_type})",
                related_object_id=template_task.id,
                related_object_type='task'
            )
        else:
            messages.success(
                request, 
                f"Successfully removed {template_task.title} from your {selection_type} tasks."
            )
            
            # Log the activity
            UserActivity.objects.create(
                user=request.user,
                activity_type='other',
                description=f"Deselected recurring task: {template_task.title} ({selection_type})",
                related_object_id=template_task.id,
                related_object_type='task'
            )
        
    except Exception as e:
        messages.error(request, f'Error updating recurring task selection: {str(e)}')
    
    return redirect('tasks:recurring-tasks')


@login_required
def create_recurring_template(request):
    """Create a new recurring task template"""
    # Check if user has permission to create templates
    if not (request.user.is_superuser or 
            request.user.groups.filter(name__in=['Admin', 'Manager', 'Team Lead']).exists()):
        from django.contrib import messages
        from django.shortcuts import redirect
        messages.error(request, 'You do not have permission to create recurring task templates.')
        return redirect('tasks:recurring-tasks')
    
    if request.method == 'POST':
        try:
            # Create the template task
            template = Task.objects.create(
                title=request.POST.get('title'),
                description=request.POST.get('description'),
                category_id=request.POST.get('category') if request.POST.get('category') else None,
                task_type=request.POST.get('task_type', 'learning'),
                priority=request.POST.get('priority', 'medium'),
                difficulty=request.POST.get('difficulty', 'medium'),
                created_by=request.user,
                estimated_hours=float(request.POST.get('estimated_hours', 1.0)),
                points_value=int(request.POST.get('points_value', 10)),
                acceptance_criteria=request.POST.get('acceptance_criteria', ''),
                is_recurring=True,
                is_template=True,
                recurrence_type=request.POST.get('recurrence_type'),
                recurrence_days=','.join(request.POST.getlist('recurrence_days[]')),
                allow_member_selection=bool(request.POST.get('allow_member_selection')),
                max_assignees=int(request.POST.get('max_assignees', 1)),
                assigned_to_all=bool(request.POST.get('assigned_to_all'))
            )
            
            messages.success(request, f'Recurring task template "{template.title}" created successfully!')
            
            # Log the activity
            UserActivity.objects.create(
                user=request.user,
                activity_type='task_created',
                description=f"Created recurring task template: {template.title}",
                related_object_id=template.id,
                related_object_type='task'
            )
            
            return redirect('tasks:recurring-templates')
            
        except Exception as e:
            messages.error(request, f'Error creating recurring task template: {str(e)}')
    
    # Get form data for template creation
    from .models import TaskCategory
    categories = TaskCategory.objects.filter(is_active=True)
    
    context = {
        'categories': categories,
        'task_types': Task.TYPE_CHOICES,
        'priority_choices': Task.PRIORITY_CHOICES,
        'difficulty_choices': Task.DIFFICULTY_CHOICES,
        'recurrence_choices': [
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
            ('both', 'Both Daily and Weekly'),
        ],
        'weekdays': [
            ('mon', 'Monday'),
            ('tue', 'Tuesday'),
            ('wed', 'Wednesday'),
            ('thu', 'Thursday'),
            ('fri', 'Friday'),
            ('sat', 'Saturday'),
            ('sun', 'Sunday'),
        ]
    }
    return render(request, 'tasks/create_recurring_template.html', context)


@login_required
def recurring_templates_view(request):
    """View and manage recurring task templates"""
    # Check if user has permission to manage templates
    if not (request.user.is_superuser or 
            request.user.groups.filter(name__in=['Admin', 'Manager', 'Team Lead']).exists()):
        from django.contrib import messages
        from django.shortcuts import redirect
        messages.error(request, 'You do not have permission to manage recurring task templates.')
        return redirect('tasks:recurring-tasks')
    
    templates = Task.objects.filter(is_template=True, is_recurring=True).order_by('-created_at')
    
    # Get statistics for each template
    template_stats = {}
    from .models import TaskRecurringSelection
    
    for template in templates:
        daily_selections = TaskRecurringSelection.objects.filter(
            task_template=template,
            selection_type='daily',
            is_active=True
        ).count()
        
        weekly_selections = TaskRecurringSelection.objects.filter(
            task_template=template,
            selection_type='weekly',
            is_active=True
        ).count()
        
        instances_created = Task.objects.filter(template_task=template).count()
        
        template_stats[template.id] = {
            'daily_selections': daily_selections,
            'weekly_selections': weekly_selections,
            'total_instances': instances_created
        }
    
    context = {
        'templates': templates,
        'template_stats': template_stats
    }
    return render(request, 'tasks/recurring_templates.html', context)


@login_required
@require_http_methods(["POST"])
def generate_recurring_tasks_manual(request):
    """Manually trigger generation of recurring tasks"""
    if not request.user.groups.filter(name__in=['Admin', 'Manager', 'Team Lead']).exists():
        messages.error(request, 'Permission denied.')
        return redirect('tasks:task-list')
    
    try:
        from datetime import date
        target_date = date.today()
        
        # Generate daily tasks
        daily_tasks = Task.generate_daily_tasks(target_date)
        
        # Generate weekly tasks
        weekly_tasks = Task.generate_weekly_tasks(target_date)
        
        total_created = len(daily_tasks) + len(weekly_tasks)
        
        messages.success(
            request,
            f'Successfully generated {total_created} recurring tasks for today '
            f'({len(daily_tasks)} daily, {len(weekly_tasks)} weekly)'
        )
        
        # Log the activity
        UserActivity.objects.create(
            user=request.user,
            activity_type='other',
            description=f"Manually generated {total_created} recurring tasks",
            additional_info=f"Daily: {len(daily_tasks)}, Weekly: {len(weekly_tasks)}"
        )
        
    except Exception as e:
        messages.error(request, f'Error generating recurring tasks: {str(e)}')
    
    return redirect('tasks:recurring-templates')
