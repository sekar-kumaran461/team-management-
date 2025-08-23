    # Admin submissions review
from django.urls import path
from . import views

app_name = 'tasks'

urlpatterns = [
    path('admin/view-file/<int:submission_id>/', views.admin_view_file, name='admin-view-file'),
    path('admin/view-file/<int:submission_id>/', views.admin_view_file, name='admin-view-file'),
    # Task management
    path('', views.TaskListView.as_view(), name='task-list'),
    path('<int:pk>/', views.TaskDetailView.as_view(), name='task-detail'),
    path('create/', views.TaskCreateView.as_view(), name='task-create'),
    path('<int:pk>/edit/', views.TaskEditView.as_view(), name='task-edit'),
    path('<int:pk>/update/', views.TaskEditView.as_view(), name='task-update'),
    path('<int:pk>/delete/', views.TaskDeleteView.as_view(), name='task-delete'),
    path('<int:pk>/update-status/', views.update_task_status, name='update-status'),
    
    # Task submissions
    path('<int:task_id>/submit/', views.submit_task, name='submit-task'),
    path('<int:task_id>/progress/', views.task_progress, name='task-progress'),
    
    # Bulk operations
    path('bulk-upload/', views.BulkTaskUploadView.as_view(), name='bulk-upload'),
    path('export/', views.export_tasks, name='export-tasks'),
    
    # User views
    path('my-tasks/', views.my_tasks, name='my-tasks'),
    path('my-submissions/', views.my_submissions, name='my-submissions'),
    
    # Calendar view
    path('calendar/', views.task_calendar, name='task-calendar'),
    
    # Team management features (placeholders for future implementation)
    path('<int:pk>/clone/', views.clone_task, name='clone-task'),
    path('<int:pk>/assign-team/', views.assign_team, name='assign-team'),
    path('<int:pk>/manage-visibility/', views.manage_visibility, name='manage-visibility'),
    path('<int:pk>/time-log/', views.time_log, name='time-log'),
    path('<int:pk>/watchers/', views.manage_watchers, name='manage-watchers'),
    path('templates/', views.task_templates, name='task-templates'),
    path('templates/create/', views.create_template, name='create-template'),
    path('analytics/', views.task_analytics, name='task-analytics'),
    path('team-dashboard/', views.team_dashboard, name='team-dashboard'),
    
    # API endpoints
    path('api/comments/<int:task_id>/', views.add_comment, name='add-comment'),
    path('api/stats/', views.task_stats_api, name='task-stats-api'),
    path('api/search/', views.search_tasks_api, name='search-tasks-api'),
    path('api/assign/', views.assign_task_api, name='assign-task-api'),
    path('api/bulk-status/', views.bulk_status_update, name='bulk-status-update'),
    path('admin/task-submissions/', views.task_submissions_admin, name='admin-task-submissions'),
    
    # Recurring tasks
    path('recurring/', views.recurring_tasks_view, name='recurring-tasks'),
    path('recurring/select/', views.select_recurring_task, name='select-recurring-task'),
    path('recurring/templates/', views.recurring_templates_view, name='recurring-templates'),
    path('recurring/templates/create/', views.create_recurring_template, name='create-recurring-template'),
    path('recurring/generate/', views.generate_recurring_tasks_manual, name='generate-recurring-tasks'),
    
    # Bulk upload features
    path('bulk-upload/daily/', views.bulk_upload_daily_tasks, name='bulk-upload-daily'),
    path('bulk-upload/weekly/', views.bulk_upload_weekly_tasks, name='bulk-upload-weekly'),
    path('download-template/daily/', views.download_daily_template, name='download-daily-template'),
    path('download-template/weekly/', views.download_weekly_template, name='download-weekly-template'),
    path('<int:task_id>/download-file/', views.download_task_file, name='download-task-file'),

]
