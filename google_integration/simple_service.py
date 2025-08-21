"""
Google Database Service - Single Account for All Users
Simple service that uses one Google account as database backend
"""
import os
import json
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

# Check if Google libraries are available
try:
    from google.oauth2.service_account import Credentials as ServiceAccountCredentials
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GOOGLE_LIBS_AVAILABLE = True
except ImportError:
    GOOGLE_LIBS_AVAILABLE = False
    # Create dummy classes for when Google libraries aren't available
    class ServiceAccountCredentials:
        @classmethod
        def from_service_account_info(cls, info, scopes=None):
            return cls()
    
    def build(service, version, credentials=None):
        return None
    
    class HttpError(Exception):
        pass

class GoogleDatabaseService:
    """Single Google Account Database Service"""
    
    def __init__(self):
        self.credentials = None
        self.drive_service = None
        self.sheets_service = None
        self.authenticated = False
        self.spreadsheet_id = getattr(settings, 'GOOGLE_DATABASE_SPREADSHEET_ID', None)
        self.available = GOOGLE_LIBS_AVAILABLE
        
    def authenticate(self):
        """Authenticate using service account (one account for all users)"""
        if not self.available:
            logger.warning("Google libraries not available, skipping authentication")
            return False
            
        try:
            # Get credentials from environment or file
            credentials_json = os.environ.get('GOOGLE_SERVICE_ACCOUNT_JSON')
            credentials_file = getattr(settings, 'GOOGLE_SERVICE_ACCOUNT_FILE', None)
            
            scopes = [
                'https://www.googleapis.com/auth/drive',
                'https://www.googleapis.com/auth/drive.file', 
                'https://www.googleapis.com/auth/spreadsheets'
            ]
            
            if credentials_json:
                # From environment variable (JSON string)
                credentials_info = json.loads(credentials_json)
                self.credentials = ServiceAccountCredentials.from_service_account_info(
                    credentials_info, scopes=scopes
                )
                logger.info("Authenticated with Google using service account from environment")
            elif credentials_file and os.path.exists(credentials_file):
                # From file
                self.credentials = ServiceAccountCredentials.from_service_account_file(
                    credentials_file, scopes=scopes
                )
                logger.info(f"Authenticated with Google using service account file: {credentials_file}")
            else:
                logger.warning("No Google service account credentials found. Please configure GOOGLE_SERVICE_ACCOUNT_JSON or GOOGLE_SERVICE_ACCOUNT_FILE")
                return False
                
            # Initialize services
            self.drive_service = build('drive', 'v3', credentials=self.credentials)
            self.sheets_service = build('sheets', 'v4', credentials=self.credentials)
            
            self.authenticated = True
            return True
            
        except Exception as e:
            logger.error(f"Google authentication failed: {e}")
            self.authenticated = False
            return False
    
    def ensure_authenticated(self):
        """Ensure service is authenticated"""
        if not self.available:
            logger.warning("Google libraries not available")
            return False
        if not self.authenticated:
            return self.authenticate()
        return True
    
    def create_database_spreadsheet(self):
        """Create the main database spreadsheet"""
        if not self.ensure_authenticated():
            return None
            
        try:
            # Create spreadsheet with multiple sheets
            spreadsheet_body = {
                'properties': {
                    'title': 'Team Management Database'
                },
                'sheets': [
                    {'properties': {'title': 'Users', 'gridProperties': {'rowCount': 1000, 'columnCount': 15}}},
                    {'properties': {'title': 'Tasks', 'gridProperties': {'rowCount': 1000, 'columnCount': 15}}},
                    {'properties': {'title': 'Projects', 'gridProperties': {'rowCount': 1000, 'columnCount': 15}}},
                    {'properties': {'title': 'Resources', 'gridProperties': {'rowCount': 1000, 'columnCount': 15}}},
                    {'properties': {'title': 'Analytics', 'gridProperties': {'rowCount': 1000, 'columnCount': 15}}}
                ]
            }
            
            spreadsheet = self.sheets_service.spreadsheets().create(body=spreadsheet_body).execute()
            self.spreadsheet_id = spreadsheet['spreadsheetId']
            
            # Setup headers
            self.setup_headers()
            
            logger.info(f"Created database spreadsheet: {self.spreadsheet_id}")
            return self.spreadsheet_id
            
        except Exception as e:
            logger.error(f"Failed to create database spreadsheet: {e}")
            return None
    
    def setup_headers(self):
        """Setup column headers for all sheets"""
        headers = {
            'Users': ['ID', 'Username', 'Email', 'First Name', 'Last Name', 'Role', 'Date Joined', 'Last Login', 'Is Active'],
            'Tasks': ['ID', 'Title', 'Description', 'Priority', 'Status', 'Assigned To', 'Created By', 'Due Date', 'Created Date'],
            'Projects': ['ID', 'Name', 'Description', 'Status', 'Team Leader', 'Members', 'Start Date', 'End Date', 'Created Date'],
            'Resources': ['ID', 'Name', 'Type', 'Description', 'File URL', 'Uploaded By', 'Category', 'Created Date', 'File Size'],
            'Analytics': ['ID', 'User ID', 'Action', 'Entity Type', 'Entity ID', 'Timestamp', 'Data']
        }
        
        for sheet_name, header_row in headers.items():
            try:
                self.update_sheet_data(sheet_name, 'A1', [header_row])
                logger.info(f"Setup headers for {sheet_name}")
            except Exception as e:
                logger.error(f"Failed to setup headers for {sheet_name}: {e}")
    
    def get_sheet_data(self, sheet_name, range_name='A:Z'):
        """Get data from a sheet"""
        if not self.ensure_authenticated():
            return []
        
        if not self.spreadsheet_id:
            logger.error("No spreadsheet ID configured")
            return []
            
        try:
            full_range = f"{sheet_name}!{range_name}"
            result = self.sheets_service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=full_range
            ).execute()
            
            return result.get('values', [])
            
        except Exception as e:
            logger.error(f"Failed to get data from {sheet_name}: {e}")
            return []
    
    def update_sheet_data(self, sheet_name, range_start, values):
        """Update data in a sheet"""
        if not self.ensure_authenticated():
            return False
        
        if not self.spreadsheet_id:
            logger.error("No spreadsheet ID configured")
            return False
            
        try:
            range_name = f"{sheet_name}!{range_start}"
            body = {'values': values}
            
            result = self.sheets_service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                body=body
            ).execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update data in {sheet_name}: {e}")
            return False
    
    def insert_row(self, sheet_name, data):
        """Insert a new row of data"""
        if not isinstance(data, list):
            data = [data]
            
        # Get existing data to find next row
        existing_data = self.get_sheet_data(sheet_name, 'A:A')
        next_row = len(existing_data) + 1
        
        return self.update_sheet_data(sheet_name, f'A{next_row}', [data])
    
    def sync_django_to_sheets(self):
        """Sync all Django data to Google Sheets"""
        if not self.ensure_authenticated():
            return False
        
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            
            # Sync Users
            users = User.objects.all()
            user_data = []
            
            for user in users:
                user_data.append([
                    str(user.id),
                    user.username,
                    user.email,
                    user.first_name,
                    user.last_name,
                    'Admin' if user.is_superuser else 'User',
                    user.date_joined.strftime('%Y-%m-%d %H:%M:%S') if user.date_joined else '',
                    user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else '',
                    'Yes' if user.is_active else 'No'
                ])
            
            # Clear existing data and add headers + new data
            all_user_data = [
                ['ID', 'Username', 'Email', 'First Name', 'Last Name', 'Role', 'Date Joined', 'Last Login', 'Is Active']
            ] + user_data
            
            success = self.update_sheet_data('Users', 'A1', all_user_data)
            
            if success:
                logger.info(f"Synced {len(user_data)} users to Google Sheets")
                return True
            else:
                logger.error("Failed to sync users to Google Sheets")
                return False
                
        except Exception as e:
            logger.error(f"Failed to sync Django data: {e}")
            return False
    
    def test_connection(self):
        """Test Google API connection"""
        if not self.ensure_authenticated():
            return False, "Authentication failed"
        
        try:
            # Try to access the spreadsheet
            if self.spreadsheet_id:
                result = self.sheets_service.spreadsheets().get(
                    spreadsheetId=self.spreadsheet_id
                ).execute()
                return True, f"Connected to spreadsheet: {result.get('properties', {}).get('title', 'Unknown')}"
            else:
                return True, "Authenticated but no spreadsheet configured"
                
        except Exception as e:
            return False, f"Connection test failed: {e}"


# Global instance
google_database = GoogleDatabaseService()
