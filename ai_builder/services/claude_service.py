from django.conf import settings
from django.contrib.auth.models import User
from typing import Dict, List, Optional
import json
import re
import logging
import anthropic
import time

logger = logging.getLogger(__name__)


class ClaudeService:
    def __init__(self, api_key: str = None, user: Optional[User] = None):
        if api_key:
            self.client = anthropic.Anthropic(api_key=api_key)
        else:
            claude_key = getattr(settings, 'CLAUDE_API_KEY', None)
            logger.info(f"Loading Claude API key from settings: {claude_key[:20] if claude_key else 'None'}...")
            self.client = anthropic.Anthropic(api_key=claude_key)
        self.system_prompt = self._get_django_system_prompt()
        self.model_name = "claude-opus-4-20250514"
        self.user = user
    
    def _get_django_system_prompt(self):
        return """You are a Django expert assistant that creates complete, working Django applications.

CRITICAL RULES:
1. ALWAYS respond with valid JSON only
2. ALWAYS include ALL necessary files for the feature to work
3. ALWAYS include a requirements.txt file with dependencies
4. Generate complete, functional code - no placeholders or comments like "# Add your logic here"

DJANGO IMPORT REQUIREMENTS (VERY IMPORTANT):
- For urls.py: ALWAYS use "from django.urls import path" (NEVER from django.contrib)
- For views.py: Use "from django.shortcuts import render, redirect, get_object_or_404"
- For models.py: Use "from django.db import models"
- For admin.py: Use "from django.contrib import admin"
- For forms.py: Use "from django import forms"
- For serializers.py: Use "from rest_framework import serializers"
- NEVER use incorrect imports like "from django.contrib import include"

For every user request, you must generate:
- Models (if needed)
- Views (class-based preferred)
- URLs routing
- Templates (if web interface needed)
- Serializers (if API needed)
- Forms (if forms needed)
- Admin registration (if applicable)
- requirements.txt with ALL dependencies

RESPONSE FORMAT (JSON ONLY):
{
  "explanation": "Brief explanation of what was created",
  "files": [
    {
      "path": "app_name/models.py",
      "content": "from django.db import models\\n\\nclass YourModel(models.Model):\\n    # Complete model definition here",
      "action": "create"
    },
    {
      "path": "app_name/views.py", 
      "content": "from django.shortcuts import render\\nfrom rest_framework import generics\\n# Complete views here",
      "action": "create"
    },
    {
      "path": "app_name/urls.py",
      "content": "from django.urls import path\\nfrom . import views\\n\\nurlpatterns = [\\n    # Complete URL patterns\\n]",
      "action": "create"
    },
    {
      "path": "requirements.txt",
      "content": "Django>=5.0\\ndjangorestframework\\n# All other dependencies",
      "action": "create"
    }
  ],
  "commands": [
    "python manage.py makemigrations",
    "python manage.py migrate"
  ]
}

CRITICAL JSON FORMATTING RULES:
- NEVER use triple quotes inside JSON strings
- Use escaped quotes for quotes inside content
- Use \\n for line breaks in content strings
- Ensure all JSON is properly formatted and parseable
- Keep content strings as single-line with \\n for line breaks

EXAMPLES OF COMPLETE IMPLEMENTATIONS:

For "Create a blog app":
- models.py: Post model with title, content, author, created_at
- views.py: ListView, DetailView, CreateView for posts
- urls.py: Complete URL patterns
- templates/: List and detail templates
- admin.py: Register Post model
- forms.py: PostForm for creating posts
- requirements.txt: Django, any other packages used

For "Create a REST API for tasks":
- models.py: Task model with fields
- serializers.py: TaskSerializer
- views.py: TaskViewSet or API views
- urls.py: API URL patterns
- requirements.txt: Django, djangorestframework

NEVER respond with incomplete code or "TODO" comments. Always provide working, complete implementations."""
    
    def _track_token_usage(self, prompt_tokens: int, completion_tokens: int, 
                          usage_type: str, operation_description: str = "",
                          project=None, response_time_ms: int = None, 
                          success: bool = True, error_message: str = "") -> bool:
        """Track token usage for the current user"""
        if not self.user:
            return True  # No user to track
        
        # Import here to avoid circular imports
        from ..billing_services import TokenService
        
        total_tokens = prompt_tokens + completion_tokens
        
        return TokenService.use_tokens(
            user=self.user,
            token_count=total_tokens,
            usage_type=usage_type,
            project=project,
            operation_description=operation_description,
            request_data={'prompt_tokens': prompt_tokens, 'completion_tokens': completion_tokens},
            response_data={'total_tokens': total_tokens},
            response_time_ms=response_time_ms,
            success=success,
            error_message=error_message
        )
    
    def _check_token_limits(self, estimated_tokens: int) -> tuple[bool, str]:
        """Check if user can use estimated tokens"""
        if not self.user:
            return True, "No user tracking"
        
        # Import here to avoid circular imports
        from ..billing_services import TokenService
        
        return TokenService.can_user_use_tokens(self.user, estimated_tokens)

    def generate_code(self, user_prompt: str, project_context: Dict, project=None) -> Dict:
        """Generate Django code based on user prompt and project context"""
        start_time = time.time()
        
        # Estimate token usage for pre-check (rough estimate)
        estimated_tokens = len(user_prompt) // 3 + 4000  # Conservative estimate
        
        # Check token limits before proceeding
        can_use, reason = self._check_token_limits(estimated_tokens)
        if not can_use:
            logger.warning(f"Token limit exceeded for user {self.user}: {reason}")
            return {
                'success': False,
                'error': f'Token limit exceeded: {reason}',
                'token_limit_exceeded': True
            }
        
        # Create a more specific prompt based on the request
        enhanced_prompt = self._create_enhanced_prompt(user_prompt, project_context)
        
        try:
            response = self.client.messages.create(
                model=self.model_name,
                max_tokens=4000,
                temperature=0.1,
                system=self.system_prompt,
                messages=[
                    {"role": "user", "content": enhanced_prompt}
                ]
            )
            
            # Calculate response time
            response_time_ms = int((time.time() - start_time) * 1000)
            
            # Track token usage
            prompt_tokens = response.usage.input_tokens
            completion_tokens = response.usage.output_tokens
            
            self._track_token_usage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                usage_type='ai_generation',
                operation_description=f"Code generation: {user_prompt[:100]}...",
                project=project,
                response_time_ms=response_time_ms,
                success=True
            )
            
            content = response.content[0].text.strip()
            logger.info(f"Raw Claude response length: {len(content)}")
            logger.info(f"Tokens used - Input: {prompt_tokens}, Output: {completion_tokens}, Total: {prompt_tokens + completion_tokens}")
            
            # Clean and parse JSON
            parsed_response = self._parse_json_response(content)
            
            # Validate and enhance the response
            validated_response = self._validate_and_enhance_response(parsed_response, user_prompt)
            
            # Add token usage info to response
            validated_response['token_usage'] = {
                'prompt_tokens': prompt_tokens,
                'completion_tokens': completion_tokens,
                'total_tokens': prompt_tokens + completion_tokens,
                'response_time_ms': response_time_ms
            }
            
            return validated_response
                
        except Exception as e:
            # Track failed operation
            response_time_ms = int((time.time() - start_time) * 1000)
            self._track_token_usage(
                prompt_tokens=0,
                completion_tokens=0,
                usage_type='ai_generation',
                operation_description=f"FAILED: Code generation: {user_prompt[:100]}...",
                project=project,
                response_time_ms=response_time_ms,
                success=False,
                error_message=str(e)
            )
            
            logger.error(f"Error generating code: {e}")
            return self._create_error_response(str(e))
    
    def _create_enhanced_prompt(self, user_prompt: str, project_context: Dict) -> str:
        """Create a more specific prompt based on the user's request"""
        
        # Analyze the user prompt to determine what type of Django app they want
        prompt_lower = user_prompt.lower()
        
        context_info = f"""
PROJECT CONTEXT:
- Project Name: {project_context.get('name', 'Unknown')}
- Django Version: {project_context.get('django_version', '5.0')}
- Main App Name: {project_context.get('app_name', 'main')}
- Existing Files: {len(project_context.get('files', []))} files

IMPORTANT: 
- The Django project structure is already created with startproject/startapp
- Generate code that will be AUTOMATICALLY INTEGRATED into the existing Django project
- The app will be automatically registered in INSTALLED_APPS and URLs will be included
- Focus on creating complete, working Django app code

USER REQUEST: {user_prompt}

"""
        
        app_name = project_context.get('app_name', 'main')
        
        if any(word in prompt_lower for word in ['blog', 'post', 'article']):
            specific_prompt = context_info + f"""
Create a complete Django blog application using the app name '{app_name}' with:
1. Post model (title, content, author, created_at, updated_at, published)
2. Category model linked to posts
3. Views for listing posts, post detail, creating posts
4. Templates for all views
5. URL routing with app_name = '{app_name}'
6. Admin interface
7. Forms for creating/editing posts

IMPORTANT: Use the existing app directory '{app_name}' - do NOT create a new 'blog' directory.
All files should be in the '{app_name}/' directory.

Generate ALL necessary files for a working blog application.
"""
        
        elif any(word in prompt_lower for word in ['api', 'rest', 'endpoint']):
            specific_prompt = context_info + f"""
Create a complete Django REST API using the app name '{app_name}' with:
1. Models for the requested entities
2. Serializers for all models
3. ViewSets or APIViews with full CRUD operations
4. URL routing for API endpoints with app_name = '{app_name}'
5. Permissions and authentication if needed
6. requirements.txt with djangorestframework

IMPORTANT: Use the existing app directory '{app_name}' - do NOT create new app directories.
All files should be in the '{app_name}/' directory.

Generate ALL necessary files for a working REST API.
"""
        
        elif any(word in prompt_lower for word in ['todo', 'task', 'list']):
            specific_prompt = context_info + f"""
Create a complete Django todo/task application using the app name '{app_name}' with:
1. Task model (title, description, completed, priority, due_date, created_at)
2. Views for listing, creating, updating, deleting tasks
3. Templates with forms
4. URL routing with app_name = '{app_name}'
5. Admin interface
6. Optional: REST API endpoints

IMPORTANT: Use the existing app directory '{app_name}' - do NOT create new app directories.
All files should be in the '{app_name}/' directory.

Generate ALL necessary files for a working todo application.
"""
        
        elif any(word in prompt_lower for word in ['ecommerce', 'shop', 'product', 'store']):
            specific_prompt = context_info + """
Create a complete Django e-commerce application with:
1. Product model (name, description, price, stock, image, category)
2. Category model
3. Order and OrderItem models
4. Views for product listing, detail, cart functionality
5. Templates for all views
6. URL routing
7. Admin interface

Generate ALL necessary files for a working e-commerce site.
"""
        
        elif any(word in prompt_lower for word in ['user', 'auth', 'login', 'register']):
            specific_prompt = context_info + """
Create a complete Django authentication system with:
1. Custom User model (if needed) or extend default User
2. Registration, login, logout views
3. Profile model and views
4. Password reset functionality
5. Templates for all auth views
6. URL routing
7. Forms for registration and login

Generate ALL necessary files for a working authentication system.
"""
        
        else:
            # Generic prompt for other requests
            specific_prompt = context_info + f"""
Based on the user request "{user_prompt}", create a complete Django application using the app name '{app_name}' with:
1. All necessary models with proper relationships
2. Views (class-based preferred) for all CRUD operations
3. Templates for web interface (if needed)
4. URL routing with app_name = '{app_name}'
5. Forms (if needed)
6. Admin interface
7. Serializers and API views (if API functionality requested)
8. requirements.txt with all dependencies

IMPORTANT: Use the existing app directory '{app_name}' - do NOT create new app directories.
All files should be in the '{app_name}/' directory.

Ensure the application is complete and functional. Generate ALL necessary files.
"""
        
        return specific_prompt
    
    def _parse_json_response(self, content: str) -> Dict:
        """Parse JSON response with multiple fallback strategies"""
        
        # Strategy 1: Direct JSON parsing
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass
        
        # Strategy 2: Remove markdown and try again
        try:
            cleaned = re.sub(r'```json\s*', '', content)
            cleaned = re.sub(r'```\s*$', '', cleaned)
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass
        
        # Strategy 3: Extract JSON object
        try:
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass
        
        # Strategy 4: Try to fix common JSON issues
        try:
            fixed_content = self._fix_json_content(content)
            if fixed_content:
                return json.loads(fixed_content)
        except json.JSONDecodeError:
            pass
        
        # Strategy 5: Manual parsing as last resort
        return self._manual_parse_response(content)
    
    def _fix_json_content(self, content: str) -> str:
        """Fix common JSON formatting issues"""
        try:
            # Find JSON boundaries
            start_idx = content.find('{')
            if start_idx == -1:
                return None
            
            # Find matching closing brace
            brace_count = 0
            end_idx = -1
            for i, char in enumerate(content[start_idx:], start_idx):
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end_idx = i
                        break
            
            if end_idx == -1:
                return None
            
            json_content = content[start_idx:end_idx + 1]
            
            # Fix common issues
            json_content = re.sub(r',(\s*[}\]])', r'\1', json_content)  # Remove trailing commas
            json_content = re.sub(r'[\r\n]+', ' ', json_content)  # Replace newlines in strings
            
            return json_content
            
        except Exception as e:
            logger.error(f"Error fixing JSON: {e}")
            return None
    
    def _manual_parse_response(self, content: str) -> Dict:
        """Manually parse response when JSON parsing fails"""
        
        # Extract explanation
        explanation_match = re.search(r'"explanation"\s*:\s*"([^"]*)"', content, re.DOTALL)
        explanation = explanation_match.group(1) if explanation_match else "Generated Django application"
        
        # Extract files
        files = []
        
        # Look for file patterns
        file_patterns = [
            r'"path"\s*:\s*"([^"]*)".*?"content"\s*:\s*"(.*?)".*?"action"\s*:\s*"([^"]*)"',
            r'"path":\s*"([^"]*)".*?"content":\s*"(.*?)"'
        ]
        
        for pattern in file_patterns:
            matches = re.findall(pattern, content, re.DOTALL)
            for match in matches:
                if len(match) >= 2:
                    file_obj = {
                        "path": match[0],
                        "content": match[1].replace('\\n', '\n'),
                        "action": match[2] if len(match) > 2 else "create"
                    }
                    files.append(file_obj)
                if len(files) >= 10:  # Limit files
                    break
            if files:
                break
        
        # Extract commands
        commands = []
        command_matches = re.findall(r'"(python manage\.py [^"]*)"', content)
        commands.extend(command_matches[:5])  # Limit commands
        
        if not commands:
            commands = ["python manage.py makemigrations", "python manage.py migrate"]
        
        return {
            "explanation": explanation,
            "files": files,
            "commands": commands
        }
    
    def _validate_and_enhance_response(self, response: Dict, user_prompt: str) -> Dict:
        """Validate and enhance the response to ensure completeness"""
        
        if not isinstance(response, dict):
            return self._create_fallback_response(user_prompt)
        
        # Ensure required keys exist
        if 'explanation' not in response:
            response['explanation'] = f"Generated Django application for: {user_prompt}"
        
        if 'files' not in response or not response['files']:
            response['files'] = self._generate_basic_files(user_prompt)
        
        if 'commands' not in response or not response['commands']:
            response['commands'] = [
                "python manage.py makemigrations",
                "python manage.py migrate"
            ]
        
        # Ensure requirements.txt exists
        has_requirements = any(f.get('path', '').endswith('requirements.txt') for f in response['files'])
        if not has_requirements:
            requirements_content = self._generate_requirements_content(response['files'])
            response['files'].append({
                "path": "requirements.txt",
                "content": requirements_content,
                "action": "create"
            })
        
        return response
    
    def _generate_basic_files(self, user_prompt: str) -> List[Dict]:
        """Generate basic Django files when Claude doesn't provide them"""
        
        app_name = "myapp"
        
        # Basic model
        model_content = f'''from django.db import models
from django.contrib.auth.models import User

class Item(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    
    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['-created_at']
'''
        
        # Basic views
        views_content = f'''from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Item
from .forms import ItemForm

class ItemListView(ListView):
    model = Item
    template_name = '{app_name}/item_list.html'
    context_object_name = 'items'
    paginate_by = 10

class ItemDetailView(DetailView):
    model = Item
    template_name = '{app_name}/item_detail.html'
    context_object_name = 'item'

class ItemCreateView(LoginRequiredMixin, CreateView):
    model = Item
    form_class = ItemForm
    template_name = '{app_name}/item_form.html'
    
    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)
'''
        
        # Basic URLs
        urls_content = f'''from django.urls import path
from . import views

app_name = '{app_name}'

urlpatterns = [
    path('', views.ItemListView.as_view(), name='item_list'),
    path('item/<int:pk>/', views.ItemDetailView.as_view(), name='item_detail'),
    path('create/', views.ItemCreateView.as_view(), name='item_create'),
]
'''
        
        # Basic forms
        forms_content = f'''from django import forms
from .models import Item

class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ['title', 'description']
        widgets = {{
            'title': forms.TextInput(attrs={{'class': 'form-control'}}),
            'description': forms.Textarea(attrs={{'class': 'form-control', 'rows': 4}}),
        }}
'''
        
        # Basic admin
        admin_content = f'''from django.contrib import admin
from .models import Item

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'created_at']
    list_filter = ['created_at', 'author']
    search_fields = ['title', 'description']
    readonly_fields = ['created_at', 'updated_at']
'''
        
        return [
            {"path": f"{app_name}/models.py", "content": model_content, "action": "create"},
            {"path": f"{app_name}/views.py", "content": views_content, "action": "create"},
            {"path": f"{app_name}/urls.py", "content": urls_content, "action": "create"},
            {"path": f"{app_name}/forms.py", "content": forms_content, "action": "create"},
            {"path": f"{app_name}/admin.py", "content": admin_content, "action": "create"},
        ]
    
    def _generate_requirements_content(self, files: List[Dict]) -> str:
        """Generate requirements.txt content based on the files"""
        
        requirements = set(["Django>=5.0"])
        
        # Check file contents for imports to determine requirements
        for file_info in files:
            content = file_info.get('content', '')
            
            if 'rest_framework' in content:
                requirements.add('djangorestframework')
            if 'channels' in content:
                requirements.add('channels')
                requirements.add('channels-redis')
            if 'dotenv' in content:
                requirements.add('python-dotenv')
            if 'Pillow' in content or 'PIL' in content:
                requirements.add('Pillow')
            if 'celery' in content:
                requirements.add('celery')
                requirements.add('redis')
        
        return '\n'.join(sorted(requirements))
    
    def _create_fallback_response(self, user_prompt: str) -> Dict:
        """Create a basic fallback response"""
        return {
            "explanation": f"Created a basic Django application structure for: {user_prompt}",
            "files": self._generate_basic_files(user_prompt),
            "commands": [
                "python manage.py makemigrations",
                "python manage.py migrate"
            ]
        }
    
    def _create_error_response(self, error_message: str) -> Dict:
        """Create error response"""
        return {
            "explanation": f"Error generating code: {error_message}",
            "files": [],
            "commands": [],
            "error": error_message
        }
    
    def analyze_error(self, error_message: str, file_content: str) -> Dict:
        """Analyze error and suggest fixes"""
        prompt = f"""Analyze this Django error and provide a solution in JSON format:

Error: {error_message}

File content:
{file_content}

Respond with JSON:
{{
    "explanation": "Clear explanation of the error and solution",
    "corrected_code": "The corrected file content",
    "additional_steps": ["step 1", "step 2"]
}}
"""
        
        try:
            response = self.client.messages.create(
                model=self.model_name,
                max_tokens=2000,
                temperature=0.1,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            content = response.content[0].text.strip()
            return self._parse_json_response(content)
            
        except Exception as e:
            logger.error(f"Error analyzing: {e}")
            return {
                "explanation": f"Error analyzing: {str(e)}",
                "corrected_code": file_content,
                "additional_steps": []
            }
    
    def stream_generate_code(self, user_prompt: str, project_context: str = "", callback=None):
        """Generate code with token-by-token streaming like bolt.new"""
        
        full_prompt = f"""
{self.system_prompt}

PROJECT CONTEXT:
{project_context}

USER REQUEST: {user_prompt}

Generate the complete Django solution as JSON with this structure:
{{
    "files": [
        {{
            "filename": "path/to/file.py",
            "content": "complete file content",
            "description": "What this file does"
        }}
    ],
    "explanation": "How the solution works",
    "requirements": ["Django>=4.0", "other-package"]
}}
"""
        
        try:
            # Claude streaming API call
            response = self.client.messages.create(
                model=self.model_name,
                max_tokens=4000,
                temperature=0.3,
                system=self.system_prompt,
                messages=[{"role": "user", "content": full_prompt}],
                stream=True  # Enable token-level streaming
            )
            
            full_content = ""
            current_file = None
            current_filename = None
            current_content = ""
            
            for chunk in response:
                if chunk.type == "content_block_delta":
                    token = chunk.delta.text
                    full_content += token
                    
                    # Parse streaming JSON to detect file creation
                    if callback:
                        # Check if we're starting a new file
                        if '"filename":' in token and '"content":' not in current_content:
                            # Extract filename from the streaming token
                            import re
                            filename_match = re.search(r'"filename":\s*"([^"]+)"', full_content)
                            if filename_match:
                                new_filename = filename_match.group(1)
                                if new_filename != current_filename:
                                    current_filename = new_filename
                                    current_content = ""
                                    
                                    # Notify new file creation
                                    callback({
                                        'type': 'file_started',
                                        'filename': current_filename,
                                        'content': ''
                                    })
                        
                        # Check if we're writing file content
                        elif '"content":' in full_content and current_filename:
                            # Extract content being written
                            content_match = re.search(r'"content":\s*"([^"]*)', full_content)
                            if content_match:
                                new_content = content_match.group(1)
                                if len(new_content) > len(current_content):
                                    # New tokens added to file content
                                    current_content = new_content
                                    
                                    # Stream token-by-token update
                                    callback({
                                        'type': 'file_content_token',
                                        'filename': current_filename,
                                        'content': current_content.replace('\\n', '\n').replace('\\"', '"'),
                                        'token': token
                                    })
            
            # Parse final response
            return self._parse_json_response(full_content)
            
        except Exception as e:
            logger.error(f"Streaming generation error: {e}")
            return self._create_error_response(f"Generation failed: {str(e)}")