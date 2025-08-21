from django.urls import path
from . import views

app_name = 'projects'

urlpatterns = [
    # Web URLs
    path('', views.ProjectListView.as_view(), name='project-list'),
    path('<int:pk>/', views.ProjectDetailView.as_view(), name='project-detail'),
    path('create/', views.ProjectCreateView.as_view(), name='project-create'),
    path('<int:pk>/edit/', views.ProjectEditView.as_view(), name='project-edit'),
    path('<int:pk>/submit/', views.ProjectSubmissionView.as_view(), name='project-submit'),
    path('<int:pk>/review/', views.WeeklyReviewView.as_view(), name='weekly-review'),
    path('my-projects/', views.MyProjectsView.as_view(), name='my-projects'),
]
