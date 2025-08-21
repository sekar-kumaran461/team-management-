"""
URL patterns for Google Drive Integration
"""
from django.urls import path
from django.views.generic import TemplateView

app_name = 'google_integration'

urlpatterns = [
    # Setup guide
    path('', TemplateView.as_view(template_name='google_integration/setup_guide.html'), name='setup_guide'),
    path('setup/', TemplateView.as_view(template_name='google_integration/setup_guide.html'), name='setup'),
]
