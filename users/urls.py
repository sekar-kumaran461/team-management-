from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    # Authentication URLs
    path('login/', views.LoginView.as_view(), name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    
    # Main user pages
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/edit/', views.ProfileEditView.as_view(), name='profile-edit'),
    path('team/', views.TeamView.as_view(), name='team'),
    
    # User Management (Admin/Team Lead only)
    path('manage/', views.UserManagementView.as_view(), name='user-management'),
    path('create/', views.UserCreateView.as_view(), name='user-create'),
    path('<int:pk>/', views.UserDetailView.as_view(), name='user-detail'),
    path('<int:pk>/edit/', views.UserEditView.as_view(), name='user-edit'),
    path('<int:pk>/toggle-status/', views.toggle_user_status, name='toggle-user-status'),
    path('export/', views.export_users, name='export-users'),
]
