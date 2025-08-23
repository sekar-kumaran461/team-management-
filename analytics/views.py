from django.shortcuts import render
from django.views.generic import ListView, DetailView, CreateView, UpdateView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta

# Try to import REST framework components
try:
    from rest_framework import viewsets, permissions, status
    from rest_framework.response import Response
    from rest_framework.views import APIView
    HAS_REST_FRAMEWORK = True
except ImportError:
    HAS_REST_FRAMEWORK = False
    # Create dummy classes
    class ViewSets:
        class ModelViewSet:
            pass
    viewsets = ViewSets()
    
    class APIView:
        pass
    
    class Permissions:
        class IsAuthenticated:
            pass
    permissions = Permissions()
    
    class Status:
        HTTP_200_OK = 200
        HTTP_400_BAD_REQUEST = 400
        HTTP_404_NOT_FOUND = 404
    status = Status()
    
    class Response:
        def __init__(self, data=None, status=None):
            self.data = data
            self.status = status

from .models import UserActivity
from users.models import User
from tasks.models import Task
from projects.models import Project

# Web Views
class AnalyticsDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'analytics/analytics_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get general statistics
        context['total_users'] = User.objects.filter(is_active=True).count()
        context['total_tasks'] = Task.objects.count()
        context['total_projects'] = Project.objects.count()
        context['completed_tasks'] = Task.objects.filter(status='completed').count()
        
        # Get recent activities
        context['recent_activities'] = UserActivity.objects.all()[:10]
        
        return context

class TeamAnalyticsView(LoginRequiredMixin, TemplateView):
    template_name = 'analytics/team_analytics.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Team performance data
        context['team_stats'] = {
            'active_members': User.objects.filter(is_active=True).count(),
            'projects_in_progress': Project.objects.filter(status='in_progress').count(),
            'tasks_completed_this_week': Task.objects.filter(
                status='completed',
                completion_date__gte=timezone.now() - timedelta(days=7)
            ).count()
        }
        
        return context

class ProgressTrackingView(LoginRequiredMixin, TemplateView):
    template_name = 'analytics/progress_tracking.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # User progress data
        user = self.request.user
        context['user_stats'] = {
            'completed_tasks': Task.objects.filter(assigned_to=user, status='completed').count(),
            'total_points': user.total_points,
            'current_level': user.level,
            'active_projects': Project.objects.filter(team_members=user, status='in_progress').count()
        }
        
        return context

class ReportsView(LoginRequiredMixin, TemplateView):
    template_name = 'analytics/reports.html'

class LeaderboardView(LoginRequiredMixin, TemplateView):
    template_name = 'analytics/leaderboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Top users by points
        context['top_users'] = User.objects.filter(is_active=True).order_by('-total_points')[:10]
        
        return context

class ExportReportsView(LoginRequiredMixin, TemplateView):
    template_name = 'analytics/export_reports.html'

# API ViewSets - Only available if REST framework is installed
if HAS_REST_FRAMEWORK:
    class UserActivityViewSet(viewsets.ModelViewSet):
        queryset = UserActivity.objects.all()
        permission_classes = [permissions.IsAuthenticated]
        
        def get_queryset(self):
            # Users can only see their own activities unless admin
            if self.request.user.can_manage_users():
                return UserActivity.objects.all()
            return UserActivity.objects.filter(user=self.request.user)
        
        def get_serializer_class(self):
            from rest_framework import serializers
            class UserActivitySerializer(serializers.ModelSerializer):
                class Meta:
                    model = UserActivity
                    fields = '__all__'
            return UserActivitySerializer

    # API Views
    class AnalyticsDataAPIView(APIView):
        permission_classes = [permissions.IsAuthenticated]
        
        def get(self, request):
            """Get analytics data for dashboard"""
            user = request.user
            
            # Task analytics
            user_tasks = Task.objects.filter(assigned_to=user)
            task_stats = {
                'total': user_tasks.count(),
                'completed': user_tasks.filter(status='completed').count(),
                'in_progress': user_tasks.filter(status='in_progress').count(),
                'todo': user_tasks.filter(status='todo').count(),
            }
            
            # Project analytics
            user_projects = Project.objects.filter(team_members=user)
            project_stats = {
                'total': user_projects.count(),
                'completed': user_projects.filter(status='completed').count(),
                'in_progress': user_projects.filter(status='in_progress').count(),
                'planning': user_projects.filter(status='planning').count(),
            }
            
            # Activity analytics
            recent_activities = UserActivity.objects.filter(user=user).order_by('-timestamp')[:5]
            activity_data = []
            for activity in recent_activities:
                activity_data.append({
                    'type': activity.activity_type,
                    'description': activity.description,
                    'timestamp': activity.timestamp,
                    'points': activity.points_earned,
                })
            
            return Response({
                'user_stats': {
                    'total_points': user.total_points,
                    'level': user.level,
                    'badges_earned': user.badges_earned,
                },
                'task_stats': task_stats,
                'project_stats': project_stats,
                'recent_activities': activity_data,
            })

    class TeamAnalyticsAPIView(APIView):
        permission_classes = [permissions.IsAuthenticated]
        
        def get(self, request):
            """Get team analytics data"""
            
            # Only allow team leads and admins to see team analytics
            if not request.user.can_manage_users():
                return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
            
            # Team statistics
            team_stats = {
                'total_members': User.objects.filter(is_active=True).count(),
                'total_tasks': Task.objects.count(),
                'total_projects': Project.objects.count(),
                'completed_tasks': Task.objects.filter(status='completed').count(),
                'active_projects': Project.objects.filter(status='in_progress').count(),
            }
            
            # Top performers
            top_users = User.objects.filter(is_active=True).order_by('-total_points')[:5]
            top_performers = []
            for user in top_users:
                top_performers.append({
                    'name': user.get_full_name(),
                    'points': user.total_points,
                    'level': user.level,
                    'completed_tasks': Task.objects.filter(assigned_to=user, status='completed').count(),
                })
            
            return Response({
                'team_stats': team_stats,
                'top_performers': top_performers,
            })

else:
    # Dummy classes when REST framework is not available
    class UserActivityViewSet:
        pass
    
    class AnalyticsDataAPIView:
        pass
    
    class TeamAnalyticsAPIView:
        pass
