from django.urls import path
from . import views

app_name = 'resources'

urlpatterns = [
    # Web URLs
    path('', views.ResourceListView.as_view(), name='resource-list'),
    path('<int:pk>/', views.ResourceDetailView.as_view(), name='resource-detail'),
    path('upload/', views.ResourceUploadView.as_view(), name='resource-upload'),
    path('<int:pk>/edit/', views.ResourceEditView.as_view(), name='resource-edit'),
    path('<int:pk>/download/', views.ResourceDownloadView.as_view(), name='resource-download'),
    path('categories/', views.ResourceCategoryListView.as_view(), name='category-list'),
    path('study-materials/', views.StudyMaterialListView.as_view(), name='study-materials'),
    path('my-uploads/', views.MyResourcesView.as_view(), name='my-uploads'),
]
