# Django AI Builder Project

## Overview
A Django application that generates complete Django projects dynamically using AI. Users can create projects through a web interface, and the system generates containerized Django applications with full CRUD functionality.

## Architecture
- **Backend**: Django REST API
- **Frontend**: Web interface for project creation and management
- **Container System**: Docker-based project isolation
- **Project Generation**: AI-powered code generation using smart templates

## Key Components

### Core Services
- `ai_builder/services/smart_project_generator.py` - Main project generation logic
- `ai_builder/services/container_manager.py` - Docker container management
- `ai_builder/models.py` - Database models for projects and users

### Project Structure
- **Generated projects**: Stored in `user_projects/{project_id}/`
- **Templates**: Dynamic template generation with proper variable substitution
- **Isolation**: Each project runs in its own Docker container

## Recent Fixes & Known Issues

### Fixed Issues
1. **NameError: app_name not defined** (Fixed 2025-07-17)
   - **Location**: `smart_project_generator.py:775`
   - **Problem**: Template was using `f'{app_name}'` without proper variable substitution
   - **Solution**: Changed to use f-string formatting with proper escaping: `f"app_name = '{app_name}'"`
   - **Files affected**: 
     - Generator template in `smart_project_generator.py`
     - Existing project files in `user_projects/*/main/views.py` and `urls.py`

2. **Template Variable Substitution**
   - **Problem**: F-string placeholders in templates weren't being properly substituted
   - **Solution**: Use proper f-string formatting with double braces `{{}}` for literal braces in generated code

### Common Patterns
- App names are dynamically inserted into templates during generation
- Views use hardcoded app names like `'main'` instead of variables
- URL namespaces match the app name

## Development Commands
```bash
# Start development server
python manage.py runserver

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run tests (if available)
python manage.py test
```

## API Endpoints
- `POST /api/projects/` - Create new project
- `GET /api/projects/{id}/` - Get project details
- `POST /api/projects/{id}/start_container/` - Start project container
- `POST /api/projects/{id}/stop_container/` - Stop project container

## Generated Project Structure
```
user_projects/{project_id}/
├── main/
│   ├── models.py      # Item model with User relationship
│   ├── views.py       # Home and create views
│   ├── urls.py        # URL patterns with app_name
│   └── forms.py       # ItemForm for CRUD operations
├── templates/main/
│   ├── base.html
│   ├── home.html
│   └── create.html
├── manage.py
├── settings.py
└── Dockerfile
```

## Template Generation Notes
- Always use f-string formatting for dynamic content
- Escape braces properly: `{{}}` for literal braces in generated code
- App names should be substituted during generation, not at runtime
- Views should reference templates with hardcoded app names: `'main/template.html'`
- URL redirects should use hardcoded namespaces: `'main:view_name'`

## Future Improvements
- Add project template customization
- Implement project backup/restore
- Add monitoring for generated projects
- Support for multiple app generation within projects