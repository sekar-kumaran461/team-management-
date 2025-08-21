"""
Simple URL patterns for Google Database Integration
"""
from django.urls import path
from . import simple_views

app_name = 'google_integration'

urlpatterns = [
    # Main dashboard
    path('', simple_views.GoogleDatabaseDashboard.as_view(), name='dashboard'),
    path('simple/', simple_views.GoogleDatabaseDashboard.as_view(), name='simple_dashboard'),
    
    # Setup and management
    path('setup/', simple_views.setup_database, name='setup'),
    path('guide/', simple_views.GoogleDatabaseSetupGuide.as_view(), name='setup_guide'),
    path('sync/', simple_views.sync_to_sheets, name='sync'),
    path('test/', simple_views.test_connection, name='test'),
    path('test-connection/', simple_views.test_connection, name='test_connection_ajax'),
    
    # File Management
    path('files/', simple_views.file_manager, name='file_manager'),
    path('files/upload/', simple_views.upload_file, name='upload_file'),
    path('files/sync/', simple_views.sync_files, name='sync_files'),
    
    # Status and Monitoring
    path('status/', simple_views.sync_status, name='sync_status'),
    path('logs/', simple_views.view_logs, name='logs'),
    
    # API endpoints
    path('api/data/', simple_views.get_sheet_data_api, name='api_data'),
    path('api/sync-status/', simple_views.sync_status_api, name='sync_status_api'),
]
