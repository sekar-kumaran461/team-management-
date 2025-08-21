"""
Simple Google Database Views - Single Account for All Users
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.conf import settings
import logging

from .simple_service import google_database

logger = logging.getLogger(__name__)


class GoogleDatabaseDashboard(LoginRequiredMixin, TemplateView):
    """Simple dashboard for Google Database"""
    template_name = 'google_integration/simple_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Test connection
        connected, message = google_database.test_connection()
        
        context.update({
            'connected': connected,
            'connection_message': message,
            'spreadsheet_id': google_database.spreadsheet_id,
            'has_credentials': bool(google_database.credentials),
        })
        
        if connected and google_database.spreadsheet_id:
            # Get some sample data
            try:
                users_data = google_database.get_sheet_data('Users', 'A1:I10')
                tasks_data = google_database.get_sheet_data('Tasks', 'A1:I10')
                
                context.update({
                    'users_count': len(users_data) - 1 if users_data else 0,  # -1 for header
                    'tasks_count': len(tasks_data) - 1 if tasks_data else 0,
                    'users_sample': users_data[:6] if users_data else [],
                    'tasks_sample': tasks_data[:6] if tasks_data else [],
                })
            except Exception as e:
                logger.error(f"Failed to get sample data: {e}")
        
        return context


@login_required
def setup_database(request):
    """Setup the Google Sheets database"""
    try:
        spreadsheet_id = google_database.create_database_spreadsheet()
        
        if spreadsheet_id:
            messages.success(
                request, 
                f'Database spreadsheet created successfully! '
                f'Spreadsheet ID: {spreadsheet_id}. '
                f'Please add this ID to your settings as GOOGLE_DATABASE_SPREADSHEET_ID.'
            )
        else:
            messages.error(request, 'Failed to create database spreadsheet. Please check your Google credentials.')
            
    except Exception as e:
        logger.error(f"Setup database failed: {e}")
        messages.error(request, f'Setup failed: {e}')
    
    return redirect('google_integration:dashboard')


@login_required
def sync_to_sheets(request):
    """Sync Django data to Google Sheets"""
    try:
        success = google_database.sync_django_to_sheets()
        
        if success:
            messages.success(request, 'Successfully synced data to Google Sheets!')
        else:
            messages.error(request, 'Failed to sync data to Google Sheets.')
            
    except Exception as e:
        logger.error(f"Sync failed: {e}")
        messages.error(request, f'Sync failed: {e}')
    
    return redirect('google_integration:dashboard')


@login_required
def test_connection(request):
    """Test Google API connection"""
    try:
        connected, message = google_database.test_connection()
        
        if connected:
            messages.success(request, f'Connection successful: {message}')
        else:
            messages.error(request, f'Connection failed: {message}')
            
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        messages.error(request, f'Connection test failed: {e}')
    
    return redirect('google_integration:dashboard')


def get_sheet_data_api(request):
    """API endpoint to get sheet data"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    sheet_name = request.GET.get('sheet', 'Users')
    range_name = request.GET.get('range', 'A1:Z100')
    
    try:
        data = google_database.get_sheet_data(sheet_name, range_name)
        
        return JsonResponse({
            'success': True,
            'data': data,
            'count': len(data)
        })
        
    except Exception as e:
        logger.error(f"Failed to get sheet data: {e}")
        return JsonResponse({'error': str(e)}, status=500)


class GoogleDatabaseSetupGuide(TemplateView):
    """Setup guide for Google Database"""
    template_name = 'google_integration/setup_guide.html'

@login_required
def file_manager(request):
    """File manager view for Google Drive integration"""
    return render(request, 'google_integration/file_manager.html', {
        'page_title': 'File Manager',
        'message': 'File management functionality coming soon!'
    })

@login_required  
def upload_file(request):
    """Upload file to Google Drive"""
    if request.method == 'POST':
        messages.info(request, 'File upload functionality coming soon!')
    return redirect('google_integration:file_manager')

@login_required
def sync_files(request):
    """Sync files between local storage and Google Drive"""
    messages.info(request, 'File sync functionality coming soon!')
    return redirect('google_integration:file_manager')

@login_required
def sync_status(request):
    """View sync status and logs"""
    return render(request, 'google_integration/sync_status.html', {
        'page_title': 'Sync Status', 
        'message': 'Sync status monitoring coming soon!'
    })

@login_required
def view_logs(request):
    """View Google integration logs"""
    return render(request, 'google_integration/logs.html', {
        'page_title': 'Integration Logs',
        'message': 'Log viewing functionality coming soon!'
    })

def sync_status_api(request):
    """API endpoint for sync status"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    return JsonResponse({
        'status': 'connected',
        'last_sync': '2025-01-15 10:30:00',
        'next_sync': '2025-01-15 11:30:00',
        'message': 'Sync status API coming soon!'
    })
