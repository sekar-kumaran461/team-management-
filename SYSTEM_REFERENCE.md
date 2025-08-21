# Team Management System - Technical Reference

## System Overview
This Django-based team management system uses Google Drive as primary storage and Google Sheets as database backend. The system is designed for team collaboration with role-based access control.

## Core Architecture

### Apps Structure
- **users**: User management, authentication, profiles, dashboard
- **tasks**: Task management, team assignments, visibility control
- **projects**: Project management, milestones, submissions
- **resources**: Resource sharing, file management, study materials
- **analytics**: Performance tracking, reporting, user activity
- **google_integration**: Google Drive/Sheets integration, OAuth, sync

## Key Models & Relationships

### User System
- **User**: Extended Django user with team roles (Admin/Manager/Team Lead/Senior Developer/Team Member/Contributor)
- **UserProfile**: Additional user information, progress tracking
- **UserActivity**: Activity logging for analytics

### Task Management
- **Task**: Core task model with team visibility logic
- **TaskFile**: Files attached to tasks (stored in Google Drive)
- **TaskFileUploadBatch**: Batch file upload tracking
- **TaskSubmission**: Task completion submissions
- **TaskComment**: Team collaboration comments

### Project Management
- **Project**: Projects with team member assignments
- **ProjectMilestone**: Project milestones and deadlines
- **ProjectSubmission**: Project deliverable submissions
- **WeeklyProjectReview**: Regular progress reviews

### Resource Management
- **Resource**: Shared team resources (stored in Google Drive)
- **ResourceCategory**: Resource categorization
- **ResourceFile**: Individual files within resources
- **StudyMaterial**: Learning materials and documentation

### Google Integration
- **GoogleDriveConfig**: Drive integration configuration
- **GoogleDriveFolder**: Folder structure mapping
- **GoogleDriveFile**: File metadata and links
- **GoogleSheetsTable**: Sheets as database tables
- **UserGoogleAuth**: User-specific OAuth tokens

## Google Integration Services

### GoogleDatabaseService
- **Purpose**: Core Google API authentication and operations
- **Key Methods**:
  - `authenticate()`: Service account authentication
  - `list_files()`: Drive file listing
  - `create_folder()`: Drive folder creation
  - `upload_file()`: File upload to Drive
  - `create_spreadsheet()`: Sheets creation
  - `get/update_spreadsheet_data()`: Sheets data operations

### GoogleDriveService
- **Purpose**: File-specific operations for tasks/resources
- **Key Methods**:
  - `upload_file()`: Upload file objects from Django
  - `get_or_create_folder()`: Folder path management
  - `delete_file()`: File deletion
  - `get_file_info()`: File metadata retrieval

### GoogleSheetsDatabase
- **Purpose**: Use Google Sheets as database backend
- **Key Methods**:
  - `setup_database_sheets()`: Initialize sheet structure
  - `insert_data()`: Add new records
  - `get_data()`: Retrieve records
  - `update_data()`: Modify existing records
  - `search_data()`: Query records

## Team Management Features

### Visibility Logic
- **Admin/Manager Created Tasks**: Visible to all team members by default
- **Team Assignment Options**:
  - Specific person assignment
  - Multiple team member assignment
  - Public tasks (visible/claimable by all)
- **Permission Levels**: Role-based task access control

### File Storage Strategy
- **Google Drive Structure**:
  ```
  /team_management/
    /tasks/
      /{task_id}/
        - attachments
        - submissions
    /projects/
      /{project_id}/
        - deliverables
        - documentation
    /resources/
      /{category}/
        - shared files
        - study materials
    /uploads/
      /temp/
        - temporary uploads
  ```

### Database Integration
- **Local SQLite**: Django models for relationships and queries
- **Google Sheets**: Long-term data storage and backup
- **Sync Strategy**: Periodic synchronization between local and Sheets

## Views Architecture

### User Views
- **DashboardView**: Main team dashboard with task/project overview
- **ProfileView**: User profile management
- **Team member statistics and progress tracking

### Task Views  
- **TaskListView**: Team task listing with visibility filtering
- **TaskDetailView**: Comprehensive task details with team features
- **TaskCreateView**: Advanced task creation with team assignment
- **Team management views**: clone, assign, visibility management

### Project Views
- **ProjectListView**: Team project overview
- **ProjectDetailView**: Project details with milestones/submissions
- **Submission and review management

### Resource Views
- **ResourceListView**: Shared resource library
- **ResourceUploadView**: File upload to Google Drive
- **Category and study material management

### Analytics Views
- **AnalyticsDashboardView**: Team performance analytics
- **Progress tracking and reporting
- **Leaderboard and team statistics

### Google Integration Views
- **GoogleDriveIntegrationView**: Drive dashboard
- **OAuth flow management
- **Sync and configuration management

## URL Patterns

### Core URLs
- `/users/`: User management and dashboard
- `/tasks/`: Task management with team features
- `/projects/`: Project collaboration
- `/resources/`: Resource sharing
- `/analytics/`: Performance tracking
- `/google/`: Google integration management

### API Endpoints
- `/api/tasks/`: Task CRUD operations
- `/api/projects/`: Project management
- `/api/resources/`: Resource access
- `/api/analytics/`: Analytics data
- `/api/google/`: Google integration APIs

## Template Structure

### Base Templates
- **base.html**: Main layout with Tailwind CSS
- **Navigation**: Role-based menu structure
- **Common components**: Modals, forms, notifications

### Task Templates
- **task_list.html**: Team task overview
- **task_detail_team.html**: Comprehensive task view
- **my_tasks.html**: Personal task dashboard
- **team_dashboard.html**: Team performance dashboard
- **create_team.html**: Advanced task creation
- **templates.html**: Task template management
- **analytics.html**: Task analytics
- **bulk_upload.html**: Bulk task import

### Responsive Design
- **Framework**: Tailwind CSS for consistent styling
- **Components**: Reusable UI components
- **Charts**: Chart.js integration for analytics
- **Modals**: Coming soon features and interactions

## Security & Permissions

### Authentication
- **Django Auth**: Session-based authentication
- **Google OAuth**: For Drive/Sheets access
- **Role-based Access**: Team hierarchy enforcement

### File Security
- **Google Drive**: Service account with controlled access
- **File Sharing**: Team-based permissions
- **Upload Validation**: File type and size restrictions

## Development Guidelines

### Google Integration
1. Always check service authentication before operations
2. Handle API rate limits and errors gracefully
3. Implement proper logging for debugging
4. Use batch operations for efficiency

### Template Development
1. Use Tailwind CSS classes consistently
2. Implement responsive design patterns
3. Add "coming soon" modals for unimplemented features
4. Ensure accessibility standards

### Database Strategy
1. Use Django models for relationships and queries
2. Sync important data to Google Sheets for backup
3. Implement proper error handling for sync operations
4. Monitor API quotas and usage

## Future Enhancements

### Planned Features
- Advanced task templates and automation
- AI-powered workload balancing
- Real-time collaboration features
- Advanced analytics and reporting
- Mobile application support
- Integration with additional Google Workspace tools

### Technical Improvements
- Caching layer for Google API responses
- Background task processing
- Advanced search and filtering
- Real-time notifications
- Performance optimization

## Configuration Requirements

### Google API Setup
```python
GOOGLE_SERVICE_ACCOUNT_FILE = 'path/to/service-account.json'
GOOGLE_DRIVE_ENABLED = True
GOOGLE_SHEETS_DATABASE_ID = 'spreadsheet_id'
```

### Required Scopes
- `https://www.googleapis.com/auth/drive`
- `https://www.googleapis.com/auth/drive.file`
- `https://www.googleapis.com/auth/spreadsheets`

This system provides a complete team management solution with Google integration for storage and data persistence, designed for scalability and team collaboration.
