# Django AI Builder - Frontend Documentation

## Overview
This document provides comprehensive API documentation for building a frontend application that interfaces with the Django AI Builder backend. The system allows users to create AI-powered Django projects dynamically through a web interface.

## Table of Contents
1. [Authentication System](#authentication-system)
2. [Core API Endpoints](#core-api-endpoints)
3. [Data Models](#data-models)
4. [WebSocket/Streaming](#websocketstreaming)
5. [Error Handling](#error-handling)
6. [Frontend Requirements](#frontend-requirements)
7. [Implementation Examples](#implementation-examples)

---

## Authentication System

### JWT Token-Based Authentication
The API uses JWT tokens for authentication. All protected endpoints require an `Authorization: Bearer <token>` header.

### Authentication Endpoints

#### 1. User Registration
```
POST /auth/register/
Content-Type: application/json

{
  "username": "string",
  "email": "string",
  "password": "string",
  "first_name": "string",
  "last_name": "string"
}

Response:
{
  "user": {
    "id": 1,
    "username": "string",
    "email": "string",
    "first_name": "string",
    "last_name": "string"
  },
  "tokens": {
    "access": "jwt_access_token",
    "refresh": "jwt_refresh_token"
  }
}
```

#### 2. User Login
```
POST /auth/login/
Content-Type: application/json

{
  "username": "string",
  "password": "string"
}

Response:
{
  "user": {
    "id": 1,
    "username": "string",
    "email": "string",
    "first_name": "string",
    "last_name": "string"
  },
  "tokens": {
    "access": "jwt_access_token",
    "refresh": "jwt_refresh_token"
  }
}
```

#### 3. Token Refresh
```
POST /auth/token/refresh/
Content-Type: application/json

{
  "refresh": "jwt_refresh_token"
}

Response:
{
  "access": "new_jwt_access_token"
}
```

#### 4. User Profile
```
GET /auth/profile/
Authorization: Bearer <token>

Response:
{
  "id": 1,
  "username": "string",
  "email": "string",
  "first_name": "string",
  "last_name": "string"
}
```

#### 5. Logout
```
POST /auth/logout/
Authorization: Bearer <token>
Content-Type: application/json

{
  "refresh": "jwt_refresh_token"
}

Response:
{
  "message": "Logout successful"
}
```

---

## Core API Endpoints

### Project Management

#### 1. List Projects
```
GET /api/projects/
Authorization: Bearer <token>

Response:
{
  "count": 10,
  "next": "url_to_next_page",
  "previous": "url_to_previous_page",
  "results": [
    {
      "id": "uuid",
      "name": "string",
      "description": "string",
      "python_version": "3.11",
      "django_version": "5.0",
      "container_id": "string",
      "container_port": 8001,
      "is_running": false,
      "files_count": 15,
      "django_project_created": true,
      "main_app_name": "main",
      "last_prompt": "string",
      "ai_generation_status": "completed",
      "created_at": "2025-01-01T00:00:00Z",
      "updated_at": "2025-01-01T00:00:00Z"
    }
  ]
}
```

#### 2. Create Project
```
POST /api/projects/
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "string",
  "description": "string",
  "python_version": "3.11",
  "django_version": "5.0",
  "project_type": "web_app",
  "complexity_level": "simple",
  "target_audience": "string",
  "key_features": ["user authentication", "file upload"],
  "technical_requirements": {}
}

Response:
{
  "id": "uuid",
  "name": "string",
  "description": "string",
  "python_version": "3.11",
  "django_version": "5.0",
  "container_id": null,
  "container_port": null,
  "is_running": false,
  "files_count": 0,
  "django_project_created": false,
  "main_app_name": null,
  "last_prompt": "",
  "ai_generation_status": "ready",
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-01-01T00:00:00Z"
}
```

#### 3. Get Project Details
```
GET /api/projects/{id}/
Authorization: Bearer <token>

Response: Same as Create Project response
```

#### 4. Update Project
```
PUT /api/projects/{id}/
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "string",
  "description": "string",
  "python_version": "3.11",
  "django_version": "5.0"
}

Response: Same as Create Project response
```

#### 5. Delete Project
```
DELETE /api/projects/{id}/
Authorization: Bearer <token>

Response: 204 No Content
```

### Container Management

#### 1. Start Container
```
POST /api/projects/{id}/start_container/
Authorization: Bearer <token>

Response:
{
  "message": "Container started successfully",
  "port": 8001,
  "container_id": "string"
}
```

#### 2. Stop Container
```
POST /api/projects/{id}/stop_container/
Authorization: Bearer <token>

Response:
{
  "message": "Container stopped successfully"
}
```

### AI Generation

#### 1. Smart Generate (Main AI Endpoint)
```
POST /api/projects/{id}/smart_generate/
Authorization: Bearer <token>
Content-Type: application/json

{
  "message": "Create a blog application with user authentication and post management"
}

Response:
{
  "message": "Successfully generated a complete Django project: **Blog App**\n\n**Project Overview:**\n- **Description:** A full-featured blog application\n- **Features:** User authentication, Post management, Comments\n- **Files Generated:** 25\n\n**Technology Stack:**\n- **Backend:** Django, DRF, SQLite\n- **Frontend:** HTML, CSS, JavaScript\n- **Database:** SQLite\n\n**Setup Instructions:**\n• Install dependencies: pip install -r requirements.txt\n• Run migrations: python manage.py migrate\n• Create superuser: python manage.py createsuperuser\n• Start server: python manage.py runserver\n\n**API Endpoints:**\n• /api/posts/ [GET, POST] - List and create posts\n• /api/posts/{id}/ [GET, PUT, DELETE] - Post details\n• /api/comments/ [GET, POST] - Comments management\n\n**Next Steps:**\n• Start the development server\n• Access admin at /admin/\n• Test API endpoints\n• Customize styling\n\nYour project is ready to use at: http://localhost:8000",
  "project_structure": {
    "project_name": "Blog App",
    "description": "A full-featured blog application",
    "features": ["User authentication", "Post management", "Comments"],
    "tech_stack": {
      "backend": ["Django", "DRF", "SQLite"],
      "frontend": ["HTML", "CSS", "JavaScript"],
      "database": "SQLite"
    }
  },
  "files": [
    {
      "id": 1,
      "path": "manage.py",
      "content": "#!/usr/bin/env python...",
      "file_type": "py",
      "size": 1024,
      "created_at": "2025-01-01T00:00:00Z",
      "updated_at": "2025-01-01T00:00:00Z",
      "is_ai_generated": true,
      "ai_merge_status": "new",
      "original_content": ""
    }
  ],
  "commands": ["pip install -r requirements.txt", "python manage.py migrate"],
  "processing_time": 15.5,
  "django_project_created": true,
  "project_path": "/user_projects/uuid",
  "generation_type": "smart_complete",
  "api_endpoints": [
    {
      "url": "/api/posts/",
      "methods": ["GET", "POST"],
      "purpose": "List and create posts"
    }
  ],
  "access_url": "http://localhost:8000"
}
```

#### 2. Smart Generate Stream (Real-time Updates)
```
POST /api/projects/{id}/smart_generate_stream/
Authorization: Bearer <token>
Content-Type: application/json

{
  "message": "Create a blog application with user authentication"
}

Response: Server-Sent Events (SSE) stream
Content-Type: text/event-stream

data: {"type": "status", "message": "Starting project generation...", "status": "initializing"}

data: {"type": "status", "message": "Analyzing your requirements...", "status": "analyzing"}

data: {"type": "status", "message": "Project structure created! Generating files...", "status": "generating"}

data: {"type": "file_created", "file": "manage.py", "progress": 10}

data: {"type": "file_created", "file": "settings.py", "progress": 20}

data: {"type": "completed", "message": "Project generated successfully!", "project_structure": {...}, "files": [...]}
```

### File Management

#### 1. Get Project Files
```
GET /api/projects/{id}/files/
Authorization: Bearer <token>

Response:
[
  {
    "id": 1,
    "path": "manage.py",
    "content": "#!/usr/bin/env python...",
    "file_type": "py",
    "size": 1024,
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-01-01T00:00:00Z",
    "is_ai_generated": true,
    "ai_merge_status": "new",
    "original_content": ""
  }
]
```

#### 2. Get Filesystem Files
```
GET /api/projects/{id}/filesystem_files/
Authorization: Bearer <token>

Response:
[
  {
    "path": "manage.py",
    "size": 1024,
    "modified": "2025-01-01T00:00:00Z",
    "type": "file",
    "is_directory": false,
    "extension": "py"
  }
]
```

#### 3. Get File Content
```
GET /api/projects/{id}/files/content/?path=manage.py
Authorization: Bearer <token>

Response:
{
  "path": "manage.py",
  "content": "#!/usr/bin/env python\nimport os\nimport sys..."
}
```

#### 4. Save File
```
POST /api/projects/{id}/save_file/
Authorization: Bearer <token>
Content-Type: application/json

{
  "path": "manage.py",
  "content": "#!/usr/bin/env python\nimport os\nimport sys..."
}

Response:
{
  "message": "File manage.py saved successfully"
}
```

### Chat & Conversation

#### 1. Conversational Chat
```
POST /api/projects/{id}/conversation_chat/
Authorization: Bearer <token>
Content-Type: application/json

{
  "message": "Add a contact form to the website",
  "is_error": false,
  "error_type": "",
  "error_source": ""
}

Response:
{
  "message": "I'll help you add a contact form to your website. Here's what I've implemented:\n\n1. Created a Contact model\n2. Added a contact form\n3. Created contact views\n4. Added contact templates\n\nThe contact form includes fields for name, email, subject, and message.",
  "files_modified": ["main/models.py", "main/forms.py", "main/views.py"],
  "code_changes": {
    "main/models.py": "Added Contact model with fields: name, email, subject, message, created_at",
    "main/forms.py": "Added ContactForm with validation",
    "main/views.py": "Added contact_view function"
  },
  "suggestions": [
    "Add email backend configuration for sending emails",
    "Style the contact form with CSS",
    "Add form validation on the frontend"
  ],
  "processing_time": 3.2,
  "thread_id": "uuid",
  "error_fixed": false
}
```

#### 2. Error Reporting
```
POST /api/projects/{id}/report_error/
Authorization: Bearer <token>
Content-Type: application/json

{
  "error_message": "NameError: name 'app_name' is not defined",
  "error_type": "runtime_error",
  "error_source": "main/views.py:25"
}

Response: Same as conversational chat response
```

#### 3. Get Conversation History
```
GET /api/projects/{id}/conversation_history/
Authorization: Bearer <token>

Response:
{
  "thread_id": "uuid",
  "messages": [
    {
      "id": 1,
      "role": "user",
      "content": "Create a blog application",
      "message_type": "normal",
      "timestamp": "2025-01-01T00:00:00Z",
      "tokens_used": null,
      "processing_time": null,
      "is_error_report": false,
      "error_type": "",
      "error_source": "",
      "files_modified": [],
      "code_changes": {},
      "created_at": "2025-01-01T00:00:00Z"
    }
  ],
  "total_messages": 10
}
```

### Command Execution

#### 1. Execute Command
```
POST /api/projects/{id}/execute_command/
Authorization: Bearer <token>
Content-Type: application/json

{
  "command": "python manage.py migrate"
}

Response:
{
  "output": "Operations to perform:\n  Apply all migrations: admin, auth, contenttypes, sessions, main\nRunning migrations:\n  Applying main.0001_initial... OK",
  "error": "",
  "exit_code": 0
}
```

#### 2. Get Command History
```
GET /api/projects/{id}/executions/
Authorization: Bearer <token>

Response:
[
  {
    "id": 1,
    "command": "python manage.py migrate",
    "output": "Operations to perform...",
    "error_output": "",
    "exit_code": 0,
    "execution_time": 2.5,
    "executed_at": "2025-01-01T00:00:00Z"
  }
]
```

### Project Statistics

#### 1. Get Project Stats
```
GET /api/projects/{id}/stats/
Authorization: Bearer <token>

Response:
{
  "files_count": 25,
  "total_lines": 1500,
  "total_size": 45000,
  "messages_count": 10,
  "executions_count": 5,
  "last_activity": "2025-01-01T00:00:00Z",
  "is_running": false
}
```

---

## Data Models

### Project Model
```typescript
interface Project {
  id: string; // UUID
  name: string;
  description: string;
  python_version: string;
  django_version: string;
  container_id: string | null;
  container_port: number | null;
  is_running: boolean;
  files_count: number;
  django_project_created: boolean;
  main_app_name: string | null;
  last_prompt: string;
  ai_generation_status: 'ready' | 'generating' | 'completed' | 'error';
  created_at: string;
  updated_at: string;
  
  // Extended fields (not in serializer by default)
  project_type: 'web_app' | 'api' | 'blog' | 'ecommerce' | 'dashboard' | 'social' | 'portfolio' | 'business' | 'education' | 'entertainment' | 'custom';
  complexity_level: 'simple' | 'medium' | 'complex' | 'enterprise';
  target_audience: string;
  key_features: string[];
  technical_requirements: object;
  original_prompt: string;
  prompt_history: PromptHistory[];
  generated_features: string[];
}

interface PromptHistory {
  timestamp: string;
  prompt: string;
  type: 'initial' | 'enhancement';
}
```

### Project File Model
```typescript
interface ProjectFile {
  id: number;
  path: string;
  content: string;
  file_type: string;
  size: number;
  created_at: string;
  updated_at: string;
  is_ai_generated: boolean;
  ai_merge_status: 'none' | 'new' | 'merged' | 'conflict';
  original_content: string;
}
```

### Chat Message Model
```typescript
interface ChatMessage {
  id: number;
  role: 'user' | 'assistant' | 'system';
  content: string;
  message_type: 'normal' | 'error_report' | 'code_request' | 'fix_applied' | 'system_notification';
  timestamp: string;
  tokens_used: number | null;
  processing_time: number | null;
  is_error_report: boolean;
  error_type: string;
  error_source: string;
  files_modified: string[];
  code_changes: object;
  created_at: string;
}
```

### Command Execution Model
```typescript
interface CommandExecution {
  id: number;
  command: string;
  output: string;
  error_output: string;
  exit_code: number;
  execution_time: number;
  executed_at: string;
}
```

---

## WebSocket/Streaming

### Server-Sent Events (SSE)
The API supports real-time updates through Server-Sent Events for AI generation:

```javascript
// Frontend implementation example
const eventSource = new EventSource('/api/projects/{id}/smart_generate_stream/', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});

eventSource.onmessage = function(event) {
  const data = JSON.parse(event.data);
  
  switch(data.type) {
    case 'status':
      updateProgressBar(data.message, data.status);
      break;
    case 'file_created':
      addFileToList(data.file);
      updateProgress(data.progress);
      break;
    case 'completed':
      onGenerationComplete(data);
      break;
    case 'error':
      onGenerationError(data.message);
      break;
  }
};

eventSource.onerror = function(event) {
  console.error('SSE error:', event);
};
```

---

## Error Handling

### HTTP Status Codes
- `200 OK` - Success
- `201 Created` - Resource created successfully
- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Permission denied
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

### Error Response Format
```json
{
  "error": "Error message description",
  "details": "Additional error details (optional)"
}
```

### Validation Errors
```json
{
  "field_name": ["Error message for this field"],
  "another_field": ["Another error message"]
}
```

---

## Frontend Requirements

### Core Features Needed
1. **User Authentication**
   - Login/Register forms
   - Token management
   - Protected routes

2. **Project Dashboard**
   - Project listing
   - Project creation
   - Project cards with status indicators

3. **AI Project Generator**
   - Prompt input interface
   - Real-time generation progress
   - File tree viewer
   - Code editor integration

4. **Chat Interface**
   - Conversational UI
   - Message history
   - Error reporting
   - File modification tracking

5. **File Management**
   - File tree navigation
   - Code editor
   - File saving
   - Syntax highlighting

6. **Container Management**
   - Start/Stop buttons
   - Status indicators
   - Port display
   - Access links

### Recommended Tech Stack
- **Framework**: React, Vue.js, or Angular
- **State Management**: Redux, Vuex, or NgRx
- **HTTP Client**: Axios or Fetch API
- **Code Editor**: Monaco Editor or CodeMirror
- **UI Components**: Material-UI, Ant Design, or Tailwind CSS
- **Real-time**: EventSource API for SSE

---

## Implementation Examples

### 1. Authentication Service
```typescript
class AuthService {
  private apiUrl = 'http://localhost:8000';
  private token: string | null = localStorage.getItem('token');

  async login(username: string, password: string): Promise<AuthResponse> {
    const response = await fetch(`${this.apiUrl}/auth/login/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ username, password }),
    });

    if (!response.ok) {
      throw new Error('Login failed');
    }

    const data = await response.json();
    this.token = data.tokens.access;
    localStorage.setItem('token', this.token);
    localStorage.setItem('refreshToken', data.tokens.refresh);
    
    return data;
  }

  async makeAuthenticatedRequest(url: string, options: RequestInit = {}): Promise<Response> {
    const headers = {
      ...options.headers,
      'Authorization': `Bearer ${this.token}`,
    };

    return fetch(url, { ...options, headers });
  }
}
```

### 2. Project Service
```typescript
class ProjectService {
  private authService: AuthService;

  constructor(authService: AuthService) {
    this.authService = authService;
  }

  async getProjects(): Promise<Project[]> {
    const response = await this.authService.makeAuthenticatedRequest('/api/projects/');
    const data = await response.json();
    return data.results;
  }

  async createProject(projectData: CreateProjectRequest): Promise<Project> {
    const response = await this.authService.makeAuthenticatedRequest('/api/projects/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(projectData),
    });

    return response.json();
  }

  async generateWithAI(projectId: string, prompt: string): Promise<GenerationResponse> {
    const response = await this.authService.makeAuthenticatedRequest(
      `/api/projects/${projectId}/smart_generate/`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: prompt }),
      }
    );

    return response.json();
  }
}
```

### 3. Real-time Generation Component
```tsx
import React, { useState, useEffect } from 'react';

interface GenerationProgress {
  status: string;
  message: string;
  progress?: number;
  files?: string[];
}

const AIGenerationComponent: React.FC<{ projectId: string; prompt: string }> = ({ 
  projectId, 
  prompt 
}) => {
  const [progress, setProgress] = useState<GenerationProgress>({
    status: 'idle',
    message: '',
  });
  const [eventSource, setEventSource] = useState<EventSource | null>(null);

  const startGeneration = () => {
    const token = localStorage.getItem('token');
    const url = `/api/projects/${projectId}/smart_generate_stream/`;
    
    const es = new EventSource(url, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    es.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setProgress(data);
      
      if (data.type === 'completed' || data.type === 'error') {
        es.close();
      }
    };

    es.onerror = (error) => {
      console.error('SSE error:', error);
      es.close();
    };

    setEventSource(es);
  };

  useEffect(() => {
    return () => {
      if (eventSource) {
        eventSource.close();
      }
    };
  }, [eventSource]);

  return (
    <div className="generation-progress">
      <h3>AI Generation Progress</h3>
      <div className="status">{progress.status}</div>
      <div className="message">{progress.message}</div>
      {progress.progress && (
        <div className="progress-bar">
          <div 
            className="progress-fill" 
            style={{ width: `${progress.progress}%` }}
          />
        </div>
      )}
      {progress.files && (
        <div className="files-created">
          <h4>Files Created:</h4>
          <ul>
            {progress.files.map((file, index) => (
              <li key={index}>{file}</li>
            ))}
          </ul>
        </div>
      )}
      <button onClick={startGeneration}>Start Generation</button>
    </div>
  );
};
```

### 4. Chat Interface Component
```tsx
import React, { useState, useEffect } from 'react';

interface ChatMessage {
  id: number;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  files_modified?: string[];
}

const ChatInterface: React.FC<{ projectId: string }> = ({ projectId }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    loadConversationHistory();
  }, [projectId]);

  const loadConversationHistory = async () => {
    const token = localStorage.getItem('token');
    const response = await fetch(`/api/projects/${projectId}/conversation_history/`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
    const data = await response.json();
    setMessages(data.messages);
  };

  const sendMessage = async () => {
    if (!inputMessage.trim()) return;

    const userMessage = {
      id: Date.now(),
      role: 'user' as const,
      content: inputMessage,
      timestamp: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/projects/${projectId}/conversation_chat/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: inputMessage }),
      });

      const data = await response.json();
      
      const assistantMessage = {
        id: Date.now() + 1,
        role: 'assistant' as const,
        content: data.message,
        timestamp: new Date().toISOString(),
        files_modified: data.files_modified,
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Failed to send message:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="chat-interface">
      <div className="messages">
        {messages.map((message) => (
          <div key={message.id} className={`message ${message.role}`}>
            <div className="content">{message.content}</div>
            {message.files_modified && message.files_modified.length > 0 && (
              <div className="files-modified">
                <strong>Files modified:</strong>
                <ul>
                  {message.files_modified.map((file, index) => (
                    <li key={index}>{file}</li>
                  ))}
                </ul>
              </div>
            )}
            <div className="timestamp">{new Date(message.timestamp).toLocaleString()}</div>
          </div>
        ))}
      </div>
      <div className="input-area">
        <input
          type="text"
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
          placeholder="Type your message..."
          disabled={isLoading}
        />
        <button onClick={sendMessage} disabled={isLoading || !inputMessage.trim()}>
          {isLoading ? 'Sending...' : 'Send'}
        </button>
      </div>
    </div>
  );
};
```

### 5. File Editor Component
```tsx
import React, { useState, useEffect } from 'react';
import { Editor } from '@monaco-editor/react';

interface FileEditorProps {
  projectId: string;
  filePath: string;
  onSave?: (content: string) => void;
}

const FileEditor: React.FC<FileEditorProps> = ({ projectId, filePath, onSave }) => {
  const [content, setContent] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    loadFileContent();
  }, [projectId, filePath]);

  const loadFileContent = async () => {
    setIsLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(
        `/api/projects/${projectId}/files/content/?path=${encodeURIComponent(filePath)}`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        }
      );
      const data = await response.json();
      setContent(data.content);
    } catch (error) {
      console.error('Failed to load file:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const saveFile = async () => {
    setIsSaving(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/projects/${projectId}/save_file/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          path: filePath,
          content: content,
        }),
      });

      if (response.ok) {
        onSave?.(content);
      }
    } catch (error) {
      console.error('Failed to save file:', error);
    } finally {
      setIsSaving(false);
    }
  };

  const getLanguage = (filePath: string) => {
    const extension = filePath.split('.').pop()?.toLowerCase();
    switch (extension) {
      case 'py': return 'python';
      case 'js': return 'javascript';
      case 'ts': return 'typescript';
      case 'html': return 'html';
      case 'css': return 'css';
      case 'json': return 'json';
      case 'md': return 'markdown';
      default: return 'text';
    }
  };

  if (isLoading) {
    return <div>Loading file...</div>;
  }

  return (
    <div className="file-editor">
      <div className="editor-header">
        <span className="file-path">{filePath}</span>
        <button onClick={saveFile} disabled={isSaving}>
          {isSaving ? 'Saving...' : 'Save'}
        </button>
      </div>
      <Editor
        height="400px"
        language={getLanguage(filePath)}
        value={content}
        onChange={(value) => setContent(value || '')}
        theme="vs-dark"
        options={{
          minimap: { enabled: false },
          fontSize: 14,
          wordWrap: 'on',
        }}
      />
    </div>
  );
};
```

---

## Dashboard Features

### Project Cards
Each project should display:
- Project name and description
- Status indicators (running, generating, error)
- Last activity timestamp
- Quick action buttons (start/stop, chat, files)
- Progress indicators for AI generation

### Real-time Updates
- Container status changes
- AI generation progress
- File modifications
- Error notifications

### Navigation
- Project list/grid view
- Project details view
- File explorer
- Chat interface
- Settings

---

## Security Considerations

1. **Token Management**
   - Store tokens securely
   - Handle token expiration
   - Implement refresh logic

2. **Input Validation**
   - Sanitize user inputs
   - Validate file paths
   - Limit file sizes

3. **Rate Limiting**
   - Implement client-side rate limiting
   - Handle API rate limit responses

4. **Error Handling**
   - Don't expose sensitive error details
   - Log errors appropriately
   - Provide user-friendly messages

---

This documentation provides a comprehensive guide for frontend developers to integrate with the Django AI Builder API. The system supports real-time AI-powered project generation, conversational interfaces, and full project management capabilities.