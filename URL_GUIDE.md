# Frontend URL Guide

## 🌟 Main Frontend Pages (Use These!)

### Dashboard & Navigation
- **Main Dashboard**: `http://127.0.0.1:8000/`
- **User Profile**: `http://127.0.0.1:8000/profile/`
- **Team Page**: `http://127.0.0.1:8000/team/`

### Tasks Module
- **Tasks List**: `http://127.0.0.1:8000/tasks/`
- **Create Task**: `http://127.0.0.1:8000/tasks/create/`
- **Task Detail**: `http://127.0.0.1:8000/tasks/{id}/`
- **Task Calendar**: `http://127.0.0.1:8000/tasks/calendar/`
- **Bulk Upload**: `http://127.0.0.1:8000/tasks/bulk-upload/`

### Resources Module
- **Resources List**: `http://127.0.0.1:8000/resources/`
- **Upload Resource**: `http://127.0.0.1:8000/resources/upload/`
- **Resource Detail**: `http://127.0.0.1:8000/resources/{id}/`
- **Categories**: `http://127.0.0.1:8000/resources/categories/`
- **My Uploads**: `http://127.0.0.1:8000/resources/my-uploads/`

### Projects Module
- **Projects List**: `http://127.0.0.1:8000/projects/`
- **Create Project**: `http://127.0.0.1:8000/projects/create/`
- **Project Detail**: `http://127.0.0.1:8000/projects/{id}/`
- **My Projects**: `http://127.0.0.1:8000/projects/my-projects/`

### Analytics Module
- **Analytics Dashboard**: `http://127.0.0.1:8000/analytics/`
- **Team Analytics**: `http://127.0.0.1:8000/analytics/team/`
- **Progress Tracking**: `http://127.0.0.1:8000/analytics/progress/`
- **Reports**: `http://127.0.0.1:8000/analytics/reports/`

## 🚫 API URLs (Don't Use for Frontend)

### Tasks API (Backend Only)
- `http://127.0.0.1:8000/tasks/api/tasks/`
- `http://127.0.0.1:8000/tasks/api/categories/`
- `http://127.0.0.1:8000/tasks/api/submissions/`

### Resources API (Backend Only)
- `http://127.0.0.1:8000/resources/api/resources/`
- `http://127.0.0.1:8000/resources/api/categories/`
- `http://127.0.0.1:8000/resources/api/study-materials/`

### Projects API (Backend Only)
- `http://127.0.0.1:8000/projects/api/projects/`
- `http://127.0.0.1:8000/projects/api/milestones/`
- `http://127.0.0.1:8000/projects/api/submissions/`

## ✅ Features Available

### Beautiful UI Features
- 🎨 Modern Tailwind CSS design
- 📱 Responsive layout (mobile-friendly)
- 🔍 Search and filtering
- 📄 Pagination
- 🏷️ Tags and categories
- 📊 Progress indicators
- 🎯 Priority badges
- 👤 User avatars and profiles

### Functionality
- 📝 CRUD operations (Create, Read, Update, Delete)
- 🔐 User authentication
- 👥 Team management
- 📈 Progress tracking
- 💾 File uploads
- 🔔 Notifications
- 📊 Analytics and reporting

## 🚀 Getting Started

1. Start the server: `python manage.py runserver 8000`
2. Open: `http://127.0.0.1:8000/`
3. Navigate using the top menu bar
4. Use the sidebar for quick access

## 📝 Notes

- All frontend pages use proper Django templates with Tailwind CSS
- No JSON fields are used - all proper Django model fields
- Navigation is available in the header
- Mobile-responsive design
- Clean, modern interface
