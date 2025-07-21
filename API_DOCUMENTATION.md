# Django AI Builder API Documentation

## Overview
The Django AI Builder provides a comprehensive REST API for creating, managing, and interacting with AI-generated Django projects. This API enables users to dynamically generate complete Django applications through natural language prompts, manage project files, execute commands, and maintain conversational workflows.

## Base URL
```
http://localhost:8000/api/
```

## Authentication
All endpoints require authentication. Include the authentication token in your requests:

```bash
Authorization: Token <your_token>
```

## Content Types
- Request: `application/json`
- Response: `application/json`
- Streaming: `text/event-stream`

---

## Projects API

### 1. List Projects
**Endpoint:** `GET /api/projects/`

**Description:** Retrieve all projects belonging to the authenticated user.

**Response:**
```json
{
  "count": 10,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "uuid",
      "name": "My Blog Project",
      "description": "A dynamic blog application",
      "project_type": "blog",
      "complexity_level": "medium",
      "django_version": "5.0",
      "is_running": false,
      "container_port": null,
      "ai_generation_status": "completed",
      "created_at": "2025-01-18T10:30:00Z",
      "updated_at": "2025-01-18T12:45:00Z"
    }
  ]
}
```

### 2. Create Project
**Endpoint:** `POST /api/projects/`

**Description:** Create a new project.

**Request Body:**
```json
{
  "name": "My New Project",
  "description": "Project description",
  "project_type": "blog",
  "complexity_level": "medium"
}
```

**Response:** Returns the created project object with status `201 Created`.

### 3. Get Project Details
**Endpoint:** `GET /api/projects/{project_id}/`

**Description:** Retrieve detailed information about a specific project.

**Response:**
```json
{
  "id": "uuid",
  "name": "My Blog Project",
  "description": "A dynamic blog application",
  "project_type": "blog",
  "complexity_level": "medium",
  "django_version": "5.0",
  "is_running": false,
  "container_port": null,
  "ai_generation_status": "completed",
  "django_project_created": true,
  "main_app_name": "blog",
  "key_features": ["user authentication", "file upload", "search functionality"],
  "generated_features": ["User management", "Post creation", "Comments"],
  "original_prompt": "Create a blog application with user authentication",
  "created_at": "2025-01-18T10:30:00Z",
  "updated_at": "2025-01-18T12:45:00Z"
}
```

### 4. Update Project
**Endpoint:** `PUT /api/projects/{project_id}/` or `PATCH /api/projects/{project_id}/`

**Description:** Update project information.

**Request Body:**
```json
{
  "name": "Updated Project Name",
  "description": "Updated description"
}
```

### 5. Delete Project
**Endpoint:** `DELETE /api/projects/{project_id}/`

**Description:** Delete a project and all associated files.

**Response:** `204 No Content`

---

## AI Generation API

### 6. Smart Generate (Regular)
**Endpoint:** `POST /api/projects/{project_id}/smart_generate/`

**Description:** Generate or enhance a Django project using AI based on natural language prompts.

**Request Body:**
```json
{
  "message": "Create a blog application with user authentication, post creation, and comments"
}
```

**Response:**
```json
{
  "message": "Successfully generated a complete Django project...",
  "project_structure": {
    "project_name": "blog_app",
    "description": "A dynamic blog application",
    "features": ["User authentication", "Post creation", "Comments"],
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
      "content": "from django.db import models...",
      "file_type": "py",
      "is_ai_generated": true
    }
  ],
  "commands": ["python manage.py migrate", "python manage.py runserver"],
  "processing_time": 15.4,
  "django_project_created": true,
  "project_path": "/user_projects/uuid",
  "generation_type": "smart_complete",
  "api_endpoints": [
    {
      "url": "/api/posts/",
      "methods": ["GET", "POST"],
      "purpose": "List and create blog posts"
    }
  ],
  "access_url": "http://localhost:8000"
}
```

### 7. Smart Generate (Streaming)
**Endpoint:** `POST /api/projects/{project_id}/smart_generate_stream/`

**Description:** Same as smart_generate but with real-time streaming updates (Server-Sent Events).

**Request Body:**
```json
{
  "message": "Create a e-commerce platform with product catalog and shopping cart"
}
```

**Response:** Stream of Server-Sent Events:
```
data: {"type": "status", "message": "Starting project generation...", "status": "initializing"}

data: {"type": "status", "message": "Analyzing your requirements...", "status": "analyzing"}

data: {"type": "status", "message": "Project structure created! Generating files...", "status": "generating"}

data: {"type": "file_created", "file": "products/models.py", "progress": 25.5}

data: {"type": "file_created", "file": "cart/views.py", "progress": 50.0}

data: {"type": "completed", "message": "Project completed!", "project_structure": {...}, "files": [...]}
```

**Event Types:**
- `status`: General status updates
- `file_created`: File creation progress
- `completed`: Generation completed successfully
- `error`: Error occurred during generation

### 8. Generate with AI (Legacy)
**Endpoint:** `POST /api/projects/{project_id}/generate_with_ai/`

**Description:** Legacy AI generation endpoint with traditional workflow.

**Request Body:**
```json
{
  "message": "Add user authentication to my project",
  "app_name": "accounts"
}
```

---

## Container Management API

### 9. Start Container
**Endpoint:** `POST /api/projects/{project_id}/start_container/`

**Description:** Start the Django development server in a Docker container.

**Response:**
```json
{
  "message": "Container started successfully",
  "port": 8001,
  "container_id": "container_hash"
}
```

### 10. Stop Container
**Endpoint:** `POST /api/projects/{project_id}/stop_container/`

**Description:** Stop the running Django development server.

**Response:**
```json
{
  "message": "Container stopped successfully"
}
```

---

## File Management API

### 11. List Project Files
**Endpoint:** `GET /api/projects/{project_id}/files/`

**Description:** Get all project files from the database.

**Response:**
```json
[
  {
    "id": 1,
    "path": "blog/models.py",
    "content": "from django.db import models...",
    "file_type": "py",
    "is_ai_generated": true,
    "ai_merge_status": "new",
    "size": 1024,
    "created_at": "2025-01-18T10:30:00Z",
    "updated_at": "2025-01-18T12:45:00Z"
  }
]
```

### 12. List Filesystem Files
**Endpoint:** `GET /api/projects/{project_id}/filesystem_files/`

**Description:** Get all project files from the filesystem.

**Response:**
```json
[
  {
    "path": "blog/models.py",
    "size": 1024,
    "modified": "2025-01-18T12:45:00Z",
    "type": "file",
    "is_directory": false,
    "extension": "py"
  }
]
```

### 13. Get File Content
**Endpoint:** `GET /api/projects/{project_id}/files/content/?path=blog/models.py`

**Description:** Get the content of a specific file.

**Query Parameters:**
- `path`: File path relative to project root

**Response:**
```json
{
  "path": "blog/models.py",
  "content": "from django.db import models\n\nclass Post(models.Model):\n    title = models.CharField(max_length=200)\n    content = models.TextField()\n    created_at = models.DateTimeField(auto_now_add=True)"
}
```

### 14. Save File Content
**Endpoint:** `POST /api/projects/{project_id}/save_file/`

**Description:** Save content to a specific file.

**Request Body:**
```json
{
  "path": "blog/models.py",
  "content": "from django.db import models\n\n# Updated content here"
}
```

**Response:**
```json
{
  "message": "File blog/models.py saved successfully"
}
```

---

## Chat and Conversation API

### 15. Simple Chat
**Endpoint:** `POST /api/projects/{project_id}/chat/`

**Description:** Basic chat with AI for code generation.

**Request Body:**
```json
{
  "message": "Add a user profile model to my project"
}
```

**Response:**
```json
{
  "message": "I've added a user profile model to your project...",
  "files": [
    {
      "path": "accounts/models.py",
      "content": "class UserProfile(models.Model)..."
    }
  ],
  "commands": ["python manage.py makemigrations", "python manage.py migrate"],
  "processing_time": 3.2
}
```

### 16. Conversational Chat
**Endpoint:** `POST /api/projects/{project_id}/conversation_chat/`

**Description:** Advanced conversational chat with full project context and error handling.

**Request Body:**
```json
{
  "message": "The user registration is not working properly",
  "is_error": true,
  "error_type": "validation_error"
}
```

**Response:**
```json
{
  "message": "I've identified the issue with user registration...",
  "files_modified": ["accounts/forms.py", "accounts/views.py"],
  "code_changes": {
    "accounts/forms.py": "Added proper validation for email field",
    "accounts/views.py": "Fixed registration view logic"
  },
  "suggestions": ["Add email verification", "Implement password strength validation"],
  "processing_time": 4.1,
  "thread_id": "thread_uuid",
  "error_fixed": true
}
```

### 17. Report Error
**Endpoint:** `POST /api/projects/{project_id}/report_error/`

**Description:** Report an error from the running project for AI to analyze and fix.

**Request Body:**
```json
{
  "error_message": "IntegrityError: duplicate key value violates unique constraint",
  "error_type": "database_error",
  "error_source": "user registration form"
}
```

**Response:** Same as conversation_chat with error flag set.

### 18. Get Conversation History
**Endpoint:** `GET /api/projects/{project_id}/conversation_history/`

**Description:** Get the conversation history for the project's chat thread.

**Response:**
```json
{
  "thread_id": "thread_uuid",
  "messages": [
    {
      "id": 1,
      "role": "user",
      "content": "Create a blog application",
      "timestamp": "2025-01-18T10:30:00Z",
      "message_type": "normal"
    },
    {
      "id": 2,
      "role": "assistant",
      "content": "I've created a blog application...",
      "timestamp": "2025-01-18T10:31:00Z",
      "processing_time": 15.4,
      "files_modified": ["blog/models.py"]
    }
  ],
  "total_messages": 2
}
```

---

## Command Execution API

### 19. Execute Command
**Endpoint:** `POST /api/projects/{project_id}/execute_command/`

**Description:** Execute Django management commands in the project environment.

**Request Body:**
```json
{
  "command": "python manage.py migrate"
}
```

**Response:**
```json
{
  "output": "Operations to perform:\n  Apply all migrations...",
  "error": "",
  "exit_code": 0,
  "execution_time": 2.3
}
```

### 20. Get Command Executions
**Endpoint:** `GET /api/projects/{project_id}/executions/`

**Description:** Get history of executed commands for the project.

**Response:**
```json
[
  {
    "id": 1,
    "command": "python manage.py migrate",
    "output": "Operations to perform...",
    "error_output": "",
    "exit_code": 0,
    "execution_time": 2.3,
    "timestamp": "2025-01-18T10:30:00Z"
  }
]
```

---

## Legacy API Endpoints

### 21. Get Chat Messages (Legacy)
**Endpoint:** `GET /api/projects/{project_id}/messages/`

**Description:** Get chat messages for the project (legacy endpoint).

### 22. Get Project Statistics
**Endpoint:** `GET /api/projects/{project_id}/stats/`

**Description:** Get detailed statistics about the project.

**Response:**
```json
{
  "files_count": 25,
  "total_lines": 1500,
  "total_size": 45000,
  "messages_count": 10,
  "executions_count": 5,
  "last_activity": "2025-01-18T12:45:00Z",
  "is_running": true
}
```

---

## Project File Management API

### 23. Create Project File
**Endpoint:** `POST /api/projects/{project_id}/files/`

**Description:** Create a new file in the project.

**Request Body:**
```json
{
  "path": "blog/admin.py",
  "content": "from django.contrib import admin\nfrom .models import Post\n\nadmin.site.register(Post)",
  "file_type": "py"
}
```

### 24. Update Project File
**Endpoint:** `PUT /api/projects/{project_id}/files/{file_id}/`

**Description:** Update an existing project file.

### 25. Delete Project File
**Endpoint:** `DELETE /api/projects/{project_id}/files/{file_id}/`

**Description:** Delete a project file.

---

## Error Handling

### HTTP Status Codes
- `200 OK`: Request successful
- `201 Created`: Resource created successfully
- `204 No Content`: Resource deleted successfully
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Permission denied
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

### Error Response Format
```json
{
  "error": "Error message description",
  "details": "Additional error details (optional)"
}
```

---

## Rate Limiting
- **AI Generation**: 10 requests per minute
- **File Operations**: 100 requests per minute
- **Other Endpoints**: 60 requests per minute

## Usage Examples

### Creating a Blog with Streaming
```javascript
// Create project
const project = await fetch('/api/projects/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Token your_token'
  },
  body: JSON.stringify({
    name: 'My Blog',
    description: 'A personal blog'
  })
}).then(r => r.json());

// Generate with streaming
const eventSource = new EventSource(`/api/projects/${project.id}/smart_generate_stream/`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Token your_token'
  },
  body: JSON.stringify({
    message: 'Create a blog with user authentication and post management'
  })
});

eventSource.onmessage = function(event) {
  const data = JSON.parse(event.data);
  
  switch(data.type) {
    case 'status':
      console.log('Status:', data.message);
      break;
    case 'file_created':
      console.log('File created:', data.file, 'Progress:', data.progress + '%');
      break;
    case 'completed':
      console.log('Generation completed!');
      console.log('Project structure:', data.project_structure);
      eventSource.close();
      break;
    case 'error':
      console.error('Error:', data.message);
      eventSource.close();
      break;
  }
};
```

### Error Reporting and Fix
```javascript
// Report an error
const errorReport = await fetch(`/api/projects/${projectId}/report_error/`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Token your_token'
  },
  body: JSON.stringify({
    error_message: 'ValidationError: Email field is required',
    error_type: 'validation_error',
    error_source: 'user registration form'
  })
}).then(r => r.json());

console.log('AI Response:', errorReport.message);
console.log('Files Modified:', errorReport.files_modified);
console.log('Error Fixed:', errorReport.error_fixed);
```

---

## WebSocket Support

The Django AI Builder now includes real-time WebSocket support for live project generation and file streaming, similar to Bolt.new.

### WebSocket Endpoints

#### 1. Project Generation WebSocket
**Endpoint:** `ws://localhost:8000/ws/projects/{project_id}/generate/`

**Description:** Real-time project generation with streaming updates

**Connection:**
```javascript
const ws = new WebSocket(`ws://localhost:8000/ws/projects/${projectId}/generate/`);

ws.onopen = function(event) {
    console.log('Connected to project generation stream');
};

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    handleGenerationUpdate(data);
};
```

**Message Types (Outgoing):**
```javascript
// Generate project
ws.send(JSON.stringify({
    type: 'generate_project',
    message: 'Create a blog application with user authentication'
}));

// Chat with AI
ws.send(JSON.stringify({
    type: 'chat_message',
    message: 'Add a comment system to the blog'
}));

// Fix error
ws.send(JSON.stringify({
    type: 'fix_error',
    error_data: {
        error_type: 'IntegrityError',
        error_message: 'duplicate key value violates unique constraint',
        traceback: 'Traceback (most recent call last)...',
        command: 'python manage.py migrate'
    }
}));

// Analyze codebase
ws.send(JSON.stringify({
    type: 'analyze_codebase'
}));

// Execute command
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
    "project_id": "uuid",
    "timestamp": "2025-01-18T10:30:00Z"
}
```

**Generation Status Updates:**
```json
{
    "type": "generation_started",
    "message": "Starting project generation...",
    "status": "initializing",
    "timestamp": "2025-01-18T10:30:00Z"
}

{
    "type": "status_update",
    "message": "Analyzing your requirements...",
    "status": "analyzing",
    "progress": 15,
    "timestamp": "2025-01-18T10:30:05Z"
}

{
    "type": "status_update",
    "message": "Generating project files...",
    "status": "generating",
    "progress": 45,
    "timestamp": "2025-01-18T10:30:15Z"
}
```

**File Generation Updates:**
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
    "content_preview": "from django.shortcuts import render\nfrom django.views.generic import ListView...",
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
        "description": "A dynamic blog application",
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
    "message": "I've added a comment system to your blog. Here's what I implemented...",
    "files_modified": ["blog/models.py", "blog/views.py", "blog/templates/blog/post_detail.html"],
    "suggestions": ["Add comment moderation", "Implement comment threading"],
    "timestamp": "2025-01-18T10:35:00Z"
}
```

**Error Analysis and Fix:**
```json
{
    "type": "error_analysis_started",
    "message": "Analyzing error and generating fix...",
    "timestamp": "2025-01-18T10:36:00Z"
}

{
    "type": "error_fix_generated",
    "error_diagnosis": "The error is caused by a duplicate key constraint violation in the database...",
    "fix_steps": [
        "Remove duplicate entries from the database",
        "Add unique constraint validation in the model",
        "Update the migration file"
    ],
    "code_changes": {
        "blog/models.py": {
            "action": "modify",
            "content": "class Post(models.Model):\n    title = models.CharField(max_length=200, unique=True)..."
        }
    },
    "auto_fixable": true,
    "confidence_level": "high",
    "timestamp": "2025-01-18T10:36:10Z"
}

{
    "type": "fixes_applied",
    "applied_fixes": [
        {
            "file": "blog/models.py",
            "action": "modified",
            "success": true
        }
    ],
    "message": "Applied 1 fixes automatically",
    "timestamp": "2025-01-18T10:36:15Z"
}
```

**Codebase Analysis:**
```json
{
    "type": "codebase_analysis_completed",
    "analysis": {
        "project_metadata": {
            "total_files": 25,
            "total_lines": 1500,
            "languages": {".py": 15, ".html": 8, ".css": 2}
        },
        "django_structure": {
            "apps": ["blog", "accounts"],
            "models": ["Post", "Comment", "User"],
            "views": ["PostListView", "PostDetailView", "CommentCreateView"]
        },
        "code_quality": {
            "complexity": {"average": "medium", "highest": "blog/views.py"},
            "security_issues": [],
            "performance_issues": ["N+1 query in PostListView"]
        }
    },
    "message": "Codebase analysis completed",
    "timestamp": "2025-01-18T10:37:00Z"
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
    "output": "Operations to perform:\n  Apply all migrations: admin, auth, blog, contenttypes, sessions\nRunning migrations:\n  Applying blog.0001_initial... OK",
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
    "message": "Failed to generate project: Claude API rate limit exceeded",
    "timestamp": "2025-01-18T10:30:00Z"
}
```

#### 2. File Watcher WebSocket
**Endpoint:** `ws://localhost:8000/ws/projects/{project_id}/files/`

**Description:** Real-time file watching and collaborative editing

**Connection:**
```javascript
const fileWs = new WebSocket(`ws://localhost:8000/ws/projects/${projectId}/files/`);

fileWs.onmessage = function(event) {
    const data = JSON.parse(event.data);
    handleFileChange(data);
};
```

**Message Types (Outgoing):**
```javascript
// Watch a specific file
fileWs.send(JSON.stringify({
    type: 'watch_file',
    file_path: 'blog/models.py'
}));

// Save file content
fileWs.send(JSON.stringify({
    type: 'save_file',
    file_path: 'blog/models.py',
    content: 'from django.db import models\n\nclass Post(models.Model):\n    title = models.CharField(max_length=200)\n    content = models.TextField()'
}));

// Get file content
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
    "content": "from django.db import models\n\nclass Post(models.Model):\n    title = models.CharField(max_length=200)\n    content = models.TextField()\n    created_at = models.DateTimeField(auto_now_add=True)",
    "timestamp": "2025-01-18T10:30:00Z"
}
```

**File Changed:**
```json
{
    "type": "file_changed",
    "file_path": "blog/models.py",
    "content": "from django.db import models\n\nclass Post(models.Model):\n    title = models.CharField(max_length=200)\n    content = models.TextField()\n    created_at = models.DateTimeField(auto_now_add=True)\n    updated_at = models.DateTimeField(auto_now=True)",
    "timestamp": "2025-01-18T10:31:00Z"
}
```

### WebSocket Authentication

WebSocket connections require authentication. Include the authentication token in the connection:

```javascript
const ws = new WebSocket(`ws://localhost:8000/ws/projects/${projectId}/generate/`, [], {
    headers: {
        'Authorization': `Token ${userToken}`
    }
});
```

### WebSocket Error Handling

```javascript
ws.onerror = function(error) {
    console.error('WebSocket error:', error);
};

ws.onclose = function(event) {
    if (event.wasClean) {
        console.log('WebSocket connection closed cleanly');
    } else {
        console.error('WebSocket connection died');
        // Implement reconnection logic
    }
};
```

### Session Memory Integration

The WebSocket connections integrate with Redis-based session memory to:
- Maintain conversation history across connections
- Persist project context and user preferences
- Enable conversation resumption after disconnection
- Track user activity and session statistics

**Session Management:**
```javascript
// Session data is automatically managed
// Each WebSocket connection maintains session state
// Conversations persist across reconnections
// Session IDs are managed server-side
```

---

## SDK Integration
The API is designed to work seamlessly with frontend frameworks:

### React Example
```jsx
import { useEffect, useState } from 'react';

function ProjectGenerator({ projectId }) {
  const [status, setStatus] = useState('');
  const [files, setFiles] = useState([]);
  
  const generateProject = async (prompt) => {
    const eventSource = new EventSource(`/api/projects/${projectId}/smart_generate_stream/`);
    
    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.type === 'status') {
        setStatus(data.message);
      } else if (data.type === 'file_created') {
        setFiles(prev => [...prev, data.file]);
      } else if (data.type === 'completed') {
        setStatus('Project generated successfully!');
        eventSource.close();
      }
    };
  };
  
  return (
    <div>
      <div>Status: {status}</div>
      <div>Files: {files.length}</div>
    </div>
  );
}
```

This comprehensive API documentation provides everything needed to integrate with the Django AI Builder system, enabling powerful AI-driven Django application development workflows.