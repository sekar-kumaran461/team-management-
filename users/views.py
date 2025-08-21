from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView, DetailView, UpdateView, FormView
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Count, Q
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import User, UserProfile
from .serializers import UserSerializer, UserProfileSerializer
from .forms import UserProfileForm, UserRegistrationForm, LoginForm
from tasks.models import Task
from projects.models import Project
from analytics.models import UserActivity
from django.utils import timezone

class DashboardView(LoginRequiredMixin, TemplateView):
    """Main dashboard view"""
    template_name = 'users/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Show all tasks to all users (no filtering by assignment)
        # This allows all users to see the learning tasks created by administrators
        all_tasks = Task.objects.all()
        
        # Get recent tasks (all tasks)
        recent_tasks = all_tasks.order_by('-created_at')[:5]
        
        # Get task statistics (all tasks)
        task_stats = {
            'total': all_tasks.count(),
            'completed': all_tasks.filter(status='completed').count(),
            'pending': all_tasks.filter(status='todo').count(),
            'in_progress': all_tasks.filter(status='in_progress').count(),
            'overdue': all_tasks.filter(
                due_date__lt=timezone.now(),
                status__in=['todo', 'in_progress']
            ).count(),
        }
        
        # Calculate completion percentage
        if task_stats['total'] > 0:
            task_stats['completion_percentage'] = round((task_stats['completed'] / task_stats['total']) * 100)
        else:
            task_stats['completion_percentage'] = 0
        
        # Get project statistics
        project_stats = {
            'total': Project.objects.count(),
            'active': Project.objects.filter(status='in_progress').count(),
            'planning': Project.objects.filter(status='planning').count(),
            'completed': Project.objects.filter(status='completed').count(),
        }
        
        # Get learning progress (overall progress across all tasks)
        learning_progress = {
            'dsa_tasks': all_tasks.filter(task_type='feature', status='completed').count(),
            'python_tasks': all_tasks.filter(task_type='bug', status='completed').count(),
            'ml_tasks': all_tasks.filter(task_type='learning', status='completed').count(),
        }
        
        # Get recent activities
        recent_activities = UserActivity.objects.filter(user=user).order_by('-timestamp')[:5]
        
        # Get upcoming deadlines (all tasks)
        upcoming_deadlines = all_tasks.filter(
            due_date__gte=timezone.now(),
            due_date__lte=timezone.now() + timezone.timedelta(days=7),
            status__in=['todo', 'in_progress']
        ).order_by('due_date')[:5]
        
        # Add today's date
        context.update({
            'today': timezone.now(),
            'recent_tasks': recent_tasks,
            'task_stats': task_stats,
            'project_stats': project_stats,
            'learning_progress': learning_progress,
            'recent_activities': recent_activities,
            'upcoming_deadlines': upcoming_deadlines,
            'user_progress': user.profile if hasattr(user, 'profile') else None,
        })
        
        return context

class ProfileView(LoginRequiredMixin, DetailView):
    """User profile view"""
    model = User
    template_name = 'users/profile.html'
    context_object_name = 'profile_user'
    
    def get_object(self):
        return self.request.user

class ProfileEditView(LoginRequiredMixin, UpdateView):
    """Edit user profile"""
    model = User
    form_class = UserProfileForm
    template_name = 'users/profile_edit.html'
    success_url = reverse_lazy('users:profile')
    
    def get_object(self):
        return self.request.user
    
    def form_valid(self, form):
        messages.success(self.request, 'Profile updated successfully!')
        return super().form_valid(form)

class TeamView(LoginRequiredMixin, TemplateView):
    """Team members view"""
    template_name = 'users/team.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['team_members'] = User.objects.filter(is_active=True).exclude(id=self.request.user.id)
        return context

class LoginView(FormView):
    """Custom login view"""
    template_name = 'users/login.html'
    form_class = LoginForm
    success_url = reverse_lazy('users:dashboard')
    
    def form_valid(self, form):
        email = form.cleaned_data['email']
        password = form.cleaned_data['password']
        user = authenticate(self.request, username=email, password=password)
        if user:
            login(self.request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(self.request, f'Welcome back, {user.first_name}!')
            return super().form_valid(form)
        else:
            form.add_error(None, 'Invalid email or password.')
            return self.form_invalid(form)
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('users:dashboard')
        return super().dispatch(request, *args, **kwargs)

def register_view(request):
    """User registration view"""
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Specify the backend when logging in after registration
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, 'Registration successful!')
            return redirect('users:dashboard')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'users/register.html', {'form': form})

@login_required
def logout_view(request):
    """User logout view"""
    logout(request)
    messages.success(request, 'You have been logged out successfully!')
    return redirect('users:login')

class UserManagementView(LoginRequiredMixin, TemplateView):
    """User management view for administrators"""
    template_name = 'users/user_management.html'
    
    def dispatch(self, request, *args, **kwargs):
        # Only allow admin users
        if not request.user.is_authenticated or request.user.role != 'admin':
            messages.error(request, 'Access denied. Admin privileges required.')
            return redirect('users:dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get all users with their statistics
        users = User.objects.all().order_by('-date_joined')
        
        # Get user statistics
        user_stats = {
            'total_users': users.count(),
            'active_users': users.filter(is_active=True).count(),
            'inactive_users': users.filter(is_active=False).count(),
            'admin_users': users.filter(role='admin').count(),
            'teacher_users': users.filter(role='teacher').count(),
            'student_users': users.filter(role='student').count(),
        }
        
        # Get recent registrations (last 30 days)
        from datetime import timedelta
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_registrations = users.filter(date_joined__gte=thirty_days_ago).count()
        
        # Prepare user data with additional info
        user_data = []
        for user in users:
            user_tasks = Task.objects.filter(assigned_to=user)
            user_projects = Project.objects.filter(team_members=user)
            
            user_info = {
                'user': user,
                'task_count': user_tasks.count(),
                'completed_tasks': user_tasks.filter(status='completed').count(),
                'project_count': user_projects.count(),
                'last_activity': UserActivity.objects.filter(user=user).first(),
                'total_points': getattr(user, 'total_points', 0),
            }
            user_data.append(user_info)
        
        context.update({
            'users': user_data,
            'user_stats': user_stats,
            'recent_registrations': recent_registrations,
            'roles': User.ROLE_CHOICES if hasattr(User, 'ROLE_CHOICES') else [
                ('admin', 'Administrator'),
                ('teacher', 'Teacher'),
                ('student', 'Student'),
            ],
        })
        
        return context

class UserCreateView(LoginRequiredMixin, FormView):
    """Create new user view for administrators"""
    template_name = 'users/user_create.html'
    form_class = UserRegistrationForm
    success_url = reverse_lazy('users:user-management')
    
    def dispatch(self, request, *args, **kwargs):
        # Only allow admin users
        if not request.user.is_authenticated or request.user.role != 'admin':
            messages.error(request, 'Access denied. Admin privileges required.')
            return redirect('users:dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        user = form.save()
        messages.success(self.request, f'User {user.full_name} created successfully!')
        return super().form_valid(form)

class UserDetailView(LoginRequiredMixin, DetailView):
    """User detail view for administrators"""
    model = User
    template_name = 'users/user_detail.html'
    context_object_name = 'profile_user'
    
    def dispatch(self, request, *args, **kwargs):
        # Only allow admin users or viewing own profile
        user = self.get_object()
        if not request.user.is_authenticated or (request.user.role != 'admin' and request.user != user):
            messages.error(request, 'Access denied.')
            return redirect('users:dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.get_object()
        
        # Get user's tasks and projects
        user_tasks = Task.objects.filter(assigned_to=user)
        user_projects = Project.objects.filter(team_members=user)
        
        context.update({
            'user_tasks': user_tasks.order_by('-created_at')[:10],
            'user_projects': user_projects.order_by('-created_at')[:10],
            'task_stats': {
                'total': user_tasks.count(),
                'completed': user_tasks.filter(status='completed').count(),
                'in_progress': user_tasks.filter(status='in_progress').count(),
                'pending': user_tasks.filter(status='todo').count(),
            },
            'recent_activities': UserActivity.objects.filter(user=user).order_by('-timestamp')[:10],
        })
        
        return context

class UserEditView(LoginRequiredMixin, UpdateView):
    """Edit user view for administrators"""
    model = User
    form_class = UserProfileForm
    template_name = 'users/user_edit.html'
    
    def dispatch(self, request, *args, **kwargs):
        # Only allow admin users or editing own profile
        user = self.get_object()
        if not request.user.is_authenticated or (request.user.role != 'admin' and request.user != user):
            messages.error(request, 'Access denied.')
            return redirect('users:dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def get_success_url(self):
        if self.request.user.role == 'admin':
            return reverse_lazy('users:user-management')
        return reverse_lazy('users:profile')
    
    def form_valid(self, form):
        messages.success(self.request, f'User {form.instance.full_name} updated successfully!')
        return super().form_valid(form)

@login_required
def toggle_user_status(request, pk):
    """Toggle user active status (admin only)"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('users:dashboard')
    
    user = get_object_or_404(User, pk=pk)
    user.is_active = not user.is_active
    user.save()
    
    status_text = 'activated' if user.is_active else 'deactivated'
    messages.success(request, f'User {user.full_name} has been {status_text}.')
    
    return redirect('users:user-management')

@login_required
def export_users(request):
    """Export users to CSV (admin only)"""
    import csv
    from django.http import HttpResponse
    
    if request.user.role != 'admin':
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('users:dashboard')
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="users_export.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['ID', 'Name', 'Email', 'Role', 'Active', 'Date Joined', 'Last Login'])
    
    users = User.objects.all().order_by('date_joined')
    for user in users:
        writer.writerow([
            user.id,
            user.full_name,
            user.email,
            user.get_role_display() if hasattr(user, 'get_role_display') else user.role,
            'Yes' if user.is_active else 'No',
            user.date_joined.strftime('%Y-%m-%d %H:%M:%S'),
            user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else 'Never',
        ])
    
    return response

# API ViewSets
class UserViewSet(viewsets.ModelViewSet):
    """User API ViewSet"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Filter by team membership if user is not admin
        if not self.request.user.role in ['admin', 'team_lead']:
            return User.objects.filter(is_active=True)
        return super().get_queryset()
    
    @action(detail=True, methods=['post'])
    def add_points(self, request, pk=None):
        """Add points to user"""
        user = self.get_object()
        points = request.data.get('points', 0)
        reason = request.data.get('reason', 'Points awarded')
        
        try:
            user.add_points(points, reason)
            return Response({'status': 'Points added successfully'})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def progress(self, request, pk=None):
        """Get user progress data"""
        user = self.get_object()
        
        # Get user's task progress
        user_tasks = Task.objects.filter(assigned_to=user)
        completed_tasks = user_tasks.filter(status='completed').count()
        total_tasks = user_tasks.count()
        
        # Get user's project progress
        user_projects = Project.objects.filter(team_members=user)
        completed_projects = user_projects.filter(status='completed').count()
        total_projects = user_projects.count()
        
        progress_data = {
            'total_points': user.total_points,
            'level': user.level,
            'badges_earned': user.badges_earned,
            'task_completion_rate': (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
            'project_completion_rate': (completed_projects / total_projects * 100) if total_projects > 0 else 0,
            'completed_tasks': completed_tasks,
            'total_tasks': total_tasks,
            'completed_projects': completed_projects,
            'total_projects': total_projects,
        }
        
        return Response(progress_data)

class UserProfileViewSet(viewsets.ModelViewSet):
    """User Profile API ViewSet"""
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Users can only access their own profile unless they're admin
        if self.request.user.role in ['admin', 'team_lead']:
            return super().get_queryset()
        return UserProfile.objects.filter(user=self.request.user)
