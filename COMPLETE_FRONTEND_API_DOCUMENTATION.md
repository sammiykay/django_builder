# Django AI Builder - Complete Frontend API Documentation

## Table of Contents
1. [Overview](#overview)
2. [Authentication (JWT)](#authentication-jwt)
3. [Base Configuration](#base-configuration)
4. [User Management](#user-management)
5. [Project Management](#project-management)
6. [AI Generation Endpoints](#ai-generation-endpoints)
7. [File Management](#file-management)
8. [Container Management](#container-management)
9. [Chat & Conversation](#chat--conversation)
10. [WebSocket Real-time Streaming](#websocket-real-time-streaming)
11. [Command Execution](#command-execution)
12. [Error Handling](#error-handling)
13. [Frontend Integration Examples](#frontend-integration-examples)
14. [Rate Limiting](#rate-limiting)
15. [Testing Guide](#testing-guide)

---

## Overview

The Django AI Builder provides a comprehensive REST API with WebSocket support for creating, managing, and interacting with AI-generated Django projects. This documentation covers all endpoints, authentication, and real-time features needed for frontend integration.

**Key Features:**
- JWT Authentication with refresh tokens
- Real-time project generation via WebSocket
- File management and collaborative editing
- AI-powered error fixing and code analysis
- Container management for running projects
- Comprehensive chat and conversation system

---

## Authentication (JWT)

The API uses JWT (JSON Web Tokens) for authentication with access and refresh tokens.

### Base URLs
- **Development:** `http://localhost:8000`
- **API Base:** `http://localhost:8000/api/`
- **WebSocket Base:** `ws://localhost:8000/ws/`

### Authentication Endpoints

#### 1. User Registration
**Endpoint:** `POST /api/auth/register/`

**Request Body:**
```json
{
    "username": "johndoe",
    "email": "john@example.com",
    "password": "SecurePassword123!",
    "first_name": "John",
    "last_name": "Doe"
}
```

**Response (201 Created):**
```json
{
    "user": {
        "id": 1,
        "username": "johndoe",
        "email": "john@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "date_joined": "2025-01-18T10:30:00Z"
    },
    "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

#### 2. User Login
**Endpoint:** `POST /api/auth/login/`

**Request Body:**
```json
{
    "username": "johndoe",
    "password": "SecurePassword123!"
}
```

**Response (200 OK):**
```json
{
    "user": {
        "id": 1,
        "username": "johndoe",
        "email": "john@example.com",
        "first_name": "John",
        "last_name": "Doe"
    },
    "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

#### 3. Token Refresh
**Endpoint:** `POST /api/auth/token/refresh/`

**Request Body:**
```json
{
    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200 OK):**
```json
{
    "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

#### 4. Token Verification
**Endpoint:** `POST /api/auth/token/verify/`

**Request Body:**
```json
{
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200 OK):**
```json
{
    "valid": true
}
```

#### 5. User Logout
**Endpoint:** `POST /api/auth/logout/`

**Headers:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Request Body:**
```json
{
    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200 OK):**
```json
{
    "message": "Successfully logged out"
}
```

---

## Base Configuration

### Request Headers
For all authenticated requests, include:
```javascript
{
    "Authorization": "Bearer <access_token>",
    "Content-Type": "application/json"
}
```

### Response Status Codes
- `200 OK` - Request successful
- `201 Created` - Resource created successfully
- `204 No Content` - Resource deleted successfully
- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Authentication required or token expired
- `403 Forbidden` - Permission denied
- `404 Not Found` - Resource not found
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server error

### Error Response Format
```json
{
    "error": "Error message description",
    "details": "Additional error details (optional)",
    "code": "error_code"
}
```

---

## User Management

### Get Current User Profile
**Endpoint:** `GET /api/auth/user/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
    "id": 1,
    "username": "johndoe",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "date_joined": "2025-01-18T10:30:00Z",
    "last_login": "2025-01-18T12:00:00Z",
    "is_active": true,
    "profile": {
        "bio": "Full-stack developer",
        "avatar": "https://example.com/avatar.jpg",
        "preferred_language": "en",
        "timezone": "UTC"
    }
}
```

### Update User Profile
**Endpoint:** `PUT /api/auth/user/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@example.com",
    "profile": {
        "bio": "Senior Full-stack Developer",
        "preferred_language": "en",
        "timezone": "America/New_York"
    }
}
```

**Response (200 OK):**
```json
{
    "id": 1,
    "username": "johndoe",
    "email": "john.doe@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "profile": {
        "bio": "Senior Full-stack Developer",
        "preferred_language": "en",
        "timezone": "America/New_York"
    }
}
```

### Change Password
**Endpoint:** `POST /api/auth/change-password/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
    "old_password": "OldPassword123!",
    "new_password": "NewSecurePassword123!"
}
```

**Response (200 OK):**
```json
{
    "message": "Password changed successfully"
}
```

---

## Project Management

### List Projects
**Endpoint:** `GET /api/projects/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `page` (optional) - Page number (default: 1)
- `page_size` (optional) - Items per page (default: 20, max: 100)
- `search` (optional) - Search term for project name/description
- `project_type` (optional) - Filter by project type
- `status` (optional) - Filter by generation status

**Example:** `GET /api/projects/?page=1&page_size=10&search=blog&project_type=blog`

**Response (200 OK):**
```json
{
    "count": 25,
    "next": "http://localhost:8000/api/projects/?page=2",
    "previous": null,
    "results": [
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "name": "My Blog Project",
            "description": "A dynamic blog application with user authentication",
            "project_type": "blog",
            "complexity_level": "medium",
            "django_version": "5.0",
            "is_running": false,
            "container_port": null,
            "container_id": null,
            "ai_generation_status": "completed",
            "django_project_created": true,
            "main_app_name": "blog",
            "key_features": ["user authentication", "post creation", "comments"],
            "generated_features": ["User management", "Post CRUD", "Comment system"],
            "original_prompt": "Create a blog application with user authentication and comments",
            "last_prompt": "Add a comment system to the blog",
            "created_at": "2025-01-18T10:30:00Z",
            "updated_at": "2025-01-18T12:45:00Z",
            "owner": 1
        }
    ]
}
```

### Create Project
**Endpoint:** `POST /api/projects/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
    "name": "E-commerce Platform",
    "description": "A complete e-commerce platform with product catalog, shopping cart, and payment processing",
    "project_type": "ecommerce",
    "complexity_level": "complex"
}
```

**Response (201 Created):**
```json
{
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "name": "E-commerce Platform",
    "description": "A complete e-commerce platform with product catalog, shopping cart, and payment processing",
    "project_type": "ecommerce",
    "complexity_level": "complex",
    "django_version": "5.0",
    "is_running": false,
    "container_port": null,
    "container_id": null,
    "ai_generation_status": "pending",
    "django_project_created": false,
    "main_app_name": null,
    "key_features": [],
    "generated_features": [],
    "original_prompt": null,
    "last_prompt": null,
    "created_at": "2025-01-18T14:00:00Z",
    "updated_at": "2025-01-18T14:00:00Z",
    "owner": 1
}
```

### Get Project Details
**Endpoint:** `GET /api/projects/{project_id}/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "My Blog Project",
    "description": "A dynamic blog application with user authentication",
    "project_type": "blog",
    "complexity_level": "medium",
    "django_version": "5.0",
    "is_running": true,
    "container_port": 8001,
    "container_id": "abc123def456",
    "ai_generation_status": "completed",
    "django_project_created": true,
    "main_app_name": "blog",
    "key_features": ["user authentication", "post creation", "comments"],
    "generated_features": ["User management", "Post CRUD", "Comment system"],
    "original_prompt": "Create a blog application with user authentication and comments",
    "last_prompt": "Add a comment system to the blog",
    "prompt_history": [
        {
            "timestamp": "2025-01-18T10:30:00Z",
            "prompt": "Create a blog application with user authentication",
            "type": "initial"
        },
        {
            "timestamp": "2025-01-18T12:45:00Z",
            "prompt": "Add a comment system to the blog",
            "type": "enhancement"
        }
    ],
    "created_at": "2025-01-18T10:30:00Z",
    "updated_at": "2025-01-18T12:45:00Z",
    "owner": 1,
    "files_count": 25,
    "total_lines": 1500
}
```

### Update Project
**Endpoint:** `PUT /api/projects/{project_id}/` or `PATCH /api/projects/{project_id}/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
    "name": "Updated Blog Project",
    "description": "An advanced blog application with user authentication and advanced features"
}
```

**Response (200 OK):**
```json
{
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Updated Blog Project",
    "description": "An advanced blog application with user authentication and advanced features",
    "updated_at": "2025-01-18T15:00:00Z"
}
```

### Delete Project
**Endpoint:** `DELETE /api/projects/{project_id}/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (204 No Content):**
```
(No response body)
```

---

## AI Generation Endpoints

### Smart Generate (Regular)
**Endpoint:** `POST /api/projects/{project_id}/smart_generate/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
    "message": "Create a blog application with user authentication, post creation, comments, and an admin dashboard for managing posts"
}
```

**Response (200 OK):**
```json
{
    "message": "Successfully generated a complete Django project: **blog_app**\n\n**Project Overview:**\n- **Description:** A dynamic blog application with user authentication\n- **Features:** User authentication, Post creation, Comments, Admin dashboard\n- **Files Generated:** 28\n\n**Technology Stack:**\n- **Backend:** Django, PostgreSQL\n- **Frontend:** Bootstrap, JavaScript\n- **Database:** PostgreSQL\n\n**Setup Instructions:**\n• Install dependencies from requirements.txt\n• Configure database settings\n• Run migrations\n• Create superuser account\n\n**API Endpoints:**\n• /api/posts/ [GET, POST] - List and create blog posts\n• /api/comments/ [GET, POST] - Manage comments\n• /api/users/ [GET, POST] - User management\n\n**Next Steps:**\n• Customize the design and styling\n• Add more advanced features\n• Deploy to production\n\nYour project is ready to use at: http://localhost:8000",
    "project_structure": {
        "project_name": "blog_app",
        "description": "A dynamic blog application with user authentication",
        "features": ["User authentication", "Post creation", "Comments", "Admin dashboard"],
        "tech_stack": {
            "backend": ["Django", "PostgreSQL"],
            "frontend": ["Bootstrap", "JavaScript"],
            "database": "PostgreSQL"
        }
    },
    "files": [
        {
            "id": 1,
            "path": "blog/models.py",
            "content": "from django.db import models\nfrom django.contrib.auth.models import User\n\nclass Post(models.Model):\n    title = models.CharField(max_length=200)\n    content = models.TextField()\n    author = models.ForeignKey(User, on_delete=models.CASCADE)\n    created_at = models.DateTimeField(auto_now_add=True)\n    updated_at = models.DateTimeField(auto_now=True)\n    \n    def __str__(self):\n        return self.title",
            "file_type": "py",
            "is_ai_generated": true,
            "ai_merge_status": "new",
            "size": 387,
            "created_at": "2025-01-18T10:30:15Z",
            "updated_at": "2025-01-18T10:30:15Z"
        }
    ],
    "commands": [
        "pip install -r requirements.txt",
        "python manage.py makemigrations",
        "python manage.py migrate",
        "python manage.py createsuperuser",
        "python manage.py runserver"
    ],
    "processing_time": 15.4,
    "django_project_created": true,
    "project_path": "/user_projects/550e8400-e29b-41d4-a716-446655440000",
    "generation_type": "smart_complete",
    "api_endpoints": [
        {
            "url": "/api/posts/",
            "methods": ["GET", "POST"],
            "purpose": "List and create blog posts",
            "authentication": "required"
        },
        {
            "url": "/api/comments/",
            "methods": ["GET", "POST"],
            "purpose": "Manage comments",
            "authentication": "required"
        }
    ],
    "access_url": "http://localhost:8000"
}
```

### Smart Generate (Streaming)
**Endpoint:** `POST /api/projects/{project_id}/smart_generate_stream/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
    "message": "Create an e-commerce platform with product catalog, shopping cart, and payment processing"
}
```

**Response:** Stream of Server-Sent Events (SSE)

**Connection:**
```javascript
const response = await fetch(`/api/projects/${projectId}/smart_generate_stream/`, {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        message: 'Create an e-commerce platform with product catalog and shopping cart'
    })
});

const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    
    const chunk = decoder.decode(value);
    const lines = chunk.split('\n');
    
    for (const line of lines) {
        if (line.startsWith('data: ')) {
            const data = JSON.parse(line.slice(6));
            handleStreamUpdate(data);
        }
    }
}
```

**Stream Event Types:**
```javascript
// Status updates
{
    "type": "status",
    "message": "Starting project generation...",
    "status": "initializing",
    "progress": 5
}

// File creation progress
{
    "type": "file_created",
    "file": "products/models.py",
    "progress": 25.5,
    "files_processed": 8,
    "total_files": 32
}

// Completion
{
    "type": "completed",
    "message": "Project generation completed successfully!",
    "project_structure": {...},
    "files": [...],
    "commands": [...],
    "processing_time": 45.2,
    "django_project_created": true,
    "project_path": "/user_projects/550e8400-e29b-41d4-a716-446655440001",
    "generation_type": "smart_complete",
    "api_endpoints": [...],
    "access_url": "http://localhost:8000"
}

// Error
{
    "type": "error",
    "message": "Generation failed: Claude API rate limit exceeded"
}
```

---

## File Management

### List Project Files (Database)
**Endpoint:** `GET /api/projects/{project_id}/files/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `search` (optional) - Search file names/paths
- `file_type` (optional) - Filter by file type (py, html, css, js, etc.)
- `ai_generated` (optional) - Filter by AI-generated files (true/false)

**Response (200 OK):**
```json
[
    {
        "id": 1,
        "path": "blog/models.py",
        "content": "from django.db import models\nfrom django.contrib.auth.models import User\n\nclass Post(models.Model):\n    title = models.CharField(max_length=200)\n    content = models.TextField()\n    author = models.ForeignKey(User, on_delete=models.CASCADE)\n    created_at = models.DateTimeField(auto_now_add=True)\n    updated_at = models.DateTimeField(auto_now=True)\n    \n    def __str__(self):\n        return self.title",
        "file_type": "py",
        "is_ai_generated": true,
        "ai_merge_status": "new",
        "size": 387,
        "created_at": "2025-01-18T10:30:15Z",
        "updated_at": "2025-01-18T10:30:15Z"
    },
    {
        "id": 2,
        "path": "blog/views.py",
        "content": "from django.shortcuts import render\nfrom django.views.generic import ListView, DetailView\nfrom .models import Post\n\nclass PostListView(ListView):\n    model = Post\n    template_name = 'blog/post_list.html'\n    context_object_name = 'posts'\n    paginate_by = 10\n    ordering = ['-created_at']",
        "file_type": "py",
        "is_ai_generated": true,
        "ai_merge_status": "new",
        "size": 245,
        "created_at": "2025-01-18T10:30:18Z",
        "updated_at": "2025-01-18T10:30:18Z"
    }
]
```

### List Filesystem Files
**Endpoint:** `GET /api/projects/{project_id}/filesystem_files/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
[
    {
        "path": "blog/models.py",
        "size": 387,
        "modified": "2025-01-18T10:30:15Z",
        "type": "file",
        "is_directory": false,
        "extension": "py"
    },
    {
        "path": "blog/views.py",
        "size": 245,
        "modified": "2025-01-18T10:30:18Z",
        "type": "file",
        "is_directory": false,
        "extension": "py"
    },
    {
        "path": "templates/",
        "size": 0,
        "modified": "2025-01-18T10:30:20Z",
        "type": "directory",
        "is_directory": true,
        "extension": ""
    }
]
```

### Get File Content
**Endpoint:** `GET /api/projects/{project_id}/files/content/?path=blog/models.py`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `path` (required) - File path relative to project root

**Response (200 OK):**
```json
{
    "path": "blog/models.py",
    "content": "from django.db import models\nfrom django.contrib.auth.models import User\n\nclass Post(models.Model):\n    title = models.CharField(max_length=200)\n    content = models.TextField()\n    author = models.ForeignKey(User, on_delete=models.CASCADE)\n    created_at = models.DateTimeField(auto_now_add=True)\n    updated_at = models.DateTimeField(auto_now=True)\n    \n    def __str__(self):\n        return self.title\n    \n    class Meta:\n        ordering = ['-created_at']\n        verbose_name = 'Blog Post'\n        verbose_name_plural = 'Blog Posts'"
}
```

### Save File Content
**Endpoint:** `POST /api/projects/{project_id}/save_file/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
    "path": "blog/models.py",
    "content": "from django.db import models\nfrom django.contrib.auth.models import User\n\nclass Post(models.Model):\n    title = models.CharField(max_length=200)\n    content = models.TextField()\n    author = models.ForeignKey(User, on_delete=models.CASCADE)\n    created_at = models.DateTimeField(auto_now_add=True)\n    updated_at = models.DateTimeField(auto_now=True)\n    \n    def __str__(self):\n        return self.title\n    \n    class Meta:\n        ordering = ['-created_at']\n        verbose_name = 'Blog Post'\n        verbose_name_plural = 'Blog Posts'"
}
```

**Response (200 OK):**
```json
{
    "message": "File blog/models.py saved successfully"
}
```

### Create Project File
**Endpoint:** `POST /api/projects/{project_id}/files/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
    "path": "blog/utils.py",
    "content": "from django.utils.text import slugify\nfrom django.utils import timezone\n\ndef generate_unique_slug(title, model_class):\n    \"\"\"Generate a unique slug for a model instance\"\"\"\n    base_slug = slugify(title)\n    unique_slug = base_slug\n    counter = 1\n    \n    while model_class.objects.filter(slug=unique_slug).exists():\n        unique_slug = f\"{base_slug}-{counter}\"\n        counter += 1\n    \n    return unique_slug",
    "file_type": "py"
}
```

**Response (201 Created):**
```json
{
    "id": 15,
    "path": "blog/utils.py",
    "content": "from django.utils.text import slugify\nfrom django.utils import timezone\n\ndef generate_unique_slug(title, model_class):\n    \"\"\"Generate a unique slug for a model instance\"\"\"\n    base_slug = slugify(title)\n    unique_slug = base_slug\n    counter = 1\n    \n    while model_class.objects.filter(slug=unique_slug).exists():\n        unique_slug = f\"{base_slug}-{counter}\"\n        counter += 1\n    \n    return unique_slug",
    "file_type": "py",
    "is_ai_generated": false,
    "ai_merge_status": "none",
    "size": 387,
    "created_at": "2025-01-18T15:30:00Z",
    "updated_at": "2025-01-18T15:30:00Z"
}
```

### Update Project File
**Endpoint:** `PUT /api/projects/{project_id}/files/{file_id}/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
    "path": "blog/utils.py",
    "content": "from django.utils.text import slugify\nfrom django.utils import timezone\nimport re\n\ndef generate_unique_slug(title, model_class):\n    \"\"\"Generate a unique slug for a model instance\"\"\"\n    base_slug = slugify(title)\n    unique_slug = base_slug\n    counter = 1\n    \n    while model_class.objects.filter(slug=unique_slug).exists():\n        unique_slug = f\"{base_slug}-{counter}\"\n        counter += 1\n    \n    return unique_slug\n\ndef clean_html(text):\n    \"\"\"Remove HTML tags from text\"\"\"\n    clean = re.compile('<.*?>')\n    return re.sub(clean, '', text)"
}
```

**Response (200 OK):**
```json
{
    "id": 15,
    "path": "blog/utils.py",
    "content": "from django.utils.text import slugify\nfrom django.utils import timezone\nimport re\n\ndef generate_unique_slug(title, model_class):\n    \"\"\"Generate a unique slug for a model instance\"\"\"\n    base_slug = slugify(title)\n    unique_slug = base_slug\n    counter = 1\n    \n    while model_class.objects.filter(slug=unique_slug).exists():\n        unique_slug = f\"{base_slug}-{counter}\"\n        counter += 1\n    \n    return unique_slug\n\ndef clean_html(text):\n    \"\"\"Remove HTML tags from text\"\"\"\n    clean = re.compile('<.*?>')\n    return re.sub(clean, '', text)",
    "file_type": "py",
    "is_ai_generated": false,
    "ai_merge_status": "none",
    "size": 489,
    "updated_at": "2025-01-18T15:45:00Z"
}
```

### Delete Project File
**Endpoint:** `DELETE /api/projects/{project_id}/files/{file_id}/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (204 No Content):**
```
(No response body)
```

---

## Container Management

### Start Container
**Endpoint:** `POST /api/projects/{project_id}/start_container/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:** (Optional)
```json
{
    "port": 8001
}
```

**Response (200 OK):**
```json
{
    "message": "Container started successfully",
    "port": 8001,
    "container_id": "abc123def456789",
    "access_url": "http://localhost:8001",
    "status": "running"
}
```

### Stop Container
**Endpoint:** `POST /api/projects/{project_id}/stop_container/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
    "message": "Container stopped successfully",
    "status": "stopped"
}
```

### Get Container Status
**Endpoint:** `GET /api/projects/{project_id}/container_status/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
    "is_running": true,
    "container_id": "abc123def456789",
    "port": 8001,
    "access_url": "http://localhost:8001",
    "status": "running",
    "uptime": "2:30:15",
    "cpu_usage": "12%",
    "memory_usage": "128MB"
}
```

---

## Chat & Conversation

### Simple Chat
**Endpoint:** `POST /api/projects/{project_id}/chat/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
    "message": "Add a user profile model to the blog app with avatar and bio fields"
}
```

**Response (200 OK):**
```json
{
    "message": "I've added a UserProfile model to your blog app with avatar and bio fields. Here's what I implemented:\n\n1. Created a UserProfile model with OneToOneField to User\n2. Added avatar ImageField and bio TextField\n3. Updated the admin interface to include the profile\n4. Created a signal to auto-create profiles for new users\n\nFiles modified:\n- blog/models.py: Added UserProfile model\n- blog/admin.py: Added UserProfile admin\n- blog/signals.py: Added profile creation signal\n- requirements.txt: Added Pillow for image handling",
    "files": [
        {
            "path": "blog/models.py",
            "content": "from django.db import models\nfrom django.contrib.auth.models import User\nfrom django.db.models.signals import post_save\nfrom django.dispatch import receiver\n\nclass Post(models.Model):\n    title = models.CharField(max_length=200)\n    content = models.TextField()\n    author = models.ForeignKey(User, on_delete=models.CASCADE)\n    created_at = models.DateTimeField(auto_now_add=True)\n    updated_at = models.DateTimeField(auto_now=True)\n    \n    def __str__(self):\n        return self.title\n\nclass UserProfile(models.Model):\n    user = models.OneToOneField(User, on_delete=models.CASCADE)\n    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)\n    bio = models.TextField(max_length=500, blank=True)\n    \n    def __str__(self):\n        return f\"{self.user.username}'s Profile\"\n\n@receiver(post_save, sender=User)\ndef create_user_profile(sender, instance, created, **kwargs):\n    if created:\n        UserProfile.objects.create(user=instance)\n\n@receiver(post_save, sender=User)\ndef save_user_profile(sender, instance, **kwargs):\n    instance.userprofile.save()"
        }
    ],
    "commands": [
        "pip install Pillow",
        "python manage.py makemigrations",
        "python manage.py migrate"
    ],
    "processing_time": 3.2,
    "files_modified": ["blog/models.py", "blog/admin.py", "requirements.txt"],
    "suggestions": [
        "Add profile picture resizing",
        "Implement profile editing forms",
        "Add profile visibility settings"
    ]
}
```

### Conversational Chat
**Endpoint:** `POST /api/projects/{project_id}/conversation_chat/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
    "message": "The user registration form is not validating email addresses properly",
    "is_error": true,
    "error_type": "validation_error"
}
```

**Response (200 OK):**
```json
{
    "message": "I've identified and fixed the email validation issue in your user registration form. The problem was that the form wasn't using Django's built-in email validation. Here's what I fixed:\n\n**Issue:** The EmailField wasn't properly validating email format\n**Solution:** Added proper email validation and custom clean method\n\n**Changes Made:**\n1. Updated the registration form to use proper email validation\n2. Added custom clean_email method to check for duplicate emails\n3. Added better error messages for validation failures\n4. Updated the view to handle validation errors gracefully\n\n**Files Modified:**\n- accounts/forms.py: Enhanced email validation\n- accounts/views.py: Improved error handling\n- templates/accounts/register.html: Better error display\n\nThe email validation now works correctly and provides clear feedback to users.",
    "files_modified": [
        "accounts/forms.py",
        "accounts/views.py", 
        "templates/accounts/register.html"
    ],
    "code_changes": {
        "accounts/forms.py": "Added EmailField with proper validation and clean_email method",
        "accounts/views.py": "Enhanced error handling for form validation",
        "templates/accounts/register.html": "Improved error message display"
    },
    "suggestions": [
        "Add email confirmation before activation",
        "Implement password strength validation",
        "Add CAPTCHA for spam protection"
    ],
    "processing_time": 4.1,
    "thread_id": "thread_uuid_12345",
    "error_fixed": true,
    "confidence_level": "high"
}
```

### Report Error
**Endpoint:** `POST /api/projects/{project_id}/report_error/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
    "error_message": "IntegrityError: duplicate key value violates unique constraint \"blog_post_slug_key\"",
    "error_type": "database_error",
    "error_source": "blog post creation form",
    "traceback": "Traceback (most recent call last):\n  File \"/app/blog/views.py\", line 25, in post\n    post.save()\n  File \"/usr/local/lib/python3.11/site-packages/django/db/models/base.py\", line 814, in save\n    self.save_base(using=using, force_insert=force_insert,\n  File \"/usr/local/lib/python3.11/site-packages/django/db/models/base.py\", line 877, in save_base\n    updated = self._save_table(\ndjango.db.utils.IntegrityError: duplicate key value violates unique constraint \"blog_post_slug_key\"",
    "command": "python manage.py runserver",
    "stdout": "System check identified no issues (0 silenced).\nJanuary 18, 2025 - 15:30:00\nDjango version 5.0, using settings 'myproject.settings'\nStarting development server at http://127.0.0.1:8000/\nQuit the server with CONTROL-C.",
    "stderr": "IntegrityError: duplicate key value violates unique constraint \"blog_post_slug_key\""
}
```

**Response (200 OK):**
```json
{
    "message": "I've analyzed the IntegrityError and implemented a fix for the duplicate slug constraint issue. Here's what I found and fixed:\n\n**Error Analysis:**\nThe error occurs when trying to create a blog post with a slug that already exists in the database. The unique constraint on the slug field prevents duplicate entries.\n\n**Root Cause:**\nThe Post model has a unique constraint on the slug field, but the form doesn't generate unique slugs when multiple posts have similar titles.\n\n**Fix Applied:**\n1. Modified the Post model to automatically generate unique slugs\n2. Added a pre_save signal to handle slug generation\n3. Created a utility function to ensure slug uniqueness\n4. Updated the form to handle slug conflicts gracefully\n\n**Files Modified:**\n- blog/models.py: Added slug auto-generation\n- blog/utils.py: Added unique slug generator\n- blog/forms.py: Enhanced form validation\n- blog/signals.py: Added pre_save signal\n\nThe issue is now resolved and posts will automatically get unique slugs.",
    "files_modified": [
        "blog/models.py",
        "blog/utils.py",
        "blog/forms.py",
        "blog/signals.py"
    ],
    "code_changes": {
        "blog/models.py": "Added auto-slug generation with unique constraint handling",
        "blog/utils.py": "Created generate_unique_slug utility function",
        "blog/forms.py": "Enhanced form validation for slug conflicts",
        "blog/signals.py": "Added pre_save signal for automatic slug generation"
    },
    "suggestions": [
        "Test the slug generation with various title formats",
        "Add slug editing capability in admin interface",
        "Consider implementing slug history for SEO"
    ],
    "processing_time": 6.8,
    "thread_id": "thread_uuid_12345",
    "error_fixed": true,
    "confidence_level": "high",
    "fix_applied": true,
    "commands_to_run": [
        "python manage.py makemigrations",
        "python manage.py migrate"
    ]
}
```

### Get Conversation History
**Endpoint:** `GET /api/projects/{project_id}/conversation_history/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `limit` (optional) - Maximum number of messages (default: 50)
- `offset` (optional) - Starting point for pagination

**Response (200 OK):**
```json
{
    "thread_id": "thread_uuid_12345",
    "messages": [
        {
            "id": 1,
            "role": "user",
            "content": "Create a blog application with user authentication",
            "timestamp": "2025-01-18T10:30:00Z",
            "message_type": "normal",
            "is_error_report": false
        },
        {
            "id": 2,
            "role": "assistant",
            "content": "I've created a complete blog application with user authentication. Here's what I implemented...",
            "timestamp": "2025-01-18T10:31:00Z",
            "message_type": "normal",
            "processing_time": 15.4,
            "files_modified": ["blog/models.py", "blog/views.py", "blog/urls.py"],
            "code_changes": {
                "blog/models.py": "Created Post model with User relationship",
                "blog/views.py": "Added authentication-required views",
                "blog/urls.py": "Configured URL patterns"
            }
        },
        {
            "id": 3,
            "role": "user",
            "content": "Add a comment system to the blog",
            "timestamp": "2025-01-18T12:45:00Z",
            "message_type": "normal",
            "is_error_report": false
        },
        {
            "id": 4,
            "role": "assistant",
            "content": "I've added a comprehensive comment system to your blog. Here's what I implemented...",
            "timestamp": "2025-01-18T12:46:00Z",
            "message_type": "normal",
            "processing_time": 8.2,
            "files_modified": ["blog/models.py", "blog/views.py", "blog/templates/blog/post_detail.html"],
            "code_changes": {
                "blog/models.py": "Added Comment model with Post relationship",
                "blog/views.py": "Added comment creation and display views",
                "blog/templates/blog/post_detail.html": "Added comment form and display"
            }
        }
    ],
    "total_messages": 4,
    "has_next": false,
    "has_previous": false
}
```

---

## WebSocket Real-time Streaming

### WebSocket Endpoints

#### 1. Project Generation WebSocket
**Endpoint:** `ws://localhost:8000/ws/projects/{project_id}/generate/`

**Authentication:** Include JWT token in connection

**JavaScript Connection:**
```javascript
// Connect to WebSocket
const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
const wsUrl = `${wsProtocol}//${window.location.host}/ws/projects/${projectId}/generate/`;

const ws = new WebSocket(wsUrl);

// Handle connection
ws.onopen = function(event) {
    console.log('Connected to project generation stream');
    
    // Send authentication
    ws.send(JSON.stringify({
        type: 'authenticate',
        token: localStorage.getItem('access_token')
    }));
};

// Handle messages
ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    handleGenerationUpdate(data);
};

// Handle errors
ws.onerror = function(error) {
    console.error('WebSocket error:', error);
};

// Handle close
ws.onclose = function(event) {
    if (event.wasClean) {
        console.log('WebSocket connection closed cleanly');
    } else {
        console.error('WebSocket connection died');
        // Implement reconnection logic
        setTimeout(() => {
            connectWebSocket();
        }, 5000);
    }
};
```

**Message Types (Outgoing):**

**Generate Project:**
```javascript
ws.send(JSON.stringify({
    type: 'generate_project',
    message: 'Create a blog application with user authentication, post creation, and comments'
}));
```

**Chat with AI:**
```javascript
ws.send(JSON.stringify({
    type: 'chat_message',
    message: 'Add a search functionality to find posts by title and content'
}));
```

**Fix Error:**
```javascript
ws.send(JSON.stringify({
    type: 'fix_error',
    error_data: {
        error_type: 'IntegrityError',
        error_message: 'duplicate key value violates unique constraint "blog_post_slug_key"',
        traceback: 'Traceback (most recent call last):\n  File "/app/blog/views.py", line 25, in post\n    post.save()\n  File "/usr/local/lib/python3.11/site-packages/django/db/models/base.py", line 814, in save\n    self.save_base(using=using, force_insert=force_insert,\ndjango.db.utils.IntegrityError: duplicate key value violates unique constraint "blog_post_slug_key"',
        command: 'python manage.py runserver',
        stdout: 'System check identified no issues (0 silenced).',
        stderr: 'IntegrityError: duplicate key value violates unique constraint "blog_post_slug_key"'
    }
}));
```

**Analyze Codebase:**
```javascript
ws.send(JSON.stringify({
    type: 'analyze_codebase'
}));
```

**Execute Command:**
```javascript
ws.send(JSON.stringify({
    type: 'execute_command',
    command: 'python manage.py migrate'
}));
```

**Message Types (Incoming):**

**Connection Established:**
```json
{
    "type": "connection_established",
    "message": "Connected to project My Blog",
    "project_id": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2025-01-18T10:30:00Z"
}
```

**Generation Started:**
```json
{
    "type": "generation_started",
    "message": "Starting project generation...",
    "status": "initializing",
    "timestamp": "2025-01-18T10:30:00Z"
}
```

**Status Updates:**
```json
{
    "type": "status_update",
    "message": "Analyzing your requirements...",
    "status": "analyzing",
    "progress": 15,
    "timestamp": "2025-01-18T10:30:05Z"
}

{
    "type": "status_update",
    "message": "Planning project architecture...",
    "status": "planning",
    "progress": 25,
    "timestamp": "2025-01-18T10:30:10Z"
}

{
    "type": "status_update",
    "message": "Generating project files...",
    "status": "generating",
    "progress": 40,
    "timestamp": "2025-01-18T10:30:15Z"
}
```

**File Processing:**
```json
{
    "type": "file_processed",
    "file": "blog/models.py",
    "progress": 65.5,
    "files_processed": 12,
    "total_files": 25,
    "timestamp": "2025-01-18T10:30:20Z"
}

{
    "type": "file_generated",
    "file_path": "blog/views.py",
    "content_preview": "from django.shortcuts import render\nfrom django.views.generic import ListView, DetailView\nfrom .models import Post\n\nclass PostListView(ListView):\n    model = Post\n    template_name = 'blog/post_list.html'...",
    "progress": 70.0,
    "timestamp": "2025-01-18T10:30:22Z"
}
```

**Generation Completed:**
```json
{
    "type": "generation_completed",
    "message": "Project generation completed successfully!",
    "project_structure": {
        "project_name": "blog_app",
        "description": "A dynamic blog application with user authentication",
        "features": ["User authentication", "Post creation", "Comments"],
        "tech_stack": {
            "backend": ["Django", "PostgreSQL"],
            "frontend": ["Bootstrap", "JavaScript"],
            "database": "PostgreSQL"
        }
    },
    "files_generated": 25,
    "api_endpoints": [
        {
            "url": "/api/posts/",
            "methods": ["GET", "POST"],
            "purpose": "List and create blog posts",
            "authentication": "required"
        }
    ],
    "access_url": "http://localhost:8000",
    "timestamp": "2025-01-18T10:32:00Z"
}
```

**AI Chat Response:**
```json
{
    "type": "ai_response",
    "message": "I've added a comprehensive search functionality to your blog. Here's what I implemented:\n\n1. Created a search form with title and content filtering\n2. Added search view with pagination\n3. Implemented full-text search capabilities\n4. Added search results template\n5. Enhanced the navigation with search box\n\nThe search now supports:\n- Title matching\n- Content search\n- Author filtering\n- Date range filtering\n- Pagination of results",
    "files_modified": [
        "blog/forms.py",
        "blog/views.py",
        "blog/urls.py",
        "templates/blog/search.html",
        "templates/base.html"
    ],
    "suggestions": [
        "Add search highlighting",
        "Implement search analytics",
        "Add search suggestions"
    ],
    "timestamp": "2025-01-18T10:35:00Z"
}
```

**Error Analysis:**
```json
{
    "type": "error_analysis_started",
    "message": "Analyzing error and generating fix...",
    "timestamp": "2025-01-18T10:36:00Z"
}

{
    "type": "error_fix_generated",
    "error_diagnosis": "The error is caused by a duplicate key constraint violation in the database. The Post model has a unique constraint on the slug field, but the application doesn't generate unique slugs when multiple posts have similar titles.",
    "root_cause": "Missing unique slug generation logic in the Post model",
    "fix_steps": [
        "Add automatic slug generation to the Post model",
        "Create a utility function to ensure slug uniqueness",
        "Update the form to handle slug conflicts",
        "Add pre_save signal for automatic slug generation"
    ],
    "code_changes": {
        "blog/models.py": {
            "action": "modify",
            "content": "from django.db import models\nfrom django.contrib.auth.models import User\nfrom django.utils.text import slugify\nfrom django.db.models.signals import pre_save\nfrom django.dispatch import receiver\n\nclass Post(models.Model):\n    title = models.CharField(max_length=200)\n    slug = models.SlugField(unique=True, blank=True)\n    content = models.TextField()\n    author = models.ForeignKey(User, on_delete=models.CASCADE)\n    created_at = models.DateTimeField(auto_now_add=True)\n    updated_at = models.DateTimeField(auto_now=True)\n    \n    def __str__(self):\n        return self.title\n    \n    def save(self, *args, **kwargs):\n        if not self.slug:\n            self.slug = self.generate_unique_slug()\n        super().save(*args, **kwargs)\n    \n    def generate_unique_slug(self):\n        base_slug = slugify(self.title)\n        unique_slug = base_slug\n        counter = 1\n        \n        while Post.objects.filter(slug=unique_slug).exclude(pk=self.pk).exists():\n            unique_slug = f\"{base_slug}-{counter}\"\n            counter += 1\n        \n        return unique_slug"
        }
    },
    "auto_fixable": true,
    "confidence_level": "high",
    "timestamp": "2025-01-18T10:36:10Z"
}

{
    "type": "applying_fixes",
    "message": "Applying automatic fixes...",
    "timestamp": "2025-01-18T10:36:12Z"
}

{
    "type": "fixes_applied",
    "applied_fixes": [
        {
            "file": "blog/models.py",
            "action": "modified",
            "success": true,
            "backup": "blog/models.py.backup"
        }
    ],
    "message": "Applied 1 fixes automatically",
    "timestamp": "2025-01-18T10:36:15Z"
}
```

**Codebase Analysis:**
```json
{
    "type": "codebase_analysis_started",
    "message": "Analyzing codebase structure and patterns...",
    "timestamp": "2025-01-18T10:37:00Z"
}

{
    "type": "codebase_analysis_completed",
    "analysis": {
        "project_metadata": {
            "total_files": 25,
            "total_lines": 1500,
            "languages": {".py": 15, ".html": 8, ".css": 2},
            "frameworks": ["Django", "Bootstrap"]
        },
        "django_structure": {
            "apps": ["blog", "accounts"],
            "models": ["Post", "Comment", "UserProfile"],
            "views": ["PostListView", "PostDetailView", "CommentCreateView"],
            "urls": ["blog/", "accounts/", "api/"],
            "installed_apps": ["django.contrib.admin", "django.contrib.auth", "blog", "accounts"]
        },
        "code_quality": {
            "complexity": {"average": "medium", "highest": "blog/views.py"},
            "security_issues": [],
            "performance_issues": ["N+1 query in PostListView", "Missing database indexes"],
            "best_practices": ["Good model design", "Proper error handling", "Clean URL structure"]
        },
        "context_summary": {
            "project_type": "blog_application",
            "complexity_level": "medium",
            "main_features": ["User authentication", "Post management", "Comment system"],
            "architecture_patterns": ["MVT (Model-View-Template)", "REST API"],
            "development_stage": "development"
        }
    },
    "message": "Codebase analysis completed",
    "timestamp": "2025-01-18T10:37:30Z"
}
```

**Command Execution:**
```json
{
    "type": "command_execution_started",
    "command": "python manage.py migrate",
    "message": "Executing: python manage.py migrate",
    "timestamp": "2025-01-18T10:38:00Z"
}

{
    "type": "command_execution_completed",
    "command": "python manage.py migrate",
    "output": "Operations to perform:\n  Apply all migrations: admin, auth, blog, contenttypes, sessions\nRunning migrations:\n  Applying blog.0001_initial... OK\n  Applying blog.0002_post_slug... OK\n  Applying blog.0003_userprofile... OK",
    "error": "",
    "exit_code": 0,
    "success": true,
    "timestamp": "2025-01-18T10:38:05Z"
}
```

**Error Messages:**
```json
{
    "type": "error",
    "message": "Failed to generate project: Claude API rate limit exceeded. Please try again in a few minutes.",
    "error_code": "rate_limit_exceeded",
    "timestamp": "2025-01-18T10:30:00Z"
}
```

#### 2. File Watcher WebSocket
**Endpoint:** `ws://localhost:8000/ws/projects/{project_id}/files/`

**JavaScript Connection:**
```javascript
const fileWs = new WebSocket(`ws://localhost:8000/ws/projects/${projectId}/files/`);

fileWs.onopen = function(event) {
    console.log('Connected to file watcher');
    
    // Send authentication
    fileWs.send(JSON.stringify({
        type: 'authenticate',
        token: localStorage.getItem('access_token')
    }));
};

fileWs.onmessage = function(event) {
    const data = JSON.parse(event.data);
    handleFileUpdate(data);
};
```

**Message Types (Outgoing):**

**Watch File:**
```javascript
fileWs.send(JSON.stringify({
    type: 'watch_file',
    file_path: 'blog/models.py'
}));
```

**Save File:**
```javascript
fileWs.send(JSON.stringify({
    type: 'save_file',
    file_path: 'blog/models.py',
    content: 'from django.db import models\nfrom django.contrib.auth.models import User\n\nclass Post(models.Model):\n    title = models.CharField(max_length=200)\n    slug = models.SlugField(unique=True, blank=True)\n    content = models.TextField()\n    author = models.ForeignKey(User, on_delete=models.CASCADE)\n    created_at = models.DateTimeField(auto_now_add=True)\n    updated_at = models.DateTimeField(auto_now=True)\n    \n    def __str__(self):\n        return self.title'
}));
```

**Get File Content:**
```javascript
fileWs.send(JSON.stringify({
    type: 'get_file_content',
    file_path: 'blog/views.py'
}));
```

**Message Types (Incoming):**

**File List:**
```json
{
    "type": "file_list",
    "files": [
        {
            "path": "blog/models.py",
            "type": "py",
            "size": 1024,
            "modified": "2025-01-18T10:30:00Z"
        },
        {
            "path": "blog/views.py",
            "type": "py",
            "size": 2048,
            "modified": "2025-01-18T10:31:00Z"
        }
    ],
    "timestamp": "2025-01-18T10:30:00Z"
}
```

**File Content:**
```json
{
    "type": "file_content",
    "file_path": "blog/models.py",
    "content": "from django.db import models\nfrom django.contrib.auth.models import User\n\nclass Post(models.Model):\n    title = models.CharField(max_length=200)\n    slug = models.SlugField(unique=True, blank=True)\n    content = models.TextField()\n    author = models.ForeignKey(User, on_delete=models.CASCADE)\n    created_at = models.DateTimeField(auto_now_add=True)\n    updated_at = models.DateTimeField(auto_now=True)\n    \n    def __str__(self):\n        return self.title",
    "timestamp": "2025-01-18T10:30:00Z"
}
```

**File Changed:**
```json
{
    "type": "file_changed",
    "file_path": "blog/models.py",
    "content": "from django.db import models\nfrom django.contrib.auth.models import User\nfrom django.utils.text import slugify\n\nclass Post(models.Model):\n    title = models.CharField(max_length=200)\n    slug = models.SlugField(unique=True, blank=True)\n    content = models.TextField()\n    author = models.ForeignKey(User, on_delete=models.CASCADE)\n    created_at = models.DateTimeField(auto_now_add=True)\n    updated_at = models.DateTimeField(auto_now=True)\n    \n    def __str__(self):\n        return self.title\n    \n    def save(self, *args, **kwargs):\n        if not self.slug:\n            self.slug = slugify(self.title)\n        super().save(*args, **kwargs)",
    "changed_by": "user",
    "timestamp": "2025-01-18T10:31:00Z"
}
```

**File Watched:**
```json
{
    "type": "file_watched",
    "file_path": "blog/models.py",
    "message": "Now watching blog/models.py for changes",
    "timestamp": "2025-01-18T10:30:00Z"
}
```

---

## Command Execution

### Execute Command
**Endpoint:** `POST /api/projects/{project_id}/execute_command/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
    "command": "python manage.py migrate",
    "timeout": 300
}
```

**Response (200 OK):**
```json
{
    "output": "Operations to perform:\n  Apply all migrations: admin, auth, blog, contenttypes, sessions\nRunning migrations:\n  Applying blog.0001_initial... OK\n  Applying blog.0002_post_slug... OK\n  Applying blog.0003_userprofile... OK",
    "error": "",
    "exit_code": 0,
    "execution_time": 2.3,
    "success": true,
    "command": "python manage.py migrate",
    "timestamp": "2025-01-18T10:30:00Z"
}
```

### Get Command History
**Endpoint:** `GET /api/projects/{project_id}/executions/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `limit` (optional) - Maximum number of executions (default: 20)
- `offset` (optional) - Starting point for pagination

**Response (200 OK):**
```json
{
    "count": 15,
    "next": "http://localhost:8000/api/projects/550e8400-e29b-41d4-a716-446655440000/executions/?offset=20",
    "previous": null,
    "results": [
        {
            "id": 1,
            "command": "python manage.py migrate",
            "output": "Operations to perform:\n  Apply all migrations: admin, auth, blog, contenttypes, sessions\nRunning migrations:\n  Applying blog.0001_initial... OK",
            "error_output": "",
            "exit_code": 0,
            "execution_time": 2.3,
            "timestamp": "2025-01-18T10:30:00Z"
        },
        {
            "id": 2,
            "command": "python manage.py createsuperuser",
            "output": "Superuser created successfully.",
            "error_output": "",
            "exit_code": 0,
            "execution_time": 1.8,
            "timestamp": "2025-01-18T10:32:00Z"
        }
    ]
}
```

---

## Error Handling

### Common Error Responses

#### 401 Unauthorized
```json
{
    "error": "Authentication credentials were not provided",
    "code": "not_authenticated"
}
```

#### 403 Forbidden
```json
{
    "error": "You do not have permission to perform this action",
    "code": "permission_denied"
}
```

#### 404 Not Found
```json
{
    "error": "Project not found",
    "code": "not_found"
}
```

#### 429 Rate Limited
```json
{
    "error": "Rate limit exceeded. Please try again in 60 seconds",
    "code": "rate_limit_exceeded",
    "retry_after": 60
}
```

#### 500 Internal Server Error
```json
{
    "error": "An internal server error occurred",
    "code": "internal_server_error",
    "details": "Please try again later or contact support"
}
```

### Validation Errors
```json
{
    "error": "Validation failed",
    "code": "validation_error",
    "details": {
        "name": ["This field is required"],
        "email": ["Enter a valid email address"]
    }
}
```

---

## Frontend Integration Examples

### React.js Integration

#### Authentication Hook
```javascript
// hooks/useAuth.js
import { useState, useEffect, useContext, createContext } from 'react';

const AuthContext = createContext();

export const useAuth = () => {
    return useContext(AuthContext);
};

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const token = localStorage.getItem('access_token');
        if (token) {
            // Verify token and get user info
            verifyToken(token).then(user => {
                setUser(user);
                setLoading(false);
            }).catch(() => {
                localStorage.removeItem('access_token');
                localStorage.removeItem('refresh_token');
                setLoading(false);
            });
        } else {
            setLoading(false);
        }
    }, []);

    const login = async (username, password) => {
        try {
            const response = await fetch('/api/auth/login/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ username, password }),
            });

            if (response.ok) {
                const data = await response.json();
                localStorage.setItem('access_token', data.access);
                localStorage.setItem('refresh_token', data.refresh);
                setUser(data.user);
                return { success: true };
            } else {
                const errorData = await response.json();
                return { success: false, error: errorData.error };
            }
        } catch (error) {
            return { success: false, error: 'Network error' };
        }
    };

    const logout = () => {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        setUser(null);
    };

    const refreshToken = async () => {
        const refresh = localStorage.getItem('refresh_token');
        if (!refresh) return false;

        try {
            const response = await fetch('/api/auth/token/refresh/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ refresh }),
            });

            if (response.ok) {
                const data = await response.json();
                localStorage.setItem('access_token', data.access);
                return true;
            } else {
                logout();
                return false;
            }
        } catch (error) {
            logout();
            return false;
        }
    };

    const verifyToken = async (token) => {
        const response = await fetch('/api/auth/user/', {
            headers: {
                'Authorization': `Bearer ${token}`,
            },
        });

        if (response.ok) {
            return await response.json();
        } else {
            throw new Error('Token invalid');
        }
    };

    const value = {
        user,
        login,
        logout,
        refreshToken,
        loading
    };

    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    );
};
```

#### API Client
```javascript
// api/client.js
class ApiClient {
    constructor(baseURL = 'http://localhost:8000/api') {
        this.baseURL = baseURL;
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const token = localStorage.getItem('access_token');

        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...(token && { 'Authorization': `Bearer ${token}` }),
            },
            ...options,
        };

        try {
            const response = await fetch(url, config);

            if (response.status === 401) {
                // Try to refresh token
                const refreshed = await this.refreshToken();
                if (refreshed) {
                    // Retry the request
                    config.headers['Authorization'] = `Bearer ${localStorage.getItem('access_token')}`;
                    return fetch(url, config);
                } else {
                    // Redirect to login
                    window.location.href = '/login';
                    return;
                }
            }

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Request failed');
            }

            return response.json();
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }

    async refreshToken() {
        const refresh = localStorage.getItem('refresh_token');
        if (!refresh) return false;

        try {
            const response = await fetch(`${this.baseURL}/auth/token/refresh/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ refresh }),
            });

            if (response.ok) {
                const data = await response.json();
                localStorage.setItem('access_token', data.access);
                return true;
            } else {
                localStorage.removeItem('access_token');
                localStorage.removeItem('refresh_token');
                return false;
            }
        } catch (error) {
            return false;
        }
    }

    // Project endpoints
    async getProjects(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        return this.request(`/projects/?${queryString}`);
    }

    async createProject(data) {
        return this.request('/projects/', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    async getProject(projectId) {
        return this.request(`/projects/${projectId}/`);
    }

    async updateProject(projectId, data) {
        return this.request(`/projects/${projectId}/`, {
            method: 'PATCH',
            body: JSON.stringify(data),
        });
    }

    async deleteProject(projectId) {
        return this.request(`/projects/${projectId}/`, {
            method: 'DELETE',
        });
    }

    // AI Generation endpoints
    async generateProject(projectId, message) {
        return this.request(`/projects/${projectId}/smart_generate/`, {
            method: 'POST',
            body: JSON.stringify({ message }),
        });
    }

    async chatWithAI(projectId, message) {
        return this.request(`/projects/${projectId}/chat/`, {
            method: 'POST',
            body: JSON.stringify({ message }),
        });
    }

    // File endpoints
    async getProjectFiles(projectId) {
        return this.request(`/projects/${projectId}/files/`);
    }

    async getFileContent(projectId, filePath) {
        return this.request(`/projects/${projectId}/files/content/?path=${encodeURIComponent(filePath)}`);
    }

    async saveFile(projectId, filePath, content) {
        return this.request(`/projects/${projectId}/save_file/`, {
            method: 'POST',
            body: JSON.stringify({ path: filePath, content }),
        });
    }

    // Container endpoints
    async startContainer(projectId) {
        return this.request(`/projects/${projectId}/start_container/`, {
            method: 'POST',
        });
    }

    async stopContainer(projectId) {
        return this.request(`/projects/${projectId}/stop_container/`, {
            method: 'POST',
        });
    }
}

export const apiClient = new ApiClient();
```

#### WebSocket Hook
```javascript
// hooks/useWebSocket.js
import { useState, useEffect, useRef } from 'react';

export const useWebSocket = (url, options = {}) => {
    const [socket, setSocket] = useState(null);
    const [lastMessage, setLastMessage] = useState(null);
    const [readyState, setReadyState] = useState(0);
    const [connectionStatus, setConnectionStatus] = useState('Connecting');
    const reconnectTimeoutRef = useRef(null);
    const shouldReconnect = useRef(true);

    const connect = () => {
        try {
            const ws = new WebSocket(url);
            
            ws.onopen = () => {
                setReadyState(1);
                setConnectionStatus('Connected');
                
                // Send authentication if token exists
                const token = localStorage.getItem('access_token');
                if (token) {
                    ws.send(JSON.stringify({
                        type: 'authenticate',
                        token: token
                    }));
                }

                if (options.onOpen) {
                    options.onOpen();
                }
            };

            ws.onmessage = (event) => {
                const message = JSON.parse(event.data);
                setLastMessage(message);
                
                if (options.onMessage) {
                    options.onMessage(message);
                }
            };

            ws.onclose = (event) => {
                setReadyState(3);
                setConnectionStatus('Disconnected');
                
                if (shouldReconnect.current) {
                    setConnectionStatus('Reconnecting...');
                    reconnectTimeoutRef.current = setTimeout(() => {
                        connect();
                    }, 5000);
                }

                if (options.onClose) {
                    options.onClose(event);
                }
            };

            ws.onerror = (error) => {
                setConnectionStatus('Error');
                
                if (options.onError) {
                    options.onError(error);
                }
            };

            setSocket(ws);
        } catch (error) {
            setConnectionStatus('Error');
            console.error('WebSocket connection failed:', error);
        }
    };

    useEffect(() => {
        connect();

        return () => {
            shouldReconnect.current = false;
            if (reconnectTimeoutRef.current) {
                clearTimeout(reconnectTimeoutRef.current);
            }
            if (socket) {
                socket.close();
            }
        };
    }, [url]);

    const sendMessage = (message) => {
        if (socket && readyState === 1) {
            socket.send(JSON.stringify(message));
        }
    };

    const disconnect = () => {
        shouldReconnect.current = false;
        if (socket) {
            socket.close();
        }
    };

    return {
        socket,
        lastMessage,
        readyState,
        connectionStatus,
        sendMessage,
        disconnect,
    };
};
```

#### Project Generation Component
```javascript
// components/ProjectGenerator.js
import React, { useState } from 'react';
import { useWebSocket } from '../hooks/useWebSocket';

const ProjectGenerator = ({ projectId }) => {
    const [prompt, setPrompt] = useState('');
    const [status, setStatus] = useState('');
    const [progress, setProgress] = useState(0);
    const [files, setFiles] = useState([]);
    const [isGenerating, setIsGenerating] = useState(false);
    const [result, setResult] = useState(null);

    const { sendMessage, lastMessage, connectionStatus } = useWebSocket(
        `ws://localhost:8000/ws/projects/${projectId}/generate/`,
        {
            onMessage: (message) => {
                handleWebSocketMessage(message);
            },
            onOpen: () => {
                console.log('Connected to project generation WebSocket');
            },
            onClose: () => {
                console.log('Disconnected from project generation WebSocket');
            },
            onError: (error) => {
                console.error('WebSocket error:', error);
            }
        }
    );

    const handleWebSocketMessage = (message) => {
        switch (message.type) {
            case 'connection_established':
                console.log('Connection established:', message.message);
                break;
            
            case 'generation_started':
                setIsGenerating(true);
                setStatus(message.message);
                setProgress(0);
                break;
            
            case 'status_update':
                setStatus(message.message);
                setProgress(message.progress || 0);
                break;
            
            case 'file_processed':
                setFiles(prev => [...prev, message.file]);
                setProgress(message.progress || 0);
                break;
            
            case 'file_generated':
                setFiles(prev => [...prev, {
                    path: message.file_path,
                    preview: message.content_preview
                }]);
                setProgress(message.progress || 0);
                break;
            
            case 'generation_completed':
                setIsGenerating(false);
                setStatus('Generation completed!');
                setProgress(100);
                setResult(message.result);
                break;
            
            case 'error':
                setIsGenerating(false);
                setStatus(`Error: ${message.message}`);
                break;
            
            default:
                console.log('Unknown message type:', message.type);
        }
    };

    const handleGenerate = () => {
        if (!prompt.trim()) return;

        setFiles([]);
        setResult(null);
        
        sendMessage({
            type: 'generate_project',
            message: prompt
        });
    };

    return (
        <div className="project-generator">
            <div className="connection-status">
                Status: {connectionStatus}
            </div>
            
            <div className="prompt-input">
                <textarea
                    value={prompt}
                    onChange={(e) => setPrompt(e.target.value)}
                    placeholder="Describe your Django project..."
                    rows={4}
                    disabled={isGenerating}
                />
                <button 
                    onClick={handleGenerate}
                    disabled={isGenerating || !prompt.trim()}
                >
                    {isGenerating ? 'Generating...' : 'Generate Project'}
                </button>
            </div>

            {isGenerating && (
                <div className="generation-progress">
                    <div className="status">{status}</div>
                    <div className="progress-bar">
                        <div 
                            className="progress-fill" 
                            style={{ width: `${progress}%` }}
                        />
                    </div>
                    <div className="progress-text">{progress}%</div>
                </div>
            )}

            {files.length > 0 && (
                <div className="files-generated">
                    <h3>Files Generated:</h3>
                    <ul>
                        {files.map((file, index) => (
                            <li key={index}>
                                {typeof file === 'string' ? file : file.path}
                            </li>
                        ))}
                    </ul>
                </div>
            )}

            {result && (
                <div className="generation-result">
                    <h3>Project Generated Successfully!</h3>
                    <div className="project-info">
                        <h4>{result.project_name}</h4>
                        <p>{result.description}</p>
                        <div className="features">
                            <strong>Features:</strong>
                            <ul>
                                {result.features.map((feature, index) => (
                                    <li key={index}>{feature}</li>
                                ))}
                            </ul>
                        </div>
                        <div className="tech-stack">
                            <strong>Tech Stack:</strong>
                            <ul>
                                {result.tech_stack.backend.map((tech, index) => (
                                    <li key={index}>{tech}</li>
                                ))}
                            </ul>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default ProjectGenerator;
```

---

## Rate Limiting

### Rate Limits by Endpoint Category

#### Authentication Endpoints
- **Login/Register:** 10 requests per minute per IP
- **Token Refresh:** 30 requests per minute per user
- **Password Reset:** 5 requests per hour per email

#### AI Generation Endpoints
- **Smart Generate:** 5 requests per hour per user
- **Chat:** 30 requests per hour per user
- **Error Fixing:** 10 requests per hour per user

#### File Management
- **File Operations:** 100 requests per minute per user
- **File Content:** 200 requests per minute per user

#### General API
- **Other Endpoints:** 1000 requests per hour per user

### Rate Limit Headers
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642521600
```

---

## Testing Guide

### Authentication Testing
```javascript
// Test authentication flow
describe('Authentication', () => {
    test('should login successfully', async () => {
        const response = await fetch('/api/auth/login/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                username: 'testuser',
                password: 'testpass123'
            }),
        });

        expect(response.ok).toBe(true);
        const data = await response.json();
        expect(data.access).toBeDefined();
        expect(data.refresh).toBeDefined();
        expect(data.user.username).toBe('testuser');
    });

    test('should refresh token', async () => {
        const refreshToken = localStorage.getItem('refresh_token');
        const response = await fetch('/api/auth/token/refresh/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                refresh: refreshToken
            }),
        });

        expect(response.ok).toBe(true);
        const data = await response.json();
        expect(data.access).toBeDefined();
    });
});
```

### WebSocket Testing
```javascript
// Test WebSocket connection
describe('WebSocket', () => {
    test('should connect and receive messages', (done) => {
        const ws = new WebSocket('ws://localhost:8000/ws/projects/test-project/generate/');
        
        ws.onopen = () => {
            ws.send(JSON.stringify({
                type: 'authenticate',
                token: 'test-token'
            }));
        };

        ws.onmessage = (event) => {
            const message = JSON.parse(event.data);
            expect(message.type).toBe('connection_established');
            ws.close();
            done();
        };

        ws.onerror = (error) => {
            done(error);
        };
    });
});
```

### API Testing
```javascript
// Test API endpoints
describe('API Endpoints', () => {
    test('should create project', async () => {
        const response = await fetch('/api/projects/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${accessToken}`,
            },
            body: JSON.stringify({
                name: 'Test Project',
                description: 'A test project',
                project_type: 'blog',
                complexity_level: 'simple'
            }),
        });

        expect(response.ok).toBe(true);
        const data = await response.json();
        expect(data.name).toBe('Test Project');
        expect(data.id).toBeDefined();
    });

    test('should generate project', async () => {
        const response = await fetch(`/api/projects/${projectId}/smart_generate/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${accessToken}`,
            },
            body: JSON.stringify({
                message: 'Create a simple blog application'
            }),
        });

        expect(response.ok).toBe(true);
        const data = await response.json();
        expect(data.django_project_created).toBe(true);
        expect(data.files).toBeDefined();
    });
});
```

---

This comprehensive documentation provides everything needed for frontend integration with the Django AI Builder API. The documentation covers authentication, all REST endpoints, WebSocket real-time streaming, error handling, and includes practical examples for React.js integration.
