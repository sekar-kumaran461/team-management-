"""
URL configuration for team_management project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from django.http import FileResponse, Http404
from django.views.decorators.http import require_http_methods
import os

def serve_sample_file(request, filename):
    """Serve sample import files"""
    file_path = os.path.join(settings.BASE_DIR, filename)
    if os.path.exists(file_path):
        return FileResponse(
            open(file_path, 'rb'),
            as_attachment=True,
            filename=filename
        )
    raise Http404("File not found")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('', include('users.urls')),
    
    path('tasks/', include('tasks.urls')),
    path('resources/', include('resources.urls')),
    path('projects/', include('projects.urls')),
    path('analytics/', include('analytics.urls')),
    path('google/', include('google_integration.simple_urls')),
    
    # Sample files for download
    path('sample_tasks_import.csv', serve_sample_file, {'filename': 'sample_tasks_import.csv'}, name='sample-csv'),
    path('sample_tasks_import.htm', serve_sample_file, {'filename': 'sample_tasks_import.htm'}, name='sample-html'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
