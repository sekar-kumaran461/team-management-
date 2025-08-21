"""
Google Drive and Sheets API Service Configuration - Single Account Database
"""
import os
import json
from google.oauth2.service_account import Credentials as ServiceAccountCredentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from django.conf import settings
import gspread
import logging

logger = logging.getLogger(__name__)

class GoogleDatabaseService:
    """Single Google Account Database Service Manager"""
    
    def __init__(self):
        self.credentials = None
        self.drive_service = None
        self.sheets_service = None
        self.gc = None  # gspread client
        self.authenticated = False
        
    def authenticate(self):
        """Authenticate using service account credentials (single account for all users)"""
        try:
            # Try to get credentials from settings
            credentials_path = getattr(settings, 'GOOGLE_SERVICE_ACCOUNT_FILE', None)
            credentials_json = getattr(settings, 'GOOGLE_SERVICE_ACCOUNT_JSON', None)
            
            scopes = [
                'https://www.googleapis.com/auth/drive',
                'https://www.googleapis.com/auth/drive.file', 
                'https://www.googleapis.com/auth/spreadsheets'
            ]
            
            if credentials_path and os.path.exists(credentials_path):
                # Use service account file
                self.credentials = ServiceAccountCredentials.from_service_account_file(
                    credentials_path, scopes=scopes
                )
            elif credentials_json:
                # Use service account JSON (for environment variables)
                credentials_info = json.loads(credentials_json)
                self.credentials = ServiceAccountCredentials.from_service_account_info(
                    credentials_info, scopes=scopes
                )
            else:
                logger.error("No Google service account credentials found")
                return False
                
            # Initialize services
            self.drive_service = build('drive', 'v3', credentials=self.credentials)
            self.sheets_service = build('sheets', 'v4', credentials=self.credentials)
            self.gc = gspread.authorize(self.credentials)
            
            self.authenticated = True
            logger.info("Google Database Service authenticated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Google Database authentication failed: {e}")
            self.authenticated = False
            return False
    
    def list_files(self, query="", max_results=100):
        """List files in Google Drive"""
        if not self.drive_service:
            return []
            
        try:
            results = self.drive_service.files().list(
                q=query,
                pageSize=max_results,
                fields="nextPageToken, files(id, name, mimeType, createdTime, modifiedTime, size, parents)"
            ).execute()
            
            return results.get('files', [])
        except HttpError as e:
            logger.error(f"Failed to list files: {e}")
            return []
    
    def create_folder(self, name, parent_id=None):
        """Create a folder in Google Drive"""
        if not self.drive_service:
            return None
            
        try:
            file_metadata = {
                'name': name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            
            if parent_id:
                file_metadata['parents'] = [parent_id]
                
            folder = self.drive_service.files().create(
                body=file_metadata,
                fields='id, name'
            ).execute()
            
            logger.info(f"Created folder: {folder.get('name')} with ID: {folder.get('id')}")
            return folder
        except HttpError as e:
            logger.error(f"Failed to create folder: {e}")
            return None
    
    def upload_file(self, file_path, name, parent_id=None, mime_type=None):
        """Upload a file to Google Drive"""
        if not self.drive_service:
            return None
            
        try:
            from googleapiclient.http import MediaFileUpload
            
            file_metadata = {'name': name}
            if parent_id:
                file_metadata['parents'] = [parent_id]
                
            media = MediaFileUpload(file_path, mimetype=mime_type, resumable=True)
            
            file = self.drive_service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name, webViewLink'
            ).execute()
            
            logger.info(f"Uploaded file: {file.get('name')} with ID: {file.get('id')}")
            return file
        except HttpError as e:
            logger.error(f"Failed to upload file: {e}")
            return None
    
    def create_spreadsheet(self, title, sheets_data=None):
        """Create a Google Spreadsheet"""
        if not self.sheets_service:
            return None
            
        try:
            spreadsheet_body = {
                'properties': {'title': title}
            }
            
            if sheets_data:
                spreadsheet_body['sheets'] = sheets_data
                
            spreadsheet = self.sheets_service.spreadsheets().create(
                body=spreadsheet_body
            ).execute()
            
            logger.info(f"Created spreadsheet: {title} with ID: {spreadsheet.get('spreadsheetId')}")
            return spreadsheet
        except HttpError as e:
            logger.error(f"Failed to create spreadsheet: {e}")
            return None
    
    def get_spreadsheet_data(self, spreadsheet_id, range_name):
        """Get data from a Google Spreadsheet"""
        if not self.sheets_service:
            return None
            
        try:
            result = self.sheets_service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=range_name
            ).execute()
            
            return result.get('values', [])
        except HttpError as e:
            logger.error(f"Failed to get spreadsheet data: {e}")
            return None
    
    def update_spreadsheet_data(self, spreadsheet_id, range_name, values):
        """Update data in a Google Spreadsheet"""
        if not self.sheets_service:
            return None
            
        try:
            body = {
                'values': values
            }
            
            result = self.sheets_service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                body=body
            ).execute()
            
            logger.info(f"Updated {result.get('updatedCells')} cells in spreadsheet")
            return result
        except HttpError as e:
            logger.error(f"Failed to update spreadsheet data: {e}")
            return None


# Global service instance
google_service = GoogleDatabaseService()


class GoogleSheetsDatabase:
    """
    Google Sheets as Database Manager
    Provides database-like operations on Google Sheets
    """
    
    def __init__(self, spreadsheet_id=None):
        self.spreadsheet_id = spreadsheet_id
        self.service = google_service
        
    def setup_database_sheets(self):
        """Setup database structure in Google Sheets"""
        sheets_to_create = [
            {
                'properties': {
                    'title': 'Users',
                    'gridProperties': {'rowCount': 1000, 'columnCount': 26}
                }
            },
            {
                'properties': {
                    'title': 'Tasks', 
                    'gridProperties': {'rowCount': 1000, 'columnCount': 26}
                }
            },
            {
                'properties': {
                    'title': 'Projects',
                    'gridProperties': {'rowCount': 1000, 'columnCount': 26}
                }
            },
            {
                'properties': {
                    'title': 'Resources',
                    'gridProperties': {'rowCount': 1000, 'columnCount': 26}
                }
            },
            {
                'properties': {
                    'title': 'Analytics',
                    'gridProperties': {'rowCount': 1000, 'columnCount': 26}
                }
            }
        ]
        
        if not self.spreadsheet_id:
            # Create new spreadsheet
            spreadsheet = self.service.create_spreadsheet(
                "Team Management Database",
                sheets_to_create
            )
            if spreadsheet:
                self.spreadsheet_id = spreadsheet['spreadsheetId']
                
                # Setup headers for each sheet
                self.setup_headers()
                return self.spreadsheet_id
        return None
    
    def setup_headers(self):
        """Setup column headers for database sheets"""
        headers = {
            'Users': ['ID', 'Username', 'Email', 'First Name', 'Last Name', 'Role', 'Created Date', 'Last Login'],
            'Tasks': ['ID', 'Title', 'Description', 'Priority', 'Status', 'Assigned To', 'Created By', 'Due Date', 'Created Date'],
            'Projects': ['ID', 'Name', 'Description', 'Status', 'Team Leader', 'Members', 'Start Date', 'End Date', 'Created Date'],
            'Resources': ['ID', 'Name', 'Type', 'Description', 'File URL', 'Uploaded By', 'Category', 'Created Date'],
            'Analytics': ['ID', 'User ID', 'Action', 'Entity Type', 'Entity ID', 'Timestamp', 'Data']
        }
        
        for sheet_name, header_row in headers.items():
            self.service.update_spreadsheet_data(
                self.spreadsheet_id,
                f"{sheet_name}!A1:{chr(65 + len(header_row) - 1)}1",
                [header_row]
            )
    
    def insert_data(self, sheet_name, data):
        """Insert data into a specific sheet"""
        if isinstance(data, dict):
            data = [list(data.values())]
        elif not isinstance(data, list):
            data = [data]
            
        # Find next empty row
        existing_data = self.service.get_spreadsheet_data(
            self.spreadsheet_id,
            f"{sheet_name}!A:A"
        )
        next_row = len(existing_data) + 1
        
        range_name = f"{sheet_name}!A{next_row}"
        return self.service.update_spreadsheet_data(
            self.spreadsheet_id,
            range_name,
            data
        )
    
    def get_data(self, sheet_name, range_name=None):
        """Get data from a specific sheet"""
        if not range_name:
            range_name = f"{sheet_name}!A:Z"
        else:
            range_name = f"{sheet_name}!{range_name}"
            
        return self.service.get_spreadsheet_data(
            self.spreadsheet_id,
            range_name
        )
    
    def update_data(self, sheet_name, range_name, data):
        """Update data in a specific sheet"""
        full_range = f"{sheet_name}!{range_name}"
        return self.service.update_spreadsheet_data(
            self.spreadsheet_id,
            full_range,
            data
        )
    
    def search_data(self, sheet_name, column, value):
        """Search for data in a specific column"""
        data = self.get_data(sheet_name)
        if not data:
            return []
            
        headers = data[0] if data else []
        if column not in headers:
            return []
            
        column_index = headers.index(column)
        results = []
        
        for row_index, row in enumerate(data[1:], start=2):
            if len(row) > column_index and row[column_index] == value:
                results.append({
                    'row_number': row_index,
                    'data': dict(zip(headers, row))
                })
                
        return results


# Global database instance
google_db = GoogleSheetsDatabase()


class GoogleDriveService:
    """Google Drive Service for file operations"""
    
    def __init__(self):
        self.service = google_service
        if not self.service.authenticated:
            self.service.authenticate()
    
    def upload_file(self, file_obj, folder_path="", description=""):
        """Upload a file object to Google Drive"""
        if not self.service.drive_service:
            return None
            
        try:
            from googleapiclient.http import MediaIoBaseUpload
            import io
            
            # Create folder if it doesn't exist
            parent_id = None
            if folder_path:
                parent_id = self.get_or_create_folder(folder_path)
            
            file_metadata = {
                'name': file_obj.name,
                'description': description
            }
            
            if parent_id:
                file_metadata['parents'] = [parent_id]
            
            # Handle file upload
            if hasattr(file_obj, 'read'):
                file_content = file_obj.read()
                if hasattr(file_obj, 'seek'):
                    file_obj.seek(0)  # Reset file pointer
            else:
                file_content = file_obj
            
            media = MediaIoBaseUpload(
                io.BytesIO(file_content),
                mimetype='application/octet-stream',
                resumable=True
            )
            
            file = self.service.drive_service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name, webViewLink, webContentLink'
            ).execute()
            
            logger.info(f"Uploaded file: {file.get('name')} with ID: {file.get('id')}")
            return file
            
        except Exception as e:
            logger.error(f"Failed to upload file: {e}")
            return None
    
    def get_or_create_folder(self, folder_path):
        """Get or create a folder path in Google Drive"""
        if not folder_path:
            return None
            
        folders = folder_path.strip('/').split('/')
        parent_id = None
        
        for folder_name in folders:
            if not folder_name:
                continue
                
            # Search for existing folder
            query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'"
            if parent_id:
                query += f" and '{parent_id}' in parents"
            
            results = self.service.list_files(query)
            
            if results:
                parent_id = results[0]['id']
            else:
                # Create folder
                folder = self.service.create_folder(folder_name, parent_id)
                if folder:
                    parent_id = folder['id']
                else:
                    return None
        
        return parent_id
    
    def delete_file(self, file_id):
        """Delete a file from Google Drive"""
        if not self.service.drive_service:
            return False
            
        try:
            self.service.drive_service.files().delete(fileId=file_id).execute()
            logger.info(f"Deleted file with ID: {file_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete file: {e}")
            return False
    
    def get_file_info(self, file_id):
        """Get file information from Google Drive"""
        if not self.service.drive_service:
            return None
            
        try:
            file = self.service.drive_service.files().get(
                fileId=file_id,
                fields='id, name, mimeType, size, createdTime, modifiedTime, webViewLink, webContentLink'
            ).execute()
            return file
        except Exception as e:
            logger.error(f"Failed to get file info: {e}")
            return None
