from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    # Web URLs
    path('', views.AnalyticsDashboardView.as_view(), name='dashboard'),
    path('team/', views.TeamAnalyticsView.as_view(), name='team-analytics'),
    path('progress/', views.ProgressTrackingView.as_view(), name='progress-tracking'),
    path('reports/', views.ReportsView.as_view(), name='reports'),
    path('leaderboard/', views.LeaderboardView.as_view(), name='leaderboard'),
    path('export/', views.ExportReportsView.as_view(), name='export-reports'),
]
