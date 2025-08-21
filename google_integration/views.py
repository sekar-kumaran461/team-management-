"""
Views for Google Drive Integration
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseRedirect, HttpResponse
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.conf import settings
import json
import logging

from .models import (
    GoogleDriveConfig, GoogleDriveFolder, GoogleDriveFile,
    GoogleSheetsTable, GoogleDriveSyncLog, UserGoogleAuth
)
from .services import google_service, google_db

logger = logging.getLogger(__name__)


class GoogleDriveIntegrationView(LoginRequiredMixin, ListView):
    """Main Google Drive integration dashboard"""
    template_name = 'google_integration/dashboard.html'
    context_object_name = 'files'
    paginate_by = 20
    
    def get_queryset(self):
        return GoogleDriveFile.objects.filter(
            uploaded_by=self.request.user
        ).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'folders': GoogleDriveFolder.objects.all()[:10],
            'recent_syncs': GoogleDriveSyncLog.objects.filter(
                initiated_by=self.request.user
            )[:5],
            'user_auth': UserGoogleAuth.objects.filter(user=self.request.user).first(),
            'configs': GoogleDriveConfig.objects.filter(is_active=True),
        })
        return context


class GoogleDriveConfigView(LoginRequiredMixin, ListView):
    """Google Drive configuration management"""
    model = GoogleDriveConfig
    template_name = 'google_integration/config.html'
    context_object_name = 'configs'


@login_required
def google_auth_start(request):
    """Start Google OAuth flow"""
    try:
        flow = google_service.create_oauth_flow()
        if not flow:
            messages.error(request, "Failed to initialize Google OAuth flow. Please check configuration.")
            return redirect('google_integration:dashboard')
        
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true'
        )
        
        request.session['google_auth_state'] = state
        return HttpResponseRedirect(authorization_url)
        
    except Exception as e:
        logger.error(f"Google auth start failed: {e}")
        messages.error(request, f"Authentication failed: {e}")
        return redirect('google_integration:dashboard')


@login_required
def google_auth_callback(request):
    """Handle Google OAuth callback"""
    try:
        code = request.GET.get('code')
        state = request.GET.get('state')
        stored_state = request.session.get('google_auth_state')
        
        if not code:
            messages.error(request, "Authorization code not received from Google.")
            return redirect('google_integration:dashboard')
        
        if state != stored_state:
            messages.error(request, "Invalid state parameter. Please try again.")
            return redirect('google_integration:dashboard')
        
        # Exchange code for credentials
        flow = google_service.create_oauth_flow()
        flow.fetch_token(code=code)
        
        credentials = flow.credentials
        
        # Store credentials
        user_auth, created = UserGoogleAuth.objects.get_or_create(
            user=request.user,
            defaults={
                'access_token': credentials.token,
                'refresh_token': credentials.refresh_token,
                'token_expiry': credentials.expiry,
                'scopes': credentials.scopes or []
            }
        )
        
        if not created:
            user_auth.access_token = credentials.token
            user_auth.refresh_token = credentials.refresh_token
            user_auth.token_expiry = credentials.expiry
            user_auth.scopes = credentials.scopes or []
            user_auth.save()
        
        # Initialize service with user credentials
        google_service.authenticate_oauth(credentials)
        
        messages.success(request, "Successfully connected to Google Drive!")
        return redirect('google_integration:dashboard')
        
    except Exception as e:
        logger.error(f"Google auth callback failed: {e}")
        messages.error(request, f"Authentication failed: {e}")
        return redirect('google_integration:dashboard')


@login_required
def google_drive_sync(request):
    """Sync files with Google Drive"""
    try:
        # Check if user is authenticated
        user_auth = UserGoogleAuth.objects.filter(user=request.user).first()
        if not user_auth or user_auth.is_expired():
            messages.warning(request, "Please authenticate with Google Drive first.")
            return redirect('google_integration:auth_start')
        
        # Authenticate service
        credentials = user_auth.get_credentials()
        google_service.authenticate_oauth(credentials)
        
        # Sync files
        files = google_service.list_files()
        synced_count = 0
        
        for file_data in files:
            # Skip folders for now
            if file_data.get('mimeType') == 'application/vnd.google-apps.folder':
                continue
            
            file_obj, created = GoogleDriveFile.objects.update_or_create(
                drive_id=file_data['id'],
                defaults={
                    'name': file_data['name'],
                    'mime_type': file_data.get('mimeType', ''),
                    'size': int(file_data.get('size', 0)) if file_data.get('size') else None,
                    'web_view_link': file_data.get('webViewLink'),
                    'web_content_link': file_data.get('webContentLink'),
                    'created_time': file_data.get('createdTime'),
                    'modified_time': file_data.get('modifiedTime'),
                    'last_synced': timezone.now(),
                    'sync_status': 'completed',
                    'uploaded_by': request.user if created else file_obj.uploaded_by
                }
            )
            
            # Determine file type
            file_obj.file_type = file_obj.get_file_type()
            file_obj.save()
            
            synced_count += 1
        
        messages.success(request, f"Successfully synced {synced_count} files from Google Drive.")
        
    except Exception as e:
        logger.error(f"Google Drive sync failed: {e}")
        messages.error(request, f"Sync failed: {e}")
    
    return redirect('google_integration:dashboard')


@login_required
def setup_database_sheets(request):
    """Setup Google Sheets as database"""
    try:
        # Check authentication
        user_auth = UserGoogleAuth.objects.filter(user=request.user).first()
        if not user_auth or user_auth.is_expired():
            messages.warning(request, "Please authenticate with Google Drive first.")
            return redirect('google_integration:auth_start')
        
        # Authenticate service
        credentials = user_auth.get_credentials()
        google_service.authenticate_oauth(credentials)
        
        # Setup database sheets
        spreadsheet_id = google_db.setup_database_sheets()
        
        if spreadsheet_id:
            # Update or create config
            config, created = GoogleDriveConfig.objects.get_or_create(
                name='Default Database',
                defaults={
                    'config_type': 'oauth',
                    'database_spreadsheet_id': spreadsheet_id,
                    'is_active': True
                }
            )
            
            if not created:
                config.database_spreadsheet_id = spreadsheet_id
                config.save()
            
            google_db.spreadsheet_id = spreadsheet_id
            
            messages.success(request, f"Database spreadsheet created successfully! ID: {spreadsheet_id}")
        else:
            messages.error(request, "Failed to create database spreadsheet.")
            
    except Exception as e:
        logger.error(f"Database setup failed: {e}")
        messages.error(request, f"Database setup failed: {e}")
    
    return redirect('google_integration:dashboard')


@login_required
def upload_to_drive(request):
    """Upload file to Google Drive"""
    if request.method == 'POST' and request.FILES.get('file'):
        try:
            uploaded_file = request.FILES['file']
            folder_id = request.POST.get('folder_id')
            
            # Check authentication
            user_auth = UserGoogleAuth.objects.filter(user=request.user).first()
            if not user_auth or user_auth.is_expired():
                return JsonResponse({'error': 'Please authenticate with Google Drive first.'})
            
            # Authenticate service
            credentials = user_auth.get_credentials()
            google_service.authenticate_oauth(credentials)
            
            # Save file temporarily
            import tempfile
            import os
            
            with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                for chunk in uploaded_file.chunks():
                    tmp_file.write(chunk)
                tmp_file_path = tmp_file.name
            
            try:
                # Upload to Google Drive
                drive_file = google_service.upload_file(
                    tmp_file_path,
                    uploaded_file.name,
                    folder_id,
                    uploaded_file.content_type
                )
                
                if drive_file:
                    # Save to local database
                    file_obj = GoogleDriveFile.objects.create(
                        name=uploaded_file.name,
                        drive_id=drive_file['id'],
                        mime_type=uploaded_file.content_type,
                        size=uploaded_file.size,
                        web_view_link=drive_file.get('webViewLink'),
                        uploaded_by=request.user,
                        sync_status='completed',
                        last_synced=timezone.now()
                    )
                    
                    file_obj.file_type = file_obj.get_file_type()
                    file_obj.save()
                    
                    return JsonResponse({
                        'success': True,
                        'file_id': drive_file['id'],
                        'file_name': uploaded_file.name,
                        'web_view_link': drive_file.get('webViewLink')
                    })
                else:
                    return JsonResponse({'error': 'Failed to upload file to Google Drive.'})
                    
            finally:
                # Clean up temporary file
                os.unlink(tmp_file_path)
                
        except Exception as e:
            logger.error(f"File upload failed: {e}")
            return JsonResponse({'error': f'Upload failed: {e}'})
    
    return JsonResponse({'error': 'No file provided or invalid request method.'})


@login_required
def create_drive_folder(request):
    """Create folder in Google Drive"""
    if request.method == 'POST':
        try:
            folder_name = request.POST.get('folder_name')
            parent_id = request.POST.get('parent_id')
            
            if not folder_name:
                return JsonResponse({'error': 'Folder name is required.'})
            
            # Check authentication
            user_auth = UserGoogleAuth.objects.filter(user=request.user).first()
            if not user_auth or user_auth.is_expired():
                return JsonResponse({'error': 'Please authenticate with Google Drive first.'})
            
            # Authenticate service
            credentials = user_auth.get_credentials()
            google_service.authenticate_oauth(credentials)
            
            # Create folder
            drive_folder = google_service.create_folder(folder_name, parent_id)
            
            if drive_folder:
                # Save to local database
                parent_folder = None
                if parent_id:
                    parent_folder = GoogleDriveFolder.objects.filter(drive_id=parent_id).first()
                
                folder_obj = GoogleDriveFolder.objects.create(
                    name=folder_name,
                    drive_id=drive_folder['id'],
                    parent_folder=parent_folder,
                    sync_status='completed',
                    last_synced=timezone.now()
                )
                
                return JsonResponse({
                    'success': True,
                    'folder_id': drive_folder['id'],
                    'folder_name': folder_name
                })
            else:
                return JsonResponse({'error': 'Failed to create folder in Google Drive.'})
                
        except Exception as e:
            logger.error(f"Folder creation failed: {e}")
            return JsonResponse({'error': f'Failed to create folder: {e}'})
    
    return JsonResponse({'error': 'Invalid request method.'})


class GoogleDriveFileDetailView(LoginRequiredMixin, DetailView):
    """Detail view for Google Drive file"""
    model = GoogleDriveFile
    template_name = 'google_integration/file_detail.html'
    context_object_name = 'file'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['sync_logs'] = GoogleDriveSyncLog.objects.filter(
            file=self.object
        ).order_by('-started_at')[:10]
        return context


class GoogleDriveSyncLogView(LoginRequiredMixin, ListView):
    """View sync logs"""
    model = GoogleDriveSyncLog
    template_name = 'google_integration/sync_logs.html'
    context_object_name = 'logs'
    paginate_by = 20
    
    def get_queryset(self):
        return GoogleDriveSyncLog.objects.filter(
            initiated_by=self.request.user
        ).order_by('-started_at')


@login_required
def database_operations(request):
    """Handle database operations with Google Sheets"""
    if request.method == 'POST':
        action = request.POST.get('action')
        
        try:
            # Check authentication and setup
            user_auth = UserGoogleAuth.objects.filter(user=request.user).first()
            if not user_auth or user_auth.is_expired():
                return JsonResponse({'error': 'Please authenticate with Google Drive first.'})
            
            # Get database spreadsheet ID
            config = GoogleDriveConfig.objects.filter(is_active=True).first()
            if not config or not config.database_spreadsheet_id:
                return JsonResponse({'error': 'Database not configured. Please setup database first.'})
            
            # Authenticate and setup database
            credentials = user_auth.get_credentials()
            google_service.authenticate_oauth(credentials)
            google_db.spreadsheet_id = config.database_spreadsheet_id
            
            if action == 'insert':
                sheet_name = request.POST.get('sheet_name')
                data = json.loads(request.POST.get('data', '{}'))
                
                result = google_db.insert_data(sheet_name, data)
                if result:
                    return JsonResponse({'success': True, 'message': f'Data inserted into {sheet_name}'})
                else:
                    return JsonResponse({'error': 'Failed to insert data'})
                    
            elif action == 'get':
                sheet_name = request.POST.get('sheet_name')
                range_name = request.POST.get('range_name')
                
                data = google_db.get_data(sheet_name, range_name)
                return JsonResponse({'success': True, 'data': data})
                
            elif action == 'search':
                sheet_name = request.POST.get('sheet_name')
                column = request.POST.get('column')
                value = request.POST.get('value')
                
                results = google_db.search_data(sheet_name, column, value)
                return JsonResponse({'success': True, 'results': results})
                
        except Exception as e:
            logger.error(f"Database operation failed: {e}")
            return JsonResponse({'error': f'Operation failed: {e}'})
    
    return JsonResponse({'error': 'Invalid request method.'})
