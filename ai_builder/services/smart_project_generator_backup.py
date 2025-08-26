import os
import json
import logging
import subprocess
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import re

from .claude_service import ClaudeService
from .validation_service import ValidationService, ValidationLevel, GenerationSequence

# Configure comprehensive logging
logger = logging.getLogger(__name__)

# Ensure logger is properly configured
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


class SmartProjectGenerator:
    """
    Dynamic Django project generator that creates complete project structures
    based on AI analysis of user prompts. Everything is generated dynamically.
    """
    
    def __init__(self, base_dir: str, user=None):
        self.base_dir = Path(base_dir)
        self.claude_service = ClaudeService(user=user)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.user = user
        
        # Initialize validation service
        self.validation_service = None  # Will be initialized per project
        
        # Initialize error tracking
        self.generation_errors = []
        self.generation_stats = {
            'files_attempted': 0,
            'files_succeeded': 0,
            'files_failed': 0,
            'retries_used': 0,
            'total_generation_time': 0,
            'validation_warnings': 0,
            'validation_errors': 0
        }
    
    def _track_error(self, error_type: str, error_message: str, context: dict = None):
        """Track errors for analysis and debugging."""
        error_entry = {
            'timestamp': datetime.now().isoformat(),
            'error_type': error_type,
            'error_message': str(error_message),
            'context': context or {},
            'stack_trace': None
        }
        
        # Capture stack trace for debugging
        import traceback
        error_entry['stack_trace'] = traceback.format_exc()
        
        self.generation_errors.append(error_entry)
        logger.error(f"Error tracked: {error_type} - {error_message}", extra={'context': context})
    
    def _update_stats(self, stat_name: str, increment: int = 1):
        """Update generation statistics."""
        if stat_name in self.generation_stats:
            self.generation_stats[stat_name] += increment
    
    def _read_file_content(self, file_path: Path) -> str:
        """Helper to read file content safely"""
        try:
            if file_path.exists():
                return file_path.read_text(encoding='utf-8')
            return ""
        except Exception as e:
            logger.error(f"Failed to read file {file_path}: {e}")
            return ""
    
    def _build_file_tree(self, project_path: Path) -> dict:
        """Build file tree structure for frontend display"""
        def build_tree(path: Path, name: str = None) -> dict:
            if name is None:
                name = path.name
            
            if path.is_file():
                return {
                    'name': name,
                    'type': 'file',
                    'path': str(path.relative_to(project_path))
                }
            elif path.is_dir():
                children = []
                try:
                    for child in sorted(path.iterdir()):
                        if not child.name.startswith('.'):
                            children.append(build_tree(child))
                except PermissionError:
                    pass
                
                return {
                    'name': name,
                    'type': 'directory',
                    'path': str(path.relative_to(project_path)),
                    'children': children
                }
        
        return build_tree(project_path, project_path.name)

    def get_generation_report(self) -> dict:
        """Get comprehensive generation report including errors and stats."""
        success_rate = 0
        if self.generation_stats['files_attempted'] > 0:
            success_rate = (self.generation_stats['files_succeeded'] / self.generation_stats['files_attempted']) * 100
        
        return {
            'statistics': self.generation_stats,
            'success_rate': round(success_rate, 2),
            'errors': self.generation_errors,
            'error_summary': self._get_error_summary()
        }
    
    def _get_error_summary(self) -> dict:
        """Get summary of errors by type."""
        error_counts = {}
        for error in self.generation_errors:
            error_type = error['error_type']
            error_counts[error_type] = error_counts.get(error_type, 0) + 1
        
        return {
            'total_errors': len(self.generation_errors),
            'error_types': error_counts,
            'most_common_error': max(error_counts.items(), key=lambda x: x[1])[0] if error_counts else None
        }
    
    def generate_project_from_prompt(self, user_prompt: str, project_id: str) -> Dict:
        """
        Generate complete Django project structure from user prompt.
        EVERYTHING is dynamically generated based on the user's request.
        """
        
        try:
            # Validate inputs
            if not user_prompt or not user_prompt.strip():
                return {
                    'success': False,
                    'error': 'User prompt is required and cannot be empty'
                }
            
            if not project_id or not project_id.strip():
                return {
                    'success': False,
                    'error': 'Project ID is required and cannot be empty'
                }
            
            logger.info(f"Starting dynamic project generation for: {project_id}")
            
            # Step 1: Analyze and plan the entire project with AI
            project_plan = self._create_complete_project_plan(user_prompt, project_id)
            
            if not project_plan or not project_plan.get('success'):
                error_msg = 'Failed to create project plan'
                if project_plan and project_plan.get('error'):
                    error_msg += f": {project_plan.get('error')}"
                return {
                    'success': False,
                    'error': error_msg,
                    'details': project_plan.get('error') if project_plan else 'Unknown error'
                }
            
            # Validate the plan structure
            plan_data = project_plan['plan']
            required_fields = ['project_name', 'description', 'apps']
            missing_fields = [field for field in required_fields if field not in plan_data]
            
            if missing_fields:
                return {
                    'success': False,
                    'error': f'Invalid project plan: missing required fields: {", ".join(missing_fields)}'
                }
            
            # Ensure apps is a list and not empty
            if not isinstance(plan_data.get('apps'), list) or len(plan_data['apps']) == 0:
                return {
                    'success': False,
                    'error': 'Project plan must include at least one app'
                }
            
            # Step 2: Create project directory
            project_path = self.base_dir / project_id
            try:
                if project_path.exists():
                    shutil.rmtree(project_path)
                project_path.mkdir(parents=True)
            except Exception as e:
                return {
                    'success': False,
                    'error': f'Failed to create project directory: {str(e)}'
                }
            
            # Step 3: Generate ALL files dynamically based on the plan
            generation_result = self._generate_entire_project(
                project_plan['plan'],
                project_path,
                user_prompt
            )
            
            if not generation_result['success']:
                return generation_result
            
            # Step 4: Set up Python environment and install dependencies
            setup_result = self._setup_project_environment(
                project_path,
                project_plan['plan']
            )
            
            # Step 5: Initialize Django project structure
            django_result = self._initialize_django_project(
                project_path,
                project_plan['plan']
            )
            
            
            print(project_plan['plan'].get('api_endpoints', []))
            return {
                'success': True,
                'project_id': project_id,
                'project_path': str(project_path),
                'project_name': project_plan['plan']['project_name'],
                'description': project_plan['plan']['description'],
                'features': project_plan['plan']['features'],
                'tech_stack': project_plan['plan']['tech_stack'],
                'files_generated': generation_result['files_count'],
                'setup_instructions': project_plan['plan']['setup_instructions'],
                'access_url': 'http://localhost:8000',
                'api_endpoints': project_plan['plan'].get('api_endpoints', []),
                'next_steps': project_plan['plan']['next_steps']
            }
            
        except Exception as e:
            logger.error(f"Critical error in project generation: {e}", exc_info=True)
            return {
                'success': False,
                'error': f"Project generation failed: {str(e)}"
            }
    
    def _create_complete_project_plan(self, user_prompt: str, project_id: str) -> Dict:
        """
        Use AI to create a complete project plan based on user input.
        This is where the magic happens - AI understands and plans everything.
        """
        
        planning_prompt = f"""
You are an expert Django architect. Create a complete, production-ready Django project plan based on this request:

USER REQUEST: "{user_prompt}"
PROJECT ID: "{project_id}"

Create a comprehensive project plan that includes EVERYTHING needed for a complete Django application.
Be creative and build EXACTLY what the user wants - not generic templates.

Your response must be a valid JSON object with this structure:

{{
    "project_name": "snake_case_name (derived from user request)",
    "description": "Clear description of what this project does",
    "features": ["List", "of", "all", "features", "the", "project", "will", "have"],
    "tech_stack": {{
        "backend": ["Django", "other backend tech"],
        "frontend": ["specific frontend tech based on request"],
        "database": "SQLite (lightweight and included with Python)",
        "additional": ["any other tech needed"]
    }},
    "apps": [
        {{
            "name": "app_name",
            "purpose": "What this app does",
            "models": [
                {{
                    "name": "ModelName",
                    "fields": [
                        {{"name": "field_name", "type": "CharField", "options": {{"max_length": 200}}}},
                        {{"name": "description", "type": "TextField", "options": {{"blank": true}}}}
                    ],
                    "methods": ["__str__", "get_absolute_url", "custom_method"],
                    "meta": {{"ordering": ["-created_at"], "verbose_name": "Model Name"}}
                }}
            ],
            "views": [
                {{
                    "name": "ViewName",
                    "type": "ListView/DetailView/CreateView/function",
                    "purpose": "What this view does",
                    "template": "template_name.html",
                    "context": ["additional", "context", "variables"]
                }}
            ],
            "urls": [
                {{"pattern": "path/", "view": "ViewName", "name": "url_name"}}
            ],
            "templates": [
                {{
                    "name": "template_name.html",
                    "purpose": "What this template displays",
                    "includes_forms": true/false,
                    "uses_ajax": true/false
                }}
            ],
            "forms": [
                {{
                    "name": "FormName",
                    "model": "ModelName",
                    "fields": ["field1", "field2"],
                    "widgets": {{"field1": "TextInput"}}
                }}
            ],
            "api_endpoints": [
                {{
                    "url": "/api/endpoint/",
                    "methods": ["GET", "POST"],
                    "purpose": "What this endpoint does"
                }}
            ]
        }}
    ],
    "dependencies": [
        "Django==5.0",
        "# All required Python packages with versions based on features",
        "# Include packages for: authentication, API, database, frontend integration, etc."
    ],
    "environment_variables": [
        {{"name": "SECRET_KEY", "description": "Django secret key"}},
        {{"name": "DATABASE_URL", "description": "Database connection string"}}
    ],
    "static_files": {{
        "css": ["style.css", "other.css"],
        "js": ["app.js", "other.js"],
        "images": ["logo.png", "favicon.ico"]
    }},
    "deployment": {{
        "dockerfile": true/false,
        "docker_compose": true/false,
        "nginx_config": true/false,
        "ci_cd": "github_actions/gitlab_ci/none"
    }},
    "testing": {{
        "framework": "pytest/unittest",
        "coverage_threshold": 80,
        "test_categories": ["unit", "integration", "e2e"]
    }},
    "security": {{
        "authentication": "django-allauth/djangorestframework-simplejwt/custom/simple",
        "permissions": ["list", "of", "permission", "types"],
        "api_authentication": "token/jwt/session"
    }},
    "ui_design": {{
        "theme": "modern/classic/minimal",
        "primary_color": "#hexcode",
        "framework": "bootstrap/tailwind/custom",
        "responsive": true,
        "animations": true/false
    }},
    "special_features": {{
        "websockets": true/false,
        "celery_tasks": true/false,
        "caching": "redis/memcached/none",
        "search": "elasticsearch/postgresql/none",
        "file_uploads": true/false,
        "email_sending": true/false,
        "payments": "stripe/paypal/none",
        "social_login": ["google", "github", "facebook"] or []
    }},
    "setup_instructions": [
        "Step 1: ...",
        "Step 2: ...",
        "# Complete setup instructions"
    ],
    "api_documentation": {{
        "format": "swagger/redoc/none",
        "auto_generate": true/false
    }},
    "next_steps": [
        "What the user should do after generation",
        "Customization suggestions",
        "Deployment recommendations"
    ]
}}

IMPORTANT GUIDELINES:
1. Be SPECIFIC - no generic "YourModel" or "Item" - use actual domain terms
2. Include ALL files needed for a complete, working application
3. Follow Django best practices and conventions
4. Make it production-ready with proper error handling, logging, etc.
5. Include modern features based on the request (real-time, API, etc.)
6. Design beautiful, user-friendly interfaces
7. Add authentication/authorization as appropriate
8. Include tests for critical functionality
9. Make it scalable and maintainable
10. Be creative and exceed expectations!

ANALYZE THE USER'S REQUEST DEEPLY:
- What type of application do they want?
- What features are implied but not explicitly stated?
- What would make this application amazing?
- What technical choices best fit their needs?

Generate a complete, detailed plan for an amazing Django application!
"""
        
        try:
            response = self.claude_service.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=8000,
                temperature=0.3,
                messages=[
                    {"role": "user", "content": planning_prompt}
                ]
            )
            
            content = response.content[0].text.strip()
            plan = self._parse_json_response(content)
            
            if plan:
                # Add the user prompt to the plan for later reference
                plan['user_prompt'] = user_prompt
                return {
                    'success': True,
                    'plan': plan
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to parse project plan'
                }
            
        except Exception as e:
            logger.error(f"Error creating project plan: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _generate_entire_project(self, project_plan: Dict, project_path: Path, user_prompt: str) -> Dict:
        """
        Generate ALL project files dynamically based on the plan.
        Each file is created by AI specifically for this project.
        """
        
        generated_files = []
        
        try:
            # 1. Generate Django project files
            logger.info("Generating Django core files...")
            try:
                django_files = self._generate_django_core_files(project_plan, project_path)
                generated_files.extend(django_files)
                logger.info(f"Generated {len(django_files)} Django core files")
            except Exception as e:
                logger.error(f"Failed to generate Django core files: {e}")
                raise Exception(f"Django core file generation failed: {str(e)}")
            
            # 2. Generate app files for each app
            logger.info(f"Generating {len(project_plan['apps'])} Django apps...")
            for i, app_config in enumerate(project_plan['apps'], 1):
                try:
                    # Validate app config
                    if not isinstance(app_config, dict) or 'name' not in app_config:
                        logger.warning(f"Skipping invalid app config at index {i-1}: {app_config}")
                        continue
                    
                    logger.info(f"Generating app {i}/{len(project_plan['apps'])}: {app_config['name']}")
                    app_files = self._generate_complete_app(
                        app_config,
                        project_plan,
                        project_path,
                        user_prompt
                    )
                    generated_files.extend(app_files)
                    logger.info(f"Generated {len(app_files)} files for app {app_config['name']}")
                except Exception as e:
                    logger.error(f"Failed to generate app {app_config.get('name', f'app_{i}')}: {e}")
                    # Continue with other apps instead of failing completely
                    continue
            
            # 3. Generate static files
            try:
                logger.info("Generating static files...")
                static_files = self._generate_static_files(project_plan, project_path)
                generated_files.extend(static_files)
                logger.info(f"Generated {len(static_files)} static files")
            except Exception as e:
                logger.error(f"Failed to generate static files: {e}")
                # Static files are not critical, continue without them
            
            # 4. Generate templates
            try:
                logger.info("Generating templates...")
                template_files = self._generate_all_templates(project_plan, project_path, user_prompt)
                generated_files.extend(template_files)
                logger.info(f"Generated {len(template_files)} template files")
            except Exception as e:
                logger.error(f"Failed to generate templates: {e}")
                # Templates are critical, but we can continue with basic ones
            
            # 5. Generate configuration files
            try:
                logger.info("Generating configuration files...")
                config_files = self._generate_config_files(project_plan, project_path)
                generated_files.extend(config_files)
                logger.info(f"Generated {len(config_files)} configuration files")
            except Exception as e:
                logger.error(f"Failed to generate configuration files: {e}")
                # Config files are critical, create minimal ones
                self._create_minimal_config_files(project_path)
            
            # 6. Generate deployment files if needed
            if project_plan.get('deployment', {}).get('dockerfile'):
                try:
                    logger.info("Generating deployment files...")
                    deployment_files = self._generate_deployment_files(project_plan, project_path)
                    generated_files.extend(deployment_files)
                    logger.info(f"Generated {len(deployment_files)} deployment files")
                except Exception as e:
                    logger.error(f"Failed to generate deployment files: {e}")
                    # Deployment files are optional
            
            # 7. Generate tests
            try:
                logger.info("Generating test files...")
                test_files = self._generate_test_files(project_plan, project_path)
                generated_files.extend(test_files)
                logger.info(f"Generated {len(test_files)} test files")
            except Exception as e:
                logger.error(f"Failed to generate test files: {e}")
                # Test files are optional
            
            # 8. Generate documentation
            try:
                logger.info("Generating documentation...")
                doc_files = self._generate_documentation(project_plan, project_path, user_prompt)
                generated_files.extend(doc_files)
                logger.info(f"Generated {len(doc_files)} documentation files")
            except Exception as e:
                logger.error(f"Failed to generate documentation: {e}")
                # Documentation is optional
            
            return {
                'success': True,
                'files': generated_files,
                'files_count': len(generated_files)
            }
            
        except Exception as e:
            logger.error(f"Error generating project files: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _generate_django_core_files(self, project_plan: Dict, project_path: Path) -> List[Dict]:
        """Generate core Django project files dynamically."""
        
        project_name = project_plan['project_name']
        files = []
        
        # Generate settings.py with controlled template
        settings_content = self._generate_django_settings(project_plan, project_name)
        settings_path = project_path / project_name / 'settings.py'
        files.append(self._save_file(settings_path, settings_content))
        homepage_app = next(
            (app['name'] for app in project_plan['apps'] if app.get('homepage')), 
            project_plan['apps'][0]['name']  # fallback to first app
        )
        app_urls_includes = f"path('', include('{homepage_app}.urls')),\n" + "\n".join(
    [f"path('{app['name']}/', include('{app['name']}.urls'))," for app in project_plan['apps'] if app['name'] != homepage_app]
)


        # Generate urls.py
        urls_prompt = f"""
Generate the main urls.py file for Django project '{project_name}'.

Project structure:
- Project name: {project_name}
- Apps: {[app['name'] for app in project_plan['apps']]}
- Homepage app: {homepage_app}
- Has API endpoints: {any(app.get('api_endpoints') for app in project_plan['apps'])}

Create a complete urls.py that includes:
1. from django.contrib import admin
2. from django.urls import path, include
3. from django.conf import settings
4. from django.conf.urls.static import static
5. Admin URL: admin/
6. 6. These app includes:
{app_urls_includes}
7. Static/media file serving for development
8. API URLs if needed

Make sure all imports are correct and URL patterns are properly formatted.
Return ONLY the Python code.
"""
        
        urls_content = self._generate_code_with_ai(urls_prompt)
        urls_path = project_path / project_name / 'urls.py'
        files.append(self._save_file(urls_path, urls_content))
        
        # Generate wsgi.py and asgi.py
        for file_type in ['wsgi', 'asgi']:
            content = self._generate_standard_django_file(file_type, project_name)
            file_path = project_path / project_name / f'{file_type}.py'
            files.append(self._save_file(file_path, content))
        
        # Generate __init__.py
        init_path = project_path / project_name / '__init__.py'
        files.append(self._save_file(init_path, ''))
        
        # Generate manage.py
        manage_content = self._generate_manage_py(project_name)
        manage_path = project_path / 'manage.py'
        files.append(self._save_file(manage_path, manage_content))
        os.chmod(manage_path, 0o755)  # Make executable
        
        return files
    
    def _generate_complete_app(self, app_config: Dict, project_plan: Dict, project_path: Path, user_prompt: str) -> List[Dict]:
        """Generate all files for a Django app dynamically."""
        
        app_name = app_config['name']
        app_path = project_path / app_name
        app_path.mkdir(parents=True, exist_ok=True)
        
        files = []
        
        # 1. Generate models.py (ALWAYS generate - create basic models.py even if empty)
        models_prompt = f"""
Generate models.py for Django app '{app_name}'.

Original user request: "{user_prompt}"
App purpose: {app_config['purpose']}
Models to create: {json.dumps(app_config.get('models', []), indent=2)}

Requirements:
- Import all necessary Django modules (django.db.models)
- Create all models with specified fields if models are defined
- If no models are specified, create a basic models.py with imports
- Add proper field types and options
- Include Meta classes
- Add __str__ methods
- Add any custom methods specified
- Include proper relationships between models
- Add verbose names and help text
- Follow Django best practices

IMPORTANT: Always create a valid models.py file even if no models are specified.

Return ONLY the Python code.
"""
        
        models_content = self._generate_code_with_ai(models_prompt)
        files.append(self._save_file(app_path / 'models.py', models_content))
        
        # 2. Generate views.py (ALWAYS generate - essential for Django apps)
        views_prompt = f"""
Generate views.py for Django app '{app_name}'.

Original user request: "{user_prompt}"
App purpose: {app_config['purpose']}
Views to create: {json.dumps(app_config.get('views', []), indent=2)}
Models available: {[model['name'] for model in app_config.get('models', [])]}

Requirements:
- Import all necessary modules (render, HttpResponse, etc.)
- Create all specified views (class-based and function-based)
- If no specific views are defined, create at least a basic index/home view for this app
- Include proper error handling
- Add authentication/permissions as needed
- Include context data
- Handle forms if applicable
- Add AJAX support where specified
- Follow Django best practices
- Ensure the app has functional views that can be accessed

IMPORTANT: Even if no specific views are provided, create a basic functional view structure.

Return ONLY the Python code.
"""
        
        views_content = self._generate_code_with_ai(views_prompt)
        files.append(self._save_file(app_path / 'views.py', views_content))
        
        # 3. Generate urls.py (ALWAYS generate - essential for Django apps)
        urls_prompt = f"""
Generate urls.py for Django app '{app_name}'.

URL patterns to create: {json.dumps(app_config.get('urls', []), indent=2)}
App name: {app_name}
Views available: Based on the views.py that was just generated
Models available: {[model['name'] for model in app_config.get('models', [])]}

Requirements:
- Include proper URL patterns with names
- Connect to appropriate views that exist in the views.py
- Include app_name = '{app_name}' for namespacing
- If no specific URLs are defined, create basic URL patterns for any views that were generated
- Ensure all generated views have corresponding URL patterns
- Follow Django URL naming conventions

IMPORTANT: Every generated view must have a corresponding URL pattern.

Return ONLY the Python code.
"""
        
        urls_content = self._generate_code_with_ai(urls_prompt)
        files.append(self._save_file(app_path / 'urls.py', urls_content))
        
        # 4. Generate forms.py (Generate if forms are specified OR models exist)
        if app_config.get('forms') or app_config.get('models'):
            forms_prompt = f"""
Generate forms.py for Django app '{app_name}'.

Forms to create: {json.dumps(app_config.get('forms', []), indent=2)}
Models available: {[model['name'] for model in app_config.get('models', [])]}

Requirements:
- All necessary imports
- ModelForms and regular Forms as specified
- If no specific forms are defined but models exist, create basic ModelForms for each model
- Custom widgets where appropriate
- Validation methods
- Help texts and labels
- Crispy forms if applicable

IMPORTANT: If models exist but no forms are specified, create basic ModelForms to enable CRUD operations.

Return ONLY the Python code.
"""
            
            forms_content = self._generate_code_with_ai(forms_prompt)
            files.append(self._save_file(app_path / 'forms.py', forms_content))
        
        # 5. Generate admin.py (ALWAYS generate)
        admin_prompt = f"""
Generate admin.py for Django app '{app_name}'.

Models: {[model['name'] for model in app_config.get('models', [])]}

Requirements:
- Import django.contrib.admin
- Create custom admin classes for each model if models exist
- If no models exist, create a basic admin.py with just the import
- List display, filters, search fields for models
- Inline models where appropriate
- Custom actions
- Fieldsets for better organization
- Read-only fields for timestamps

IMPORTANT: Always create a valid admin.py file even if no models exist.

Return ONLY the Python code.
"""
        
        admin_content = self._generate_code_with_ai(admin_prompt)
        files.append(self._save_file(app_path / 'admin.py', admin_content))
        
        # 6. Generate serializers.py if API endpoints exist
        if app_config.get('api_endpoints'):
            serializers_prompt = f"""
Generate serializers.py for Django REST Framework.

App: {app_name}
Models: {[model['name'] for model in app_config.get('models', [])]}
API endpoints: {json.dumps(app_config['api_endpoints'], indent=2)}

Create serializers with proper fields, validation, and nested relationships.
Return ONLY the Python code.
"""
            
            serializers_content = self._generate_code_with_ai(serializers_prompt)
            files.append(self._save_file(app_path / 'serializers.py', serializers_content))
        
        # 7. Generate apps.py
        apps_content = f"""from django.apps import AppConfig


class {app_name.capitalize()}Config(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = '{app_name}'
    verbose_name = '{app_name.replace("_", " ").title()}'
"""
        files.append(self._save_file(app_path / 'apps.py', apps_content))
        
        # 8. Generate __init__.py
        files.append(self._save_file(app_path / '__init__.py', ''))
        
        # 9. Generate tests.py
        tests_prompt = f"""
Generate tests.py for Django app '{app_name}'.

Models to test: {[model['name'] for model in app_config.get('models', [])]}
Views to test: {[view['name'] for view in app_config.get('views', [])]}

Create comprehensive tests including:
- Model tests
- View tests
- Form tests
- API tests if applicable
- Edge cases

Use {project_plan.get('testing', {}).get('framework', 'unittest')}.
Return ONLY the Python code.
"""
        
        tests_content = self._generate_code_with_ai(tests_prompt)
        files.append(self._save_file(app_path / 'tests.py', tests_content))
        
        # 10. Create migrations directory
        migrations_path = app_path / 'migrations'
        migrations_path.mkdir(exist_ok=True)
        files.append(self._save_file(migrations_path / '__init__.py', ''))
        
        # 11. Create templates directory for this app
        templates_path = app_path / 'templates' / app_name
        templates_path.mkdir(parents=True, exist_ok=True)
        
        # 12. Create static directory for this app
        static_path = app_path / 'static' / app_name
        static_path.mkdir(parents=True, exist_ok=True)
        
        return files
    
    def _generate_all_templates(self, project_plan: Dict, project_path: Path, user_prompt: str) -> List[Dict]:
        """Generate all HTML templates dynamically based on the project plan."""
        
        files = []
        templates_path = project_path / 'templates'
        templates_path.mkdir(exist_ok=True)
        
        # Generate base template with advanced features
        base_template_prompt = f"""
Create a comprehensive base.html template for this Django project:

Project: {project_plan['project_name']}
Description: {project_plan['description']}
UI Design: {json.dumps(project_plan.get('ui_design', {}), indent=2)}
Features: {project_plan['features']}
Project Type: {project_plan.get('project_type', 'web_app')}

Requirements:
- Modern, responsive design using {project_plan.get('ui_design', {}).get('framework', 'Bootstrap 5')}
- Dark/light theme toggle if modern theme
- Navigation bar with dropdown menus for all apps
- User authentication UI (login/logout/register/profile)
- Real-time notifications area with toast messages
- Search functionality if applicable
- Footer with social links and project info
- SEO meta tags
- Progressive Web App (PWA) features
- Accessibility features (ARIA labels, keyboard navigation)
- Loading states and animations
- Mobile-first responsive design
- Include necessary CSS/JS CDNs and custom files

Special features based on project type:
{self._get_template_features_for_project_type(project_plan.get('project_type', 'web_app'))}

Return ONLY the HTML code.
"""
        
        base_content = self._generate_code_with_ai(base_template_prompt)
        files.append(self._save_file(templates_path / 'base.html', base_content))
        
        # Generate dynamic home page based on project type
        home_template_prompt = f"""
Create a dynamic home.html template for this Django project:

Project: {project_plan['project_name']}
Description: {project_plan['description']}
Original request: "{user_prompt}"
Features: {project_plan['features']}
Project Type: {project_plan.get('project_type', 'web_app')}

Create an engaging landing page that:
- Extends base.html
- Hero section with compelling headline and CTA
- Feature showcase with icons and descriptions
- Testimonials/reviews section if applicable
- Statistics/metrics dashboard if relevant
- Recent content/activity feed
- Call-to-action sections throughout
- Interactive elements and animations
- Mobile-optimized layout

Specific to {project_plan.get('project_type', 'web_app')}:
{self._get_home_features_for_project_type(project_plan.get('project_type', 'web_app'))}

Return ONLY the HTML code.
"""
        
        home_content = self._generate_code_with_ai(home_template_prompt)
        files.append(self._save_file(templates_path / 'home.html', home_content))
        
        # Generate authentication templates
        auth_templates = ['login.html', 'register.html', 'profile.html', 'password_reset.html']
        for auth_template in auth_templates:
            auth_prompt = f"""
Create {auth_template} for Django authentication:

Project: {project_plan['project_name']}
Theme: {project_plan.get('ui_design', {}).get('theme', 'modern')}

Create a beautiful, secure authentication page with:
- Modern form design with validation
- Social login options if configured
- Proper CSRF protection
- User-friendly error messages
- Responsive design
- Loading states
- Accessibility features

Return ONLY the HTML code.
"""
            
            auth_content = self._generate_code_with_ai(auth_prompt)
            files.append(self._save_file(templates_path / auth_template, auth_content))
        
        # Generate templates for each app with enhanced features
        for app in project_plan['apps']:
            app_templates_path = project_path / app['name'] / 'templates' / app['name']
            app_templates_path.mkdir(parents=True, exist_ok=True)
            
            # Generate standard CRUD templates for each model
            for model in app.get('models', []):
                model_name = model['name']
                model_fields = model.get('fields', [])
                
                # List view template
                list_template_prompt = f"""
Create {model_name.lower()}_list.html template for Django app '{app['name']}':

Model: {model_name}
Fields: {model_fields}
App purpose: {app['purpose']}
Features: Advanced list view with search, filtering, pagination

Create a comprehensive list template with:
- Data table with sorting and filtering
- Search functionality
- Pagination with page size options
- Bulk actions (select all, delete selected)
- Export options (CSV, PDF)
- Add new button
- Quick view modals
- Loading states and animations
- Responsive design for mobile

Return ONLY the HTML code.
"""
                
                list_content = self._generate_code_with_ai(list_template_prompt)
                files.append(self._save_file(app_templates_path / f'{model_name.lower()}_list.html', list_content))
                
                # Detail view template
                detail_template_prompt = f"""
Create {model_name.lower()}_detail.html template for Django app '{app['name']}':

Model: {model_name}
Fields: {model_fields}
App purpose: {app['purpose']}

Create a detailed view template with:
- Clean, organized field display
- Edit/Delete action buttons
- Related objects display
- Activity history if applicable
- Share functionality
- Print-friendly layout
- Image gallery if has images
- Comments section if relevant
- Breadcrumb navigation

Return ONLY the HTML code.
"""
                
                detail_content = self._generate_code_with_ai(detail_template_prompt)
                files.append(self._save_file(app_templates_path / f'{model_name.lower()}_detail.html', detail_content))
                
                # Form template (create/edit)
                form_template_prompt = f"""
Create {model_name.lower()}_form.html template for Django app '{app['name']}':

Model: {model_name}
Fields: {model_fields}
App purpose: {app['purpose']}

Create a comprehensive form template with:
- Step-by-step form wizard if complex
- Real-time validation feedback
- Auto-save functionality
- File upload with drag-and-drop if applicable
- Rich text editor for text fields
- Date/time pickers for date fields
- Image preview for image uploads
- Form progress indicator
- Cancel and save draft options
- Accessibility features

Return ONLY the HTML code.
"""
                
                form_content = self._generate_code_with_ai(form_template_prompt)
                files.append(self._save_file(app_templates_path / f'{model_name.lower()}_form.html', form_content))
            
            # Generate custom templates specified in the plan
            for template_config in app.get('templates', []):
                template_prompt = f"""
Create {template_config['name']} template for Django app '{app['name']}':

Purpose: {template_config['purpose']}
App purpose: {app['purpose']}
Original request: "{user_prompt}"
Uses forms: {template_config.get('includes_forms', False)}
Uses AJAX: {template_config.get('uses_ajax', False)}
Models: {[model['name'] for model in app.get('models', [])]}

Create an advanced template with:
- Interactive UI components
- Real-time updates if AJAX enabled
- Progressive enhancement
- Error handling and loading states
- Keyboard shortcuts
- Print-friendly version
- SEO optimization
- Social sharing if applicable

Return ONLY the HTML code.
"""
                
                template_content = self._generate_code_with_ai(template_prompt)
                template_path = app_templates_path / template_config['name']
                files.append(self._save_file(template_path, template_content))
        
        # Generate enhanced error pages
        error_pages = {
            '400': 'Bad Request',
            '403': 'Forbidden', 
            '404': 'Page Not Found',
            '500': 'Server Error',
            '503': 'Service Unavailable'
        }
        
        for error_code, error_title in error_pages.items():
            error_prompt = f"""
Create {error_code}.html error page for Django project '{project_plan['project_name']}':

Error: {error_code} - {error_title}
Project theme: {project_plan.get('ui_design', {}).get('theme', 'modern')}

Create an engaging error page with:
- Friendly, helpful message
- Search functionality
- Popular pages links
- Contact support option
- Fun illustration or animation
- Automatic redirect timer for some errors
- Consistent with project design
- Mobile-friendly layout

Return ONLY the HTML code.
"""
            
            error_content = self._generate_code_with_ai(error_prompt)
            files.append(self._save_file(templates_path / f'{error_code}.html', error_content))
        
        # Generate component templates (reusable components)
        component_templates = ['pagination.html', 'search_form.html', 'notification_toast.html', 'loading_spinner.html']
        for component in component_templates:
            component_prompt = f"""
Create reusable {component} component template:

Project: {project_plan['project_name']}
Theme: {project_plan.get('ui_design', {}).get('theme', 'modern')}

Create a modular, reusable component that:
- Can be included in other templates
- Follows design system patterns
- Is accessible and responsive
- Includes proper ARIA labels
- Has customizable parameters

Return ONLY the HTML code.
"""
            
            component_content = self._generate_code_with_ai(component_prompt)
            components_path = templates_path / 'components'
            components_path.mkdir(exist_ok=True)
            files.append(self._save_file(components_path / component, component_content))
        
        return files
    
    def _get_template_features_for_project_type(self, project_type: str) -> str:
        """Get specific template features based on project type."""
        features_map = {
            'blog': '- Article reading progress bar\n- Social sharing buttons\n- Comment system UI\n- Tag cloud widget',
            'ecommerce': '- Shopping cart dropdown\n- Product quick view modals\n- Wishlist functionality\n- Price comparison widgets',
            'social': '- Live chat interface\n- Activity feed components\n- Friend request notifications\n- Real-time messaging UI',
            'dashboard': '- Widget-based layout\n- Drag-and-drop dashboard\n- Chart containers\n- Data export options',
            'api': '- API documentation viewer\n- Request/response panels\n- Rate limiting indicators\n- Interactive API explorer',
            'portfolio': '- Image galleries\n- Project showcase grid\n- Contact form modal\n- Smooth scrolling navigation',
            'education': '- Course progress tracking\n- Quiz interface components\n- Video player controls\n- Student dashboard widgets'
        }
        return features_map.get(project_type, '- Standard web application features')
    
    def _get_home_features_for_project_type(self, project_type: str) -> str:
        """Get specific home page features based on project type."""
        features_map = {
            'blog': '- Featured articles carousel\n- Recent posts grid\n- Author spotlight\n- Newsletter signup',
            'ecommerce': '- Product categories showcase\n- Best sellers section\n- Promotional banners\n- Customer reviews',
            'social': '- Activity feed preview\n- User statistics\n- Trending topics\n- Community highlights',
            'dashboard': '- Quick stats overview\n- Recent activity feed\n- Performance metrics\n- Shortcut buttons',
            'api': '- API endpoint showcase\n- Usage statistics\n- Developer resources\n- Integration examples',
            'portfolio': '- Project gallery\n- Skills showcase\n- Client testimonials\n- Contact information',
            'education': '- Course catalog preview\n- Learning paths\n- Student achievements\n- Instructor highlights'
        }
        return features_map.get(project_type, '- General purpose content sections')
    
    def _generate_static_files(self, project_plan: Dict, project_path: Path) -> List[Dict]:
        """Generate CSS and JavaScript files dynamically."""
        
        files = []
        static_path = project_path / 'static'
        
        # Create directory structure
        css_path = static_path / 'css'
        js_path = static_path / 'js'
        img_path = static_path / 'images'
        
        for path in [css_path, js_path, img_path]:
            path.mkdir(parents=True, exist_ok=True)
        
        # Generate main CSS
        css_prompt = f"""
Create a comprehensive CSS file for this Django project:

Project: {project_plan['project_name']}
UI Design: {json.dumps(project_plan.get('ui_design', {}), indent=2)}
Primary Color: {project_plan.get('ui_design', {}).get('primary_color', '#007bff')}
Theme: {project_plan.get('ui_design', {}).get('theme', 'modern')}

Create custom CSS that:
- Implements the design theme
- Includes responsive design
- Adds smooth animations if specified
- Customizes framework components
- Looks professional and modern
- Is specific to this application type

Return ONLY the CSS code.
"""
        
        css_content = self._generate_code_with_ai(css_prompt)
        files.append(self._save_file(css_path / 'style.css', css_content))
        
        # Generate main JavaScript
        js_prompt = f"""
Create JavaScript code for this Django project:

Project: {project_plan['project_name']}
Features requiring JS: {project_plan['features']}
Uses AJAX: {any(app.get('templates', [{}])[0].get('uses_ajax', False) for app in project_plan['apps'])}
Special features: {project_plan.get('special_features', {})}

Include:
- Form validation
- AJAX handlers if needed
- Interactive UI elements
- Any feature-specific JavaScript
- Smooth user experience enhancements
- CSRF token handling for Django

Return ONLY the JavaScript code.
"""
        
        js_content = self._generate_code_with_ai(js_prompt)
        files.append(self._save_file(js_path / 'app.js', js_content))
        
        return files
    
    def _generate_config_files(self, project_plan: Dict, project_path: Path) -> List[Dict]:
        """Generate configuration files (requirements.txt, .env, etc.)."""
        
        files = []
        
        # Generate dynamic requirements.txt based on project features
        requirements_content = self._generate_dynamic_requirements(project_plan)
        files.append(self._save_file(project_path / 'requirements.txt', requirements_content))
        
        # Generate .env.example
        env_content = '\n'.join([
            f"{var['name']}={var.get('default', '')}"
            for var in project_plan.get('environment_variables', [])
        ])
        files.append(self._save_file(project_path / '.env.example', env_content))
        
        # Generate .gitignore
        gitignore_prompt = """
Create a comprehensive .gitignore file for a Django project.
Include all common Python, Django, IDE, and OS-specific files.
Return ONLY the file content.
"""
        
        gitignore_content = self._generate_code_with_ai(gitignore_prompt)
        files.append(self._save_file(project_path / '.gitignore', gitignore_content))
        
        return files
    
    def _generate_django_settings(self, project_plan: Dict, project_name: str) -> str:
        """Generate Django settings.py based on actual project structure"""
        
        # Get the actual apps that will be created
        app_names = [app['name'] for app in project_plan['apps']]
        
        # Get comprehensive project context for feature detection
        user_prompt = project_plan.get('user_prompt', '').lower()
        description = project_plan.get('description', '').lower()
        features = str(project_plan.get('features', {})).lower()
        apps_data = str(project_plan.get('apps', [])).lower()
        tech_stack = project_plan.get('tech_stack', {})
        special_features = project_plan.get('special_features', {})
        
        # Combine all text for comprehensive analysis
        full_context = f"{user_prompt} {description} {features} {apps_data}".lower()
        
        # Build INSTALLED_APPS dynamically based on detected features
        installed_apps = [
            'django.contrib.admin',
            'django.contrib.auth', 
            'django.contrib.contenttypes',
            'django.contrib.sessions',
            'django.contrib.messages',
            'django.contrib.staticfiles'
        ]
        
        # Add third-party apps based on comprehensive feature detection
        has_api = any(app.get('api_endpoints') for app in project_plan['apps'])
        if has_api or 'api' in full_context or 'rest' in full_context or 'endpoint' in full_context:
            installed_apps.extend([
                'rest_framework',
                'django_filters',
            ])
        
        if ('frontend' in full_context or 'react' in full_context or 'vue' in full_context or 
            'angular' in full_context or 'cors' in full_context or 'spa' in full_context):
            installed_apps.append('corsheaders')
        
        # WebSocket/Real-time features
        if ('websocket' in full_context or 'real-time' in full_context or 'chat' in full_context or
            'notification' in full_context or 'live' in full_context or 'socket' in full_context):
            installed_apps.extend(['channels'])
        
        # Authentication systems
        if 'auth' in full_context and ('social' in full_context or 'google' in full_context or 
                                       'github' in full_context or 'facebook' in full_context or 'oauth' in full_context):
            installed_apps.extend([
                'allauth',
                'allauth.account',
                'allauth.socialaccount',
            ])
        
        # Development tools (always include for better DX)
        installed_apps.extend([
            'django_extensions',
            'debug_toolbar',
        ])
        
        # Forms enhancement
        if ('form' in full_context or 'crispy' in full_context or 'bootstrap' in full_context):
            installed_apps.append('crispy_forms')
        
        # Import/Export functionality
        if ('data' in full_context or 'analytics' in full_context or 'report' in full_context or
            'import' in full_context or 'export' in full_context):
            installed_apps.append('import_export')
            
        # Add project apps
        installed_apps.extend(app_names)
        
        # Build middleware dynamically
        middleware = [
            'django.middleware.security.SecurityMiddleware',
            'whitenoise.middleware.WhiteNoiseMiddleware',  # Always include for static files
            'django.contrib.sessions.middleware.SessionMiddleware'
        ]
        
        # CORS middleware (must be early in middleware stack)
        if ('frontend' in full_context or 'react' in full_context or 'vue' in full_context or 
            'angular' in full_context or 'cors' in full_context or 'spa' in full_context):
            middleware.append('corsheaders.middleware.CorsMiddleware')
            
        middleware.extend([
            'django.middleware.common.CommonMiddleware',
            'django.middleware.csrf.CsrfViewMiddleware', 
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'django.contrib.messages.middleware.MessageMiddleware',
            'django.middleware.clickjacking.XFrameOptionsMiddleware'
        ])
        
        # Debug toolbar middleware (development only)
        middleware.append('debug_toolbar.middleware.DebugToolbarMiddleware')
        
        # Database configuration - Always use SQLite for generated projects
        # SQLite is ideal for development, testing, and small-to-medium projects
        db_config = """'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }"""
        
        # Generate additional configuration sections
        additional_configs = []
        
        # WebSocket/Channels configuration - Only for explicit WebSocket apps
        if ('websocket' in full_context or 'real-time chat' in full_context or 
            special_features.get('websockets')):
            additional_configs.append("""
# Channels/WebSocket Configuration
ASGI_APPLICATION = '{project_name}.asgi.application'
CHANNEL_LAYERS = {{
    'default': {{
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {{
            'hosts': [('127.0.0.1', 6379)],
        }},
    }},
}}""".format(project_name=project_name))

        # Celery configuration - Only for explicit background task requirements
        if ('celery' in full_context or 'background task' in full_context or 
            special_features.get('celery_tasks')):
            additional_configs.append("""
# Celery Configuration
CELERY_BROKER_URL = os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/0')
CELERY_RESULT_BACKEND = os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'""")

        # Debug toolbar configuration
        additional_configs.append("""
# Debug Toolbar Configuration (Development)
if DEBUG:
    INTERNAL_IPS = ['127.0.0.1', 'localhost']""")

        # Generate the settings file
        settings_template = f'''import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-development-key-{project_name}')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1,0.0.0.0').split(',')

# Application definition
INSTALLED_APPS = [
    {self._format_python_list(installed_apps)}
]

MIDDLEWARE = [
    {self._format_python_list(middleware)}
]

ROOT_URLCONF = '{project_name}.urls'

TEMPLATES = [
    {{
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {{
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        }},
    }},
]

WSGI_APPLICATION = '{project_name}.wsgi.application'

# Database
# Using SQLite for development and small-to-medium applications
# SQLite is file-based, requires no setup, and is perfect for getting started
# For production with high traffic, consider PostgreSQL or MySQL
DATABASES = {{
    {db_config}
}}

# Caching - Use local memory cache for simplicity
CACHES = {{
    'default': {{
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }}
}}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {{'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'}},
    {{'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'}},
    {{'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'}},
    {{'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'}},
]

{self._get_rest_framework_config(full_context) if ('api' in full_context or has_api) else ""}

{self._get_cors_config(full_context) if ('frontend' in full_context) else ""}

{chr(10).join(additional_configs)}

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Security settings
SECURE_SSL_REDIRECT = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# Logging
LOGGING = {{
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {{
        'file': {{
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
        }},
        'console': {{
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        }},
    }},
    'loggers': {{
        'django': {{
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        }},
    }},
}}
'''
        
        return settings_template
    
    def _format_python_list(self, items: list) -> str:
        """Format a Python list with proper indentation"""
        formatted_items = [f"    '{item}'," for item in items]
        return '\n'.join(formatted_items)
    
    def _get_rest_framework_config(self, full_context: str) -> str:
        """Get REST Framework configuration based on detected features"""
        config = '''
# REST Framework configuration
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',  # Start with open permissions for development
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication','''
        
        # Add JWT if authentication features detected
        if 'jwt' in full_context or 'token' in full_context or 'auth' in full_context:
            config += '''
        'rest_framework_simplejwt.authentication.JWTAuthentication','''
        
        config += '''
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}'''

        # Add JWT settings if needed
        if 'jwt' in full_context or 'token' in full_context:
            config += '''

# JWT Configuration
from datetime import timedelta
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': True,
}'''
        
        return config
    
    def _get_cors_config(self, full_context: str) -> str:
        """Get CORS configuration based on frontend needs"""
        config = '''
# CORS configuration
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",  # React dev server
    "http://127.0.0.1:3000",
    "http://localhost:8080",  # Vue dev server
    "http://127.0.0.1:8080",
]
CORS_ALLOW_CREDENTIALS = True'''

        # Add specific origins based on detected frontend frameworks
        if 'next' in full_context:
            config += '''
CORS_ALLOWED_ORIGINS += ["http://localhost:3001"]  # Next.js dev server'''
        
        return config
    
    def _generate_dynamic_requirements(self, project_plan: Dict) -> str:
        """Generate comprehensive requirements.txt based on project features and needs"""
        
        # Base Django requirements
        requirements = [
            'Django==5.0.7',
            'python-dotenv==1.0.1',
        ]
        
        # Get comprehensive project context
        user_prompt = project_plan.get('user_prompt', '').lower()
        description = project_plan.get('description', '').lower()
        features = str(project_plan.get('features', {})).lower()
        apps_data = str(project_plan.get('apps', [])).lower()
        tech_stack = project_plan.get('tech_stack', {})
        project_type = project_plan.get('project_type', 'web_app')
        special_features = project_plan.get('special_features', {})
        
        # Combine all text for comprehensive analysis
        full_context = f"{user_prompt} {description} {features} {apps_data}".lower()
        
        # Project type specific requirements
        type_requirements = self._get_requirements_for_project_type(project_type)
        requirements.extend(type_requirements)
        
        # API and REST Framework
        has_api = any(app.get('api_endpoints') for app in project_plan['apps'])
        if has_api or 'api' in full_context or 'rest' in full_context or 'endpoint' in full_context:
            requirements.extend([
                'djangorestframework==3.15.2',
                'djangorestframework-simplejwt==5.3.0',  # JWT authentication
                'django-filter==23.4',                   # API filtering
                'drf-spectacular==0.27.0',               # OpenAPI schema generation
                'django-rest-swagger==2.2.0',           # API documentation
            ])
        
        # CORS for frontend integration
        if ('frontend' in full_context or 'react' in full_context or 'vue' in full_context or 
            'angular' in full_context or 'cors' in full_context or 'spa' in full_context):
            requirements.append('django-cors-headers==4.3.1')
        
        # Database packages - SQLite only (no additional packages needed)
        # SQLite is included with Python, no extra dependencies required
        # This keeps projects lightweight and easy to deploy
        
        # Image and media processing
        if ('image' in full_context or 'photo' in full_context or 'upload' in full_context or
            'media' in full_context or 'file' in full_context or 'avatar' in full_context):
            requirements.extend([
                'Pillow==10.1.0',
                'django-imagekit==5.0.0',               # Image processing utilities
                'python-magic==0.4.27',                 # File type detection
            ])
        
        # Real-time features (WebSockets, Chat) - Only for explicitly real-time apps
        if ('websocket' in full_context or 'real-time chat' in full_context or 
            special_features.get('websockets')):
            requirements.extend([
                'channels==4.0.0',
                'channels-redis==4.1.0',               # Redis backend for channels
                'daphne==4.0.0',                       # ASGI server
                'redis==5.0.1',                        # Required for channels-redis
            ])
        elif ('chat' in full_context or 'notification' in full_context):
            # Simple notifications without WebSockets
            requirements.append('django-notifications-hq==1.8.3')
        
        # Caching - Only add Redis if explicitly requested
        if 'redis' in full_context and ('cache' in full_context or 'redis cache' in full_context):
            requirements.extend([
                'django-redis==5.4.0',
                'hiredis==2.2.3',                       # Faster Redis client
            ])
        
        # Authentication systems
        if 'auth' in full_context:
            if ('social' in full_context or 'google' in full_context or 'github' in full_context or
                'facebook' in full_context or 'oauth' in full_context):
                requirements.extend([
                    'django-allauth==0.57.0',
                    'PyJWT==2.8.0',                     # JWT handling
                ])
        
        # Payment processing
        if (special_features.get('payments') or 'payment' in full_context or 'stripe' in full_context or 
            'billing' in full_context or 'subscription' in full_context or 'checkout' in full_context):
            requirements.extend([
                'stripe==7.8.0',
                'requests==2.31.0',
                'django-payments==2.0.0',               # Payment gateway abstraction
            ])
        
        # Email functionality
        if (special_features.get('email_sending') or 'email' in full_context or 'mail' in full_context or 
            'notification' in full_context):
            requirements.extend([
                'django-anymail==10.2',
                'celery==5.3.4',                        # For async email sending
                'django-email-verification==0.3.4',     # Email verification
            ])
        
        # Background tasks - Only add if explicitly requested for complex tasks
        if ('celery' in full_context or 'background task' in full_context or 
            'queue' in full_context or special_features.get('celery_tasks')):
            requirements.extend([
                'celery==5.3.4',
                'redis==5.0.1',                         # Message broker for Celery
                'django-celery-beat==2.5.0',            # Periodic tasks
                'django-celery-results==2.5.0',         # Task results backend
                'flower==2.0.1',                        # Celery monitoring
            ])
        
        # Search functionality
        if (special_features.get('search') or 'search' in full_context or 'elasticsearch' in full_context or 
            'solr' in full_context):
            if 'elasticsearch' in full_context:
                requirements.extend([
                    'django-elasticsearch-dsl==8.0',
                    'elasticsearch==8.11.0',
                ])
            else:
                requirements.extend([
                    'django-haystack==3.2.1',           # Search abstraction
                    'whoosh==2.7.4',                    # Pure Python search engine
                ])
        
        # Forms and UI enhancements
        if ('form' in full_context or 'crispy' in full_context or 'bootstrap' in full_context):
            framework = project_plan.get('ui_design', {}).get('framework', 'bootstrap')
            requirements.extend([
                'django-crispy-forms==2.1',
                f'crispy-{framework.lower()}==0.7' if framework.lower() in ['bootstrap5', 'tailwind'] else 'crispy-bootstrap5==0.7',
                'django-widget-tweaks==1.5.0',         # Form widget customization
            ])
        
        # Content Management
        if ('cms' in full_context or 'content' in full_context or 'blog' in full_context):
            requirements.extend([
                'django-ckeditor==6.7.0',               # Rich text editor
                'django-taggit==5.0.1',                 # Tagging system
                'django-mptt==0.15.0',                  # Tree structures
            ])
        
        # Development and debugging tools
        requirements.extend([
            'django-extensions==3.2.3',        # Management command extensions
            'django-debug-toolbar==4.2.0',     # Debug toolbar
            'django-silk==5.1.0',              # Profiling and monitoring
        ])
        
        # Testing framework
        if 'test' in full_context or 'pytest' in full_context:
            requirements.extend([
                'pytest==7.4.3',
                'pytest-django==4.7.0',
                'factory-boy==3.3.0',                   # Test data factories
                'pytest-cov==4.1.0',                    # Coverage reporting
                'model-bakery==1.17.0',                 # Test data generation
            ])
        
        # Cloud storage and CDN
        if ('aws' in full_context or 's3' in full_context or 'cloud' in full_context or
            'storage' in full_context):
            requirements.extend([
                'boto3==1.34.0',
                'django-storages==1.14.2',
                'django-compressor==4.4',               # Asset compression
            ])
        
        # External API integration
        if ('api' in full_context or 'external' in full_context or 'integration' in full_context or
            'webhook' in full_context):
            requirements.extend([
                'requests==2.31.0',
                'httpx==0.25.2',                        # Modern async HTTP client
                'django-webhook==1.3.0',                # Webhook handling
            ])
        
        # Monitoring and logging
        if project_plan.get('complexity_level') in ['complex', 'enterprise']:
            requirements.extend([
                'sentry-sdk==1.39.1',                   # Error tracking
                'django-structlog==7.0.0',              # Structured logging
                'django-health-check==3.17.0',          # Health checks
            ])
        
        # Security enhancements
        if ('secure' in full_context or 'ssl' in full_context or 
            project_plan.get('complexity_level') in ['complex', 'enterprise']):
            requirements.extend([
                'django-security==0.17.0',
                'django-csp==3.7',                      # Content Security Policy
                'django-ratelimit==4.1.0',              # Rate limiting
            ])
        
        # Data processing and analytics
        if ('data' in full_context or 'analytics' in full_context or 'report' in full_context):
            requirements.extend([
                'pandas==2.1.4',
                'django-import-export==3.3.4',          # Data import/export
                'openpyxl==3.1.2',                      # Excel support
                'reportlab==4.0.8',                     # PDF generation
            ])
        
        # Internationalization
        if ('i18n' in full_context or 'international' in full_context or 'language' in full_context):
            requirements.extend([
                'django-modeltranslation==0.18.11',     # Model translation
                'django-rosetta==0.9.9',                # Translation interface
            ])
        
        # Performance optimization
        if project_plan.get('complexity_level') in ['complex', 'enterprise']:
            requirements.extend([
                'django-cachalot==2.6.1',               # ORM caching
                'django-compression-middleware==0.4.1', # Response compression
            ])
        
        # Production deployment packages
        requirements.extend([
            'gunicorn==21.2.0',                         # WSGI server
            'whitenoise==6.5.0',                        # Static file serving
            'python-decouple==3.8',                     # Settings management
        ])
        
        # Remove duplicates while preserving order
        unique_requirements = []
        seen = set()
        for req in requirements:
            if req not in seen:
                unique_requirements.append(req)
                seen.add(req)
        
        return '\n'.join(unique_requirements)
    
    def _get_requirements_for_project_type(self, project_type: str) -> List[str]:
        """Get specific requirements based on project type."""
        type_requirements = {
            'blog': [
                'django-ckeditor==6.7.0',           # Rich text editor
                'django-taggit==5.0.1',             # Tagging system
                'django-mptt==0.15.0',              # Comment trees
                'feedparser==6.0.10',               # RSS feeds
            ],
            'ecommerce': [
                'django-oscar==3.2.2',              # E-commerce framework
                'stripe==7.8.0',                    # Payment processing
                'Pillow==10.1.0',                   # Product images
                'django-storages==1.14.2',          # File storage
                'reportlab==4.0.8',                 # Invoice generation
            ],
            'social': [
                'django-notifications-hq==1.8.3',  # Notifications
                'Pillow==10.1.0',                   # Profile images
                'django-friendship==1.9.6',         # Friend relationships
            ],
            'dashboard': [
                'django-chartjs==2.3.0',            # Charts and graphs
                'pandas==2.1.4',                    # Data processing
                'django-import-export==3.3.4',      # Data import/export
            ],
            'api': [
                'djangorestframework==3.15.2',      # REST API
                'drf-spectacular==0.27.0',          # OpenAPI docs
                'django-filter==23.4',              # API filtering
                'django-rest-auth==0.9.5',          # API authentication
                'django-cors-headers==4.3.1',       # CORS handling
            ],
            'portfolio': [
                'Pillow==10.1.0',                   # Image processing
                'django-imagekit==5.0.0',           # Image optimization
                'django-ckeditor==6.7.0',           # Rich content
                'django-compressor==4.4',           # Asset optimization
            ],
            'education': [
                'django-ckeditor==6.7.0',           # Course content
                'Pillow==10.1.0',                   # Media files
                'django-mptt==0.15.0',              # Course structure
                'reportlab==4.0.8',                 # Certificate generation
            ],
            'business': [
                'django-import-export==3.3.4',      # Data management
                'openpyxl==3.1.2',                  # Excel support
                'reportlab==4.0.8',                 # Report generation
                'django-crispy-forms==2.1',         # Form styling
            ]
        }
        
        return type_requirements.get(project_type, [])
    
    def _generate_deployment_files(self, project_plan: Dict, project_path: Path) -> List[Dict]:
        """Generate deployment-related files."""
        
        files = []
        
        if project_plan.get('deployment', {}).get('dockerfile'):
            dockerfile_prompt = f"""
Create a production-ready Dockerfile for Django project '{project_plan['project_name']}'.

Database: {project_plan['tech_stack']['database']}
Special requirements: {project_plan.get('special_features', {})}

IMPORTANT: Include robust pip installation with retry logic for network issues:
- Use --retries flag with increasing retry counts
- Include --resume-retries option for interrupted downloads
- Add fallback with --no-cache-dir if retries fail
- Add final fallback installing packages individually
- Use appropriate timeouts (300-600 seconds)

Example pip install command with retries:
RUN pip install --retries 5 --timeout 300 -r requirements.txt || \\
    (pip install --retries 10 --timeout 600 --resume-retries -r requirements.txt) || \\
    (pip install --no-cache-dir --retries 5 --timeout 300 -r requirements.txt) || \\
    (cat requirements.txt | xargs -n 1 pip install --retries 3 --timeout 120)

Include multi-stage build, security best practices, and optimization.
Return ONLY the Dockerfile content.
"""
            
            dockerfile_content = self._generate_code_with_ai(dockerfile_prompt)
            files.append(self._save_file(project_path / 'Dockerfile', dockerfile_content))
        
        if project_plan.get('deployment', {}).get('docker_compose'):
            compose_prompt = f"""
Create docker-compose.yml for Django project '{project_plan['project_name']}'.

Services needed:
- Web application
- {project_plan['tech_stack']['database']} database
- Redis if caching is enabled: {project_plan.get('special_features', {}).get('caching')}
- Celery if enabled: {project_plan.get('special_features', {}).get('celery_tasks')}

Return ONLY the YAML content.
"""
            
            compose_content = self._generate_code_with_ai(compose_prompt)
            files.append(self._save_file(project_path / 'docker-compose.yml', compose_content))
        
        return files
    
    def _generate_test_files(self, project_plan: Dict, project_path: Path) -> List[Dict]:
        """Generate test configuration and sample tests."""
        
        files = []
        
        if project_plan.get('testing', {}).get('framework') == 'pytest':
            pytest_ini = """[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = "{}.settings"
python_files = ["test_*.py", "*_test.py"]
addopts = "-v --tb=short --strict-markers --cov --cov-report=html"
""".format(project_plan['project_name'])
            
            files.append(self._save_file(project_path / 'pytest.ini', pytest_ini))
        
        return files
    def _generate_documentation(self, project_plan: Dict, project_path: Path, user_prompt: str) -> List[Dict]:
       """Generate comprehensive project documentation."""
       
       files = []
       
       # Generate README.md
       readme_prompt = f"""
Create a comprehensive README.md for this Django project:

Project: {project_plan['project_name']}
Description: {project_plan['description']}
Original request: "{user_prompt}"
Features: {json.dumps(project_plan['features'])}
Tech Stack: {json.dumps(project_plan['tech_stack'])}
Setup Instructions: {json.dumps(project_plan['setup_instructions'])}

Include:
- Project overview and features
- Screenshots/demo section (placeholders)
- Prerequisites
- Installation instructions
- Usage guide
- API documentation (if applicable)
- Contributing guidelines
- License information
- Contact/support section

Make it professional, clear, and helpful.
Return ONLY the Markdown content.
"""
       
       readme_content = self._generate_code_with_ai(readme_prompt)
       files.append(self._save_file(project_path / 'README.md', readme_content))
       
       # Generate API documentation if needed
       if any(app.get('api_endpoints') for app in project_plan['apps']):
           api_doc_prompt = f"""
Create API documentation for this Django project:

Project: {project_plan['project_name']}
API Endpoints: {json.dumps([endpoint for app in project_plan['apps'] for endpoint in app.get('api_endpoints', [])])}
Authentication: {project_plan.get('security', {}).get('api_authentication', 'token')}

Create comprehensive API documentation with:
- Overview
- Authentication guide
- Endpoint details (URL, methods, parameters, responses)
- Example requests and responses
- Error codes
- Rate limiting info

Return ONLY the Markdown content.
"""
           
           api_doc_content = self._generate_code_with_ai(api_doc_prompt)
           files.append(self._save_file(project_path / 'API_DOCUMENTATION.md', api_doc_content))
       
       return files
   
    def _generate_code_with_ai(self, prompt: str, callback=None, max_retries: int = 3) -> str:
        """
        Generate code using Claude AI with streaming support and retry logic.
        This is the core method that makes everything dynamic.
        """
        
        last_error = None
        
        for attempt in range(max_retries):
            try:
                logger.debug(f"AI generation attempt {attempt + 1}/{max_retries}")
                full_content = ""
                
                # Validate prompt
                if not prompt or not prompt.strip():
                    raise ValueError("Empty or invalid prompt provided")
                
                with self.claude_service.client.messages.stream(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=4000,
                    temperature=0.2,
                    messages=[
                        {
                            "role": "user",
                            "content": prompt + "\n\nIMPORTANT: Return ONLY the requested code/content, no explanations or markdown blocks."
                        }
                    ]
                ) as stream:
                    for text in stream.text_stream:
                        full_content += text
                        if callback:
                            callback(text)
                
                # Validate response
                if not full_content or len(full_content.strip()) < 10:
                    raise ValueError("AI response was too short or empty")
                
                # Clean up any markdown code blocks if they exist
                content = self._clean_code_response(full_content)
                
                if not content or len(content.strip()) < 5:
                    raise ValueError("Cleaned content is empty or too short")
                
                logger.debug(f"AI generation successful on attempt {attempt + 1}")
                return content
                
            except Exception as e:
                last_error = e
                self._update_stats('retries_used')
                self._track_error(
                    'ai_generation_attempt_failed',
                    str(e),
                    {
                        'attempt': attempt + 1,
                        'max_retries': max_retries,
                        'prompt_length': len(prompt) if prompt else 0
                    }
                )
                logger.warning(f"AI generation attempt {attempt + 1} failed: {e}")
                
                # Wait before retry (exponential backoff)
                if attempt < max_retries - 1:
                    import time
                    wait_time = 2 ** attempt  # 1s, 2s, 4s
                    logger.debug(f"Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
        
        # All retries failed
        logger.error(f"AI generation failed after {max_retries} attempts. Last error: {last_error}")
        
        # Return intelligent fallback based on prompt content
        if 'models.py' in prompt.lower():
            return """# AI generation failed - please regenerate this models file
from django.db import models
from django.contrib.auth.models import User

# Add your models here
"""
        elif 'views.py' in prompt.lower():
            return """# AI generation failed - please regenerate this views file
from django.shortcuts import render
from django.http import HttpResponse

def home(request):
    return HttpResponse("Hello World!")
"""
        elif 'urls.py' in prompt.lower():
            return """# AI generation failed - please regenerate this urls file
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
]
"""
        else:
            return f"# AI generation failed after {max_retries} attempts\n# Last error: {last_error}\n# Please regenerate this file manually"
    
    def _generate_code_with_ai_streaming(self, prompt: str, callback_func=None, max_retries: int = 2) -> str:
        """
        Generate code with real-time streaming updates for the frontend.
        Uses fewer retries for streaming to maintain responsiveness.
        """
        last_error = None
        
        for attempt in range(max_retries):
            try:
                logger.debug(f"AI streaming generation attempt {attempt + 1}/{max_retries}")
                full_content = ""
                
                # Validate prompt
                if not prompt or not prompt.strip():
                    raise ValueError("Empty or invalid prompt provided")
                
                # Add callback for real-time updates
                def stream_callback(text_chunk):
                    nonlocal full_content
                    full_content += text_chunk
                    if callback_func:
                        try:
                            callback_func({
                                'type': 'content_chunk',
                                'chunk': text_chunk,
                                'total_length': len(full_content),
                                'attempt': attempt + 1
                            })
                        except Exception as cb_error:
                            logger.warning(f"Callback error: {cb_error}")
                
                with self.claude_service.client.messages.stream(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=4000,
                    temperature=0.2,
                    messages=[
                        {
                            "role": "user",
                            "content": prompt + "\n\nIMPORTANT: Return ONLY the requested code/content, no explanations or markdown blocks."
                        }
                    ]
                ) as stream:
                    for text in stream.text_stream:
                        stream_callback(text)
                
                # Validate response
                if not full_content or len(full_content.strip()) < 10:
                    raise ValueError("AI response was too short or empty")
                
                # Clean up any markdown code blocks if they exist
                content = self._clean_code_response(full_content)
                
                if not content or len(content.strip()) < 5:
                    raise ValueError("Cleaned content is empty or too short")
                
                logger.debug(f"AI streaming generation successful on attempt {attempt + 1}")
                return content
                
            except Exception as e:
                last_error = e
                logger.warning(f"AI streaming generation attempt {attempt + 1} failed: {e}")
                
                # Notify callback of retry
                if callback_func and attempt < max_retries - 1:
                    try:
                        callback_func({
                            'type': 'retry',
                            'attempt': attempt + 1,
                            'max_retries': max_retries,
                            'error': str(e)
                        })
                    except Exception as cb_error:
                        logger.warning(f"Retry callback error: {cb_error}")
                
                # Wait before retry (shorter for streaming)
                if attempt < max_retries - 1:
                    import time
                    wait_time = 1 + attempt  # 1s, 2s
                    logger.debug(f"Waiting {wait_time}s before streaming retry...")
                    time.sleep(wait_time)
        
        # All retries failed
        logger.error(f"AI streaming generation failed after {max_retries} attempts. Last error: {last_error}")
        
        # Notify callback of final failure
        if callback_func:
            try:
                callback_func({
                    'type': 'error',
                    'error': str(last_error),
                    'attempts': max_retries
                })
            except Exception as cb_error:
                logger.warning(f"Error callback error: {cb_error}")
        
        # Return same intelligent fallback as non-streaming version
        return self._generate_code_with_ai(prompt, max_retries=1)  # Single retry for fallback
    
    def _clean_code_response(self, content: str) -> str:
        """Clean up AI response to get pure code."""
        
        # Remove markdown code blocks
        content = re.sub(r'^```[a-zA-Z]*\n', '', content, flags=re.MULTILINE)
        content = re.sub(r'\n```$', '', content, flags=re.MULTILINE)
        content = re.sub(r'^```\n', '', content, flags=re.MULTILINE)
        
        # Remove any explanation text that might appear before code
        lines = content.split('\n')
        code_started = False
        clean_lines = []
        
        for line in lines:
            # Detect code start patterns
            if not code_started and any(pattern in line for pattern in ['import ', 'from ', '<!', '<?', 'class ', 'def ', '/*', '#!']):
                code_started = True
            
            if code_started:
                clean_lines.append(line)
        
        return '\n'.join(clean_lines) if clean_lines else content
    
    def _save_file(self, file_path: Path, content: str, component_type: str = None, 
                  progress_callback=None) -> Dict:
        """Save content to file with comprehensive validation and error tracking."""
        
        try:
            self._update_stats('files_attempted')
            
            # Use the safe validation method
            result = self._validate_and_save_file(
                str(file_path), 
                content, 
                component_type=component_type,
                progress_callback=progress_callback
            )
            
            if result['success']:
                self._update_stats('files_succeeded')
                return {
                    'success': True,
                    'path': str(file_path),
                    'name': file_path.name,
                    'size': len(content),
                    'validation_results': result['validation_results'],
                    'warnings': result['warnings'],
                    'errors': result['errors']
                }
            else:
                self._update_stats('files_failed')
                return {
                    'success': False,
                    'error': f"Validation failed for {file_path.name}",
                    'validation_results': result['validation_results'],
                    'warnings': result['warnings'], 
                    'errors': result['errors']
                }
                
        except Exception as e:
            self._update_stats('files_failed')
            
            # Validate inputs
            if not file_path:
                raise ValueError("File path cannot be empty")
            
            if content is None:
                raise ValueError("Content cannot be None")
            
            # Create parent directories
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Validate content before writing
            if len(content.strip()) == 0:
                logger.warning(f"Writing empty content to {file_path}")
            
            # Write file with error handling
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Verify file was written correctly
            if not file_path.exists():
                raise FileNotFoundError(f"File was not created: {file_path}")
            
            file_size = file_path.stat().st_size
            if file_size == 0 and len(content) > 0:
                raise IOError(f"File was created but is empty: {file_path}")
            
            self._update_stats('files_succeeded')
            logger.debug(f"Successfully saved file: {file_path} ({file_size} bytes)")
            
            return {
                'path': str(file_path),
                'size': len(content),
                'file_size': file_size,
                'type': file_path.suffix.lstrip('.') if file_path.suffix else 'txt',
                'created': datetime.now().isoformat()
            }
            
        except Exception as e:
            self._update_stats('files_failed')
            self._track_error(
                'file_save_error',
                str(e),
                {
                    'file_path': str(file_path),
                    'content_length': len(content) if content else 0,
                    'file_type': file_path.suffix if file_path else 'unknown'
                }
            )
            
            # Re-raise the exception after tracking
            raise Exception(f"Failed to save file {file_path}: {str(e)}")
    
    def _generate_standard_django_file(self, file_type: str, project_name: str) -> str:
        """Generate standard Django files like wsgi.py and asgi.py."""
        
        if file_type == 'wsgi':
            return f"""\"\"\"
WSGI config for {project_name} project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/wsgi/
\"\"\"

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', '{project_name}.settings')

application = get_wsgi_application()
    """
        
        elif file_type == 'asgi':
            return f"""\"\"\"
ASGI config for {project_name} project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/asgi/
\"\"\"

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', '{project_name}.settings')

application = get_asgi_application()
    """
    
    def _generate_manage_py(self, project_name: str) -> str:
        """Generate manage.py file."""
        
        return f"""#!/usr/bin/env python
\"\"\"Django's command-line utility for administrative tasks.\"\"\"
import os
import sys


def main():
    \"\"\"Run administrative tasks.\"\"\"
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', '{project_name}.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
    """
    
    def _setup_project_environment(self, project_path: Path, project_plan: Dict) -> Dict:
        """Skip virtual environment setup - handled externally."""
        return {'success': True}

    def _initialize_django_project(self, project_path: Path, project_plan: Dict) -> Dict:
        """Initialize Django project structure."""
        
        try:
            project_name = project_plan['project_name']
            
            # Create project directory structure
            project_dir = project_path / project_name
            project_dir.mkdir(exist_ok=True)
            
            # The files are already generated, so we just need to ensure the structure is correct
            
            # Create media and staticfiles directories
            (project_path / 'media').mkdir(exist_ok=True)
            (project_path / 'staticfiles').mkdir(exist_ok=True)
            
            return {'success': True}
            
        except Exception as e:
            logger.error(f"Error initializing Django project: {e}")
            return {'success': False, 'error': str(e)}
    
   
    def _parse_json_response(self, content: str) -> Optional[Dict]:
        """Parse JSON response from AI, handling various formats."""
        
        # Try direct parsing
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass
        
        # Try to extract JSON from markdown
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', content)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        
        # Try to find JSON object in content
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        
        logger.error(f"Failed to parse JSON from AI response: {content[:500]}...")
        return None
    
    def generate_app_component(self, project_id: str, component_type: str, component_config: Dict) -> Dict:
        """
        Generate a specific component (model, view, template, etc.) for an existing project.
        This allows adding features to an already generated project.
        """
        
        project_path = self.base_dir / project_id
        
        if not project_path.exists():
            return {
                'success': False,
                'error': f'Project {project_id} does not exist'
            }
        
        try:
            if component_type == 'model':
                return self._add_model_to_app(project_path, component_config)
            elif component_type == 'view':
                return self._add_view_to_app(project_path, component_config)
            elif component_type == 'api_endpoint':
                return self._add_api_endpoint(project_path, component_config)
            elif component_type == 'template':
                return self._add_template(project_path, component_config)
            else:
                return {
                    'success': False,
                    'error': f'Unknown component type: {component_type}'
                }
                
        except Exception as e:
            logger.error(f"Error generating component: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _add_model_to_app(self, project_path: Path, config: Dict) -> Dict:
        """Add a new model to an existing app."""
        
        app_name = config['app_name']
        model_name = config['model_name']
        fields = config['fields']
        
        # Read existing models.py
        models_path = project_path / app_name / 'models.py'
        if not models_path.exists():
            return {
                'success': False,
                'error': f'App {app_name} does not exist'
            }
        
        existing_content = models_path.read_text()
        
        # Generate new model code
        model_prompt = f"""
    Add a new Django model to an existing models.py file.

    Model name: {model_name}
    Fields: {json.dumps(fields)}

    Generate ONLY the model class code that should be appended to the file.
    Include proper field types, Meta class, __str__ method, and any necessary methods.
    Do NOT include imports or other models.

    Return ONLY the Python code for this model.
    """
        
        new_model_code = self._generate_code_with_ai(model_prompt)
        
        # Append to existing file
        updated_content = existing_content.rstrip() + '\n\n\n' + new_model_code + '\n'
        
        with open(models_path, 'w') as f:
            f.write(updated_content)
        
        # Update admin.py
        self._update_admin_for_model(project_path, app_name, model_name)
        
        return {
            'success': True,
            'message': f'Model {model_name} added to {app_name}',
            'next_steps': [
                'Run: python manage.py makemigrations',
                'Run: python manage.py migrate',
                f'Model {model_name} is now available in your app'
            ]
        }
    
    def _add_view_to_app(self, project_path: Path, config: Dict) -> Dict:
        """Add a new view to an existing app."""
        
        app_name = config['app_name']
        view_name = config['view_name']
        view_type = config.get('view_type', 'function')  # function or class
        purpose = config['purpose']
        
        # Generate view code
        view_prompt = f"""
    Create a Django view:

    View name: {view_name}
    Type: {view_type}-based view
    Purpose: {purpose}
    App context: {app_name}

    Generate a complete, working view with:
    - Proper imports (assume common imports are already present)
    - Error handling
    - Authentication if needed
    - Proper response

    Return ONLY the Python code for this view.
    """
        
        view_code = self._generate_code_with_ai(view_prompt)
        
        # Add to views.py
        views_path = project_path / app_name / 'views.py'
        existing_content = views_path.read_text()
        updated_content = existing_content.rstrip() + '\n\n\n' + view_code + '\n'
        
        with open(views_path, 'w') as f:
            f.write(updated_content)
        
        # Generate URL pattern
        url_pattern = self._generate_url_pattern(view_name, view_type)
        
        return {
            'success': True,
            'message': f'View {view_name} added to {app_name}',
            'url_pattern': url_pattern,
            'next_steps': [
                f'Add this to your urls.py: {url_pattern}',
                'Create corresponding template if needed'
            ]
        }
    
    def _add_api_endpoint(self, project_path: Path, config: Dict) -> Dict:
        """Add a new API endpoint to an existing app."""
        
        endpoint_prompt = f"""
    Create a Django REST Framework API endpoint:

    Endpoint: {config['endpoint']}
    Methods: {config['methods']}
    Purpose: {config['purpose']}
    Model: {config.get('model', 'N/A')}

    Generate:
    1. Serializer (if needed)
    2. View/ViewSet
    3. URL pattern

    Return the code in JSON format:
    {{
    "serializer": "serializer code here",
    "view": "view code here", 
    "url": "url pattern here"
    }}
    """
        
        response = self._generate_code_with_ai(endpoint_prompt)
        endpoint_code = self._parse_json_response(response)
        
        if not endpoint_code:
            return {
                'success': False,
                'error': 'Failed to generate API endpoint code'
            }
        
        # Add serializer, view, and URL
        # ... (implementation details)
        
        return {
            'success': True,
            'message': f'API endpoint {config["endpoint"]} added',
            'endpoint': config['endpoint'],
            'methods': config['methods']
        }
    
    def _add_template(self, project_path: Path, config: Dict) -> Dict:
        """Add a new template to an existing app."""
        
        template_prompt = f"""
    Create a Django template:

    Template name: {config['template_name']}
    Purpose: {config['purpose']}
    App: {config['app_name']}
    Extends: base.html
    Context variables: {config.get('context_vars', [])}

    Create a complete, beautiful template that:
    - Serves its purpose perfectly
    - Looks professional and modern
    - Handles any forms or data display needed
    - Is responsive

    Return ONLY the HTML code.
    """
        
        template_content = self._generate_code_with_ai(template_prompt)
        
        # Save template
        template_path = (project_path / config['app_name'] / 'templates' / 
                        config['app_name'] / config['template_name'])
        template_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(template_path, 'w') as f:
            f.write(template_content)
        
        return {
            'success': True,
            'message': f'Template {config["template_name"]} added',
            'path': str(template_path)
        }
    
    def _update_admin_for_model(self, project_path: Path, app_name: str, model_name: str):
        """Update admin.py to register new model."""
        
        admin_path = project_path / app_name / 'admin.py'
        existing_content = admin_path.read_text()
        
        # Generate admin code for the model
        admin_code = f"""

    @admin.register({model_name})
    class {model_name}Admin(admin.ModelAdmin):
    list_display = ['__str__', 'created_at', 'updated_at']
    search_fields = ['name']
    list_filter = ['created_at']
    ordering = ['-created_at']
    """
        
        # Add import if not present
        if f'from .models import' in existing_content and model_name not in existing_content:
            existing_content = existing_content.replace(
                'from .models import',
                f'from .models import {model_name},'
            )
        
        # Append admin code
        updated_content = existing_content.rstrip() + admin_code + '\n'
        
        with open(admin_path, 'w') as f:
            f.write(updated_content)
    
    def _generate_url_pattern(self, view_name: str, view_type: str) -> str:
        """Generate URL pattern for a view."""
        
        if view_type == 'class':
            return f"path('{view_name.lower()}/', views.{view_name}.as_view(), name='{view_name.lower()}')"
        else:
            return f"path('{view_name.lower()}/', views.{view_name}, name='{view_name.lower()}')"

    def fix_incomplete_project(self, project_id: str) -> Dict:
        """
        Fix existing projects that have missing essential files (views.py, urls.py, etc.)
        This method scans a project and generates any missing essential Django files.
        """
        
        project_path = self.base_dir / project_id
        
        if not project_path.exists():
            return {
                'success': False,
                'error': f'Project {project_id} does not exist'
            }
        
        try:
            fixed_files = []
            
            # Find all Django apps in the project
            for item in project_path.iterdir():
                if item.is_dir() and not item.name.startswith('.') and item.name not in ['media', 'static', 'staticfiles', 'templates']:
                    # Check if it's a Django app by looking for apps.py or models.py
                    if (item / 'apps.py').exists() or (item / 'models.py').exists():
                        app_name = item.name
                        missing_files = self._check_missing_files(item)
                        
                        if missing_files:
                            logger.info(f"Fixing missing files for app {app_name}: {missing_files}")
                            
                            # Generate missing files
                            for file_type in missing_files:
                                file_result = self._generate_missing_file(
                                    item, 
                                    app_name, 
                                    file_type, 
                                    project_id
                                )
                                if file_result['success']:
                                    fixed_files.append(file_result)
            
            return {
                'success': True,
                'fixed_files': fixed_files,
                'message': f'Fixed {len(fixed_files)} missing files in project {project_id}'
            }
            
        except Exception as e:
            logger.error(f"Error fixing project {project_id}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _check_missing_files(self, app_path: Path) -> List[str]:
        """Check which essential Django files are missing from an app."""
        
        essential_files = ['models.py', 'views.py', 'urls.py', 'admin.py', 'apps.py', '__init__.py']
        missing_files = []
        
        for file_name in essential_files:
            if not (app_path / file_name).exists():
                missing_files.append(file_name)
        
        return missing_files
    
    def _generate_missing_file(self, app_path: Path, app_name: str, file_type: str, project_id: str) -> Dict:
        """Generate a specific missing file for an app."""
        
        try:
            if file_type == 'views.py':
                content = self._generate_fallback_views(app_name, app_path)
            elif file_type == 'urls.py':
                content = self._generate_fallback_urls(app_name, app_path)
            elif file_type == 'models.py':
                content = self._generate_fallback_models(app_name)
            elif file_type == 'admin.py':
                content = self._generate_fallback_admin(app_name, app_path)
            elif file_type == 'apps.py':
                content = self._generate_fallback_apps(app_name)
            elif file_type == '__init__.py':
                content = ''
            else:
                return {'success': False, 'error': f'Unknown file type: {file_type}'}
            
            file_path = app_path / file_type
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return {
                'success': True,
                'file_path': str(file_path),
                'file_type': file_type,
                'app_name': app_name
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to generate {file_type}: {str(e)}'
            }
    
    def _generate_fallback_views(self, app_name: str, app_path: Path) -> str:
        """Generate basic views.py when missing."""
        
        # Check if models exist to create appropriate views
        models_content = ""
        models_path = app_path / 'models.py'
        if models_path.exists():
            models_content = models_path.read_text()
        
        prompt = f"""
Create a basic views.py file for Django app '{app_name}'.

App path: {app_path}
Models file content (if exists): {models_content[:1000] if models_content else "No models found"}

Requirements:
- Import necessary Django modules (render, HttpResponse, etc.)
- Create a basic index view for the app
- If models exist, create basic CRUD views for the models
- Include proper error handling
- Use function-based views for simplicity
- Ensure all views return proper responses

Return ONLY the Python code.
"""
        
        return self._generate_code_with_ai(prompt)
    
    def _generate_fallback_urls(self, app_name: str, app_path: Path) -> str:
        """Generate basic urls.py when missing."""
        
        # Check if views exist to create appropriate URL patterns
        views_content = ""
        views_path = app_path / 'views.py'
        if views_path.exists():
            views_content = views_path.read_text()
        
        prompt = f"""
Create a basic urls.py file for Django app '{app_name}'.

Views file content (if exists): {views_content[:1000] if views_content else "No views found"}

Requirements:
- Import path from django.urls
- Import views from current app
- Set app_name = '{app_name}' for namespacing
- Create URL patterns for any views that exist
- If no views exist, create a basic empty urlpatterns list
- Follow Django URL naming conventions

Return ONLY the Python code.
"""
        
        return self._generate_code_with_ai(prompt)
    
    def _generate_fallback_models(self, app_name: str) -> str:
        """Generate basic models.py when missing."""
        
        return f"""from django.db import models

# Create your models here.
# Add your {app_name} models below

"""
    
    def _generate_fallback_admin(self, app_name: str, app_path: Path) -> str:
        """Generate basic admin.py when missing."""
        
        # Check if models exist
        models_content = ""
        models_path = app_path / 'models.py'
        if models_path.exists():
            models_content = models_path.read_text()
        
        if "class " in models_content and "models.Model" in models_content:
            prompt = f"""
Create admin.py for Django app '{app_name}'.

Models file content: {models_content}

Requirements:
- Import django.contrib.admin
- Import models from current app
- Register all models with basic admin classes
- Include proper admin configuration

Return ONLY the Python code.
"""
            return self._generate_code_with_ai(prompt)
        else:
            return f"""from django.contrib import admin

# Register your {app_name} models here.

"""
    
    def _generate_fallback_apps(self, app_name: str) -> str:
        """Generate basic apps.py when missing."""
        
        return f"""from django.apps import AppConfig


class {app_name.capitalize()}Config(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = '{app_name}'
    verbose_name = '{app_name.replace("_", " ").title()}'
"""

    def _create_minimal_config_files(self, project_path: Path) -> List[str]:
        """
        Create minimal configuration files when primary generation fails.
        This ensures the project has at least the basic files needed to run.
        """
        try:
            logger.info("Creating minimal configuration files as fallback...")
            files_created = []
            
            # Create minimal requirements.txt
            minimal_requirements = """Django>=4.2,<5.0
python-dotenv>=1.0.0
Pillow>=10.0.0
"""
            requirements_file = project_path / 'requirements.txt'
            self._save_file(requirements_file, minimal_requirements)
            files_created.append(str(requirements_file))
            
            # Create minimal .env file
            minimal_env = """DEBUG=True
SECRET_KEY=django-insecure-change-this-in-production
DATABASE_URL=sqlite:///db.sqlite3
ALLOWED_HOSTS=localhost,127.0.0.1
"""
            env_file = project_path / '.env'
            self._save_file(env_file, minimal_env)
            files_created.append(str(env_file))
            
            # Create minimal Dockerfile
            minimal_dockerfile = """FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
"""
            dockerfile = project_path / 'Dockerfile'
            self._save_file(dockerfile, minimal_dockerfile)
            files_created.append(str(dockerfile))
            
            # Create minimal .gitignore
            minimal_gitignore = """__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
pip-log.txt
pip-delete-this-directory.txt
.tox
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.log
.git
.mypy_cache
.pytest_cache
.hypothesis

.DS_Store
.vscode/
.idea/

db.sqlite3
.env
media/
staticfiles/
"""
            gitignore_file = project_path / '.gitignore'
            self._save_file(gitignore_file, minimal_gitignore)
            files_created.append(str(gitignore_file))
            
            logger.info(f"Created {len(files_created)} minimal configuration files")
            return files_created
            
        except Exception as e:
            logger.error(f"Failed to create minimal config files: {e}")
            return []

    def _initialize_validation_service(self, project_path: str):
        """Initialize validation service for the project"""
        try:
            self.validation_service = ValidationService(project_path)
            logger.info(f"Validation service initialized for project: {project_path}")
        except Exception as e:
            logger.warning(f"Failed to initialize validation service: {e}")
            self.validation_service = None
    
    def _validate_and_save_file(self, file_path: str, content: str, component_type: str = None, 
                               progress_callback=None) -> Dict:
        """Safely validate and save a generated file"""
        result = {
            'success': False,
            'validation_results': [],
            'file_path': file_path,
            'warnings': [],
            'errors': []
        }
        
        try:
            # Ensure validation service is available
            if not self.validation_service:
                self._initialize_validation_service(str(Path(file_path).parent))
            
            # Check generation sequence if component type is specified
            if component_type and self.validation_service:
                sequence_results = self.validation_service.validate_generation_sequence(component_type)
                result['validation_results'].extend(sequence_results)
                
                # Send sequence warnings to user
                for seq_result in sequence_results:
                    if seq_result.level == ValidationLevel.WARNING and progress_callback:
                        progress_callback({
                            'type': 'sequence_warning',
                            'message': f"⚠️ {seq_result.message}",
                            'suggestion': seq_result.suggestion
                        })
            
            # Validate template content before writing (if it looks like a template)
            if self.validation_service and ('{{' in content or '{%' in content):
                try:
                    # Extract template context from content patterns
                    template_context = self._extract_template_context(content)
                    rendered_content, template_results = self.validation_service.validate_template(
                        content, template_context
                    )
                    
                    result['validation_results'].extend(template_results)
                    
                    # Use rendered content if validation passed
                    template_errors = [r for r in template_results if r.level == ValidationLevel.ERROR]
                    if not template_errors and rendered_content:
                        content = rendered_content
                        if progress_callback:
                            progress_callback({
                                'type': 'template_validated',
                                'message': f"✅ Template validation passed for {Path(file_path).name}"
                            })
                    elif template_errors and progress_callback:
                        for error in template_errors:
                            progress_callback({
                                'type': 'template_error',
                                'message': f"🚨 Template error: {error.message}",
                                'suggestion': error.suggestion
                            })
                            
                except Exception as e:
                    logger.warning(f"Template validation failed for {file_path}: {e}")
                    if progress_callback:
                        progress_callback({
                            'type': 'template_warning',
                            'message': f"⚠️ Template validation skipped for {Path(file_path).name}: {str(e)}"
                        })
            
            # Create directory if it doesn't exist
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Write the file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            if progress_callback:
                progress_callback({
                    'type': 'file_created',
                    'file': file_path,
                    'message': f"📄 Created {Path(file_path).name}"
                })
            
            # Validate the written file
            if self.validation_service and file_path.endswith('.py'):
                file_results = self.validation_service.validate_file(
                    file_path, 
                    check_imports=True, 
                    run_linting=False  # Skip linting for now to avoid noise
                )
                result['validation_results'].extend(file_results)
                
                # Categorize results
                for val_result in file_results:
                    if val_result.level in [ValidationLevel.ERROR, ValidationLevel.CRITICAL]:
                        result['errors'].append(val_result)
                        self.generation_stats['validation_errors'] += 1
                        if progress_callback:
                            progress_callback({
                                'type': 'validation_error',
                                'message': f"❌ {val_result.message}",
                                'file': file_path,
                                'suggestion': val_result.suggestion
                            })
                    elif val_result.level == ValidationLevel.WARNING:
                        result['warnings'].append(val_result)
                        self.generation_stats['validation_warnings'] += 1
                        if progress_callback:
                            progress_callback({
                                'type': 'validation_warning', 
                                'message': f"⚠️ {val_result.message}",
                                'file': file_path,
                                'suggestion': val_result.suggestion
                            })
                    elif val_result.level == ValidationLevel.INFO and 'valid' in val_result.message.lower():
                        if progress_callback:
                            progress_callback({
                                'type': 'validation_success',
                                'message': f"✅ {Path(file_path).name} validation passed"
                            })
            
            result['success'] = True
            self.generation_stats['files_succeeded'] += 1
            
        except Exception as e:
            error_msg = f"Failed to write file {file_path}: {str(e)}"
            logger.error(error_msg)
            result['errors'].append(error_msg)
            self.generation_stats['files_failed'] += 1
            
            if progress_callback:
                progress_callback({
                    'type': 'file_error',
                    'message': f"❌ Failed to create {Path(file_path).name}: {str(e)}",
                    'suggestion': "Check file path and permissions"
                })
        
        self.generation_stats['files_attempted'] += 1
        return result
    
    def _extract_template_context(self, content: str) -> Dict:
        """Extract likely template context from content"""
        # Simple heuristic to provide common Django template variables
        context = {
            'app_name': 'main',
            'project_name': 'myproject', 
            'model_name': 'Item',
            'model_name_lower': 'item',
            'model_name_plural': 'items',
            'fields': ['name', 'description'],
            'user': {'username': 'testuser'}
        }
        
        # Look for specific patterns in the content
        import re
        
        # Extract app names
        app_matches = re.findall(r'app_name[\'"]?\s*=\s*[\'"](\w+)[\'"]', content)
        if app_matches:
            context['app_name'] = app_matches[0]
        
        # Extract model names
        model_matches = re.findall(r'class\s+(\w+)\s*\(.*Model', content)
        if model_matches:
            context['model_name'] = model_matches[0]
            context['model_name_lower'] = model_matches[0].lower()
            context['model_name_plural'] = model_matches[0].lower() + 's'
        
        return context
    
    def _run_django_validation(self, project_path: str, progress_callback=None) -> List:
        """Run comprehensive Django validation on the project"""
        validation_results = []
        
        if not self.validation_service:
            self._initialize_validation_service(project_path)
        
        if self.validation_service:
            try:
                if progress_callback:
                    progress_callback({
                        'type': 'validation_start',
                        'message': "🔍 Running Django project validation..."
                    })
                
                # Run Django checks
                django_results = self.validation_service.validate_project(run_django_check=True)
                validation_results.extend(django_results)
                
                # Report results
                errors = [r for r in django_results if r.level in [ValidationLevel.ERROR, ValidationLevel.CRITICAL]]
                warnings = [r for r in django_results if r.level == ValidationLevel.WARNING]
                
                if progress_callback:
                    if errors:
                        progress_callback({
                            'type': 'django_validation_errors',
                            'message': f"❌ Django validation found {len(errors)} errors",
                            'details': [e.message for e in errors[:3]]  # Show first 3
                        })
                    elif warnings:
                        progress_callback({
                            'type': 'django_validation_warnings', 
                            'message': f"⚠️ Django validation found {len(warnings)} warnings",
                            'details': [w.message for w in warnings[:3]]  # Show first 3
                        })
                    else:
                        progress_callback({
                            'type': 'django_validation_success',
                            'message': "✅ Django project validation passed"
                        })
                        
            except Exception as e:
                logger.warning(f"Django validation failed: {e}")
                if progress_callback:
                    progress_callback({
                        'type': 'validation_warning',
                        'message': f"⚠️ Django validation skipped: {str(e)}"
                    })
        
        return validation_results

    def generate_project_from_prompt_streaming(self, user_prompt: str, project_id: str, 
                                             progress_callback=None) -> Dict:
        """
        Generate complete Django project structure from user prompt with streaming updates.
        BOLT.NEW APPROACH: Start with official Django scaffolding, then stream modifications.
        """
        
        def send_status(message, status='generating', progress=None, **kwargs):
            """Helper to send status updates via callback"""
            if progress_callback:
                progress_callback({
                    'type': 'status',
                    'message': message,
                    'status': status,
                    'progress': progress,
                    **kwargs
                })
        
        def send_file_created(file_path, content_preview=None, progress=None):
            """Helper to send file creation updates with full content"""
            if progress_callback:
                progress_callback({
                    'type': 'file_created',
                    'file': file_path,
                    'content': content_preview,  # Send full content for real-time viewing
                    'content_preview': content_preview[:200] + '...' if content_preview and len(content_preview) > 200 else content_preview,
                    'progress': progress
                })
        
        def send_file_tree_update(tree_structure, progress=None):
            """Send file tree structure updates"""
            if progress_callback:
                progress_callback({
                    'type': 'file_tree_update',
                    'tree': tree_structure,
                    'progress': progress
                })
                
        def run_django_command(command, cwd, description):
            """Run Django command and stream output"""
            try:
                send_status(f'{description}...', 'scaffolding')
                result = subprocess.run(
                    command, 
                    cwd=cwd, 
                    capture_output=True, 
                    text=True, 
                    check=True
                )
                # Update file tree after command
                tree = self._build_file_tree(project_path)
                send_file_tree_update(tree)
                return True
            except subprocess.CalledProcessError as e:
                logger.error(f"Django command failed: {e}")
                send_status(f'Error: {description} failed: {e.stderr}', 'error')
                return False
        
        try:
            # Validate inputs
            if not user_prompt or not user_prompt.strip():
                return {
                    'success': False,
                    'error': 'User prompt cannot be empty'
                }
            
            send_status('Analyzing your requirements...', 'analyzing', 5)
            
            # Set up project directory
            project_path = Path(self.base_dir) / project_id
            project_path.mkdir(parents=True, exist_ok=True)
            
            send_status('Analyzing project requirements with AI...', 'analyzing', 10)
            
            # Get AI analysis to determine project structure
            analysis = self._create_complete_project_plan(user_prompt, project_id)
            if not analysis.get('success', True):
                return analysis
            
            project_plan = analysis.get('plan', {})
            project_name = project_plan.get('project_name', 'django_project')
            apps_to_create = project_plan.get('apps', [])
            
            send_status(f"Creating {project_name} Django project...", 'scaffolding', 15)
            
            # STEP 1: Create Django project scaffolding (Bolt.new approach)
            send_status('Running django-admin startproject...', 'scaffolding', 20)
            if not run_django_command(
                ['django-admin', 'startproject', project_name, '.'],
                cwd=project_path,
                description='Creating Django project scaffolding'
            ):
                return {'success': False, 'error': 'Failed to create Django project'}
            
            # Show initial project structure
            send_file_created('manage.py', self._read_file_content(project_path / 'manage.py'), 25)
            send_file_created(f'{project_name}/settings.py', 
                            self._read_file_content(project_path / project_name / 'settings.py'), 25)
            send_file_created(f'{project_name}/urls.py', 
                            self._read_file_content(project_path / project_name / 'urls.py'), 25)
            
            # STEP 2: Create Django apps (one by one)
            created_apps = []
            for i, app_config in enumerate(apps_to_create):
                app_name = app_config.get('name', f'app_{i+1}')
                progress = 30 + (i * 15)
                
                send_status(f'Running python manage.py startapp {app_name}...', 'scaffolding', progress)
                if not run_django_command(
                    ['python', 'manage.py', 'startapp', app_name],
                    cwd=project_path,
                    description=f'Creating {app_name} app scaffolding'
                ):
                    logger.warning(f'Failed to create app {app_name}')
                    continue
                
                created_apps.append(app_name)
                
                # Show scaffolded app files
                app_files = [
                    f'{app_name}/__init__.py',
                    f'{app_name}/apps.py', 
                    f'{app_name}/models.py',
                    f'{app_name}/views.py',
                    f'{app_name}/admin.py',
                    f'{app_name}/tests.py'
                ]
                
                for app_file in app_files:
                    file_path = project_path / app_file
                    if file_path.exists():
                        send_file_created(app_file, self._read_file_content(file_path), progress)
            
            send_status('Django scaffolding complete. Starting AI-powered customization...', 'generating', 50)
            
            # STEP 3: Stream AI-powered modifications to scaffolded files
            files_created = list(created_apps)  # Track created files
            
            # Generate customizations for each app
            for app_name in created_apps:
                # Customize models.py
                send_status(f'Customizing {app_name}/models.py...', 'generating', 55)
                models_prompt = f"""
                Based on this user request: "{user_prompt}"
                Create Django models for the {app_name} app. Generate complete models with:
                - Proper field types and relationships
                - Meta classes where appropriate
                - String representations
                - Any necessary methods
                
                Return ONLY the Python code for models.py, no explanations.
                """
                
                models_content = self.claude_service.generate_code(models_prompt)
                models_file = project_path / app_name / 'models.py'
                
                if models_content and models_content.strip():
                    models_file.write_text(models_content, encoding='utf-8')
                    send_file_created(f'{app_name}/models.py', models_content, 55)
                
                # Customize views.py
                send_status(f'Customizing {app_name}/views.py...', 'generating', 65)
                views_prompt = f"""
                Based on this user request: "{user_prompt}"
                Create Django views for the {app_name} app. Generate:
                - Class-based views where appropriate
                - Function-based views where simpler
                - Proper imports
                - CRUD operations as needed
                
                Return ONLY the Python code for views.py, no explanations.
                """
                
                views_content = self.claude_service.generate_code(views_prompt)
                views_file = project_path / app_name / 'views.py'
                
                if views_content and views_content.strip():
                    views_file.write_text(views_content, encoding='utf-8')
                    send_file_created(f'{app_name}/views.py', views_content, 65)
                
                # Create urls.py for app
                send_status(f'Creating {app_name}/urls.py...', 'generating', 70)
                urls_prompt = f"""
                Based on this user request: "{user_prompt}"
                Create URL patterns for the {app_name} app. Generate:
                - Proper URL patterns
                - View imports
                - app_name for namespacing
                
                Return ONLY the Python code for urls.py, no explanations.
                """
                
                urls_content = self.claude_service.generate_code(urls_prompt)
                urls_file = project_path / app_name / 'urls.py'
                
                if urls_content and urls_content.strip():
                    urls_file.write_text(urls_content, encoding='utf-8')
                    send_file_created(f'{app_name}/urls.py', urls_content, 70)
            
            # Update main settings.py to include apps
            send_status('Updating settings.py with new apps...', 'generating', 75)
            settings_file = project_path / project_name / 'settings.py'
            if settings_file.exists():
                settings_content = settings_file.read_text(encoding='utf-8')
                
                # Add created apps to INSTALLED_APPS
                installed_apps_addition = "    # Generated apps\n"
                for app_name in created_apps:
                    installed_apps_addition += f"    '{app_name}',\n"
                
                # Find INSTALLED_APPS and add new apps
                if 'INSTALLED_APPS = [' in settings_content:
                    settings_content = settings_content.replace(
                        'INSTALLED_APPS = [',
                        f'INSTALLED_APPS = [\n{installed_apps_addition}'
                    )
                    settings_file.write_text(settings_content, encoding='utf-8')
                    send_file_created(f'{project_name}/settings.py', settings_content, 75)
            
            # Update main urls.py to include app URLs  
            send_status('Updating main urls.py...', 'generating', 80)
            main_urls_file = project_path / project_name / 'urls.py'
            if main_urls_file.exists():
                urls_content = main_urls_file.read_text(encoding='utf-8')
                
                # Add include import if not present
                if 'from django.urls import include' not in urls_content:
                    urls_content = urls_content.replace(
                        'from django.urls import path',
                        'from django.urls import path, include'
                    )
                
                # Add URL patterns for each app
                url_patterns_addition = ""
                for app_name in created_apps:
                    url_patterns_addition += f"    path('{app_name}/', include('{app_name}.urls')),\n"
                
                if url_patterns_addition and 'urlpatterns = [' in urls_content:
                    urls_content = urls_content.replace(
                        'urlpatterns = [',
                        f'urlpatterns = [\n{url_patterns_addition}'
                    )
                    main_urls_file.write_text(urls_content, encoding='utf-8')
                    send_file_created(f'{project_name}/urls.py', urls_content, 80)
            
            # Create requirements.txt
            send_status('Creating requirements.txt...', 'generating', 85)
            requirements_content = self._generate_requirements_for_project(project_plan, user_prompt)
            requirements_file = project_path / 'requirements.txt'
            requirements_file.write_text(requirements_content, encoding='utf-8')
            send_file_created('requirements.txt', requirements_content, 85)
            
            # Send final file tree update
            final_tree = self._build_file_tree(project_path)
            send_file_tree_update(final_tree, 90)
            
            send_status('✅ Django project generated successfully!', 'completed', 100)
            
            return {
                'success': True,
                'project_id': project_id,
                'project_path': str(project_path),
                'project_name': project_name,
                'apps_created': created_apps,
                'files_count': len([f for f in project_path.rglob('*') if f.is_file()]),
                'message': f'Successfully created {project_name} with {len(created_apps)} apps using Django scaffolding approach'
            }
            
        except Exception as e:
            logger.error(f"Error during project generation: {e}")
            send_status(f'❌ Generation failed: {str(e)}', 'error', 0)
            return {
                'success': False,
                'error': str(e),
                'project_id': project_id
            }
        
    def _generate_requirements_for_project(self, project_plan: Dict, user_prompt: str) -> str:
        """Generate requirements.txt content based on project analysis"""
        # Base Django requirements
        requirements = [
            "Django>=4.2,<5.0",
            "python-dotenv>=0.19.0",
        ]
        
        # Add requirements based on features mentioned in user prompt
        user_prompt_lower = user_prompt.lower()
        
        if 'api' in user_prompt_lower or 'rest' in user_prompt_lower:
            requirements.append("djangorestframework>=3.14.0")
        
        if 'auth' in user_prompt_lower or 'login' in user_prompt_lower:
            requirements.append("django-allauth>=0.51.0")
        
        if 'cors' in user_prompt_lower:
            requirements.append("django-cors-headers>=4.0.0")
            
        if 'celery' in user_prompt_lower or 'task' in user_prompt_lower:
            requirements.append("celery>=5.3.0")
            requirements.append("redis>=4.5.0")
            
        if 'postgres' in user_prompt_lower:
            requirements.append("psycopg2-binary>=2.9.0")
            
        if 'mysql' in user_prompt_lower:
            requirements.append("mysqlclient>=2.1.0")
            
        # Development requirements
        requirements.extend([
            "# Development",
            "django-debug-toolbar>=4.0.0",
            "pytest>=7.0.0",
            "pytest-django>=4.5.0"
        ])
        
        return "\n".join(requirements)
                self._save_file(settings_file, settings_content, component_type='settings', progress_callback=progress_callback)
                files_created.append(str(settings_file))
                send_file_created(f'{project_name}/settings.py', settings_content, 45)
                
                # 3. Create other Django project files
                send_status('Creating URL configuration...', 'generating', 50)
                urls_content = self._generate_main_urls_file(analysis)
                urls_file = main_project_dir / 'urls.py'
                self._save_file(urls_file, urls_content, component_type='urls', progress_callback=progress_callback)
                files_created.append(str(urls_file))
                send_file_created(f'{project_name}/urls.py', urls_content, 55)
                
                # Create __init__.py files
                init_files = [
                    main_project_dir / '__init__.py',
                ]
                for init_file in init_files:
                    self._save_file(init_file, '')
                    files_created.append(str(init_file))
                
                # 4. Generate main application
                app_name = analysis.get('main_app', 'main')
                send_status(f'Creating {app_name} application...', 'generating', 60)
                app_files = self._generate_main_app_with_streaming(
                    project_path, app_name, analysis, send_file_created, 60, 80
                )
                files_created.extend(app_files)
                
                # 5. Create templates with streaming
                send_status('Creating templates...', 'generating', 80)
                template_files = self._create_templates_with_streaming(
                    project_path, analysis, send_file_created, 80, 90
                )
                files_created.extend(template_files)
                
                # 6. Create requirements.txt and other config files
                send_status('Creating configuration files...', 'generating', 90)
                config_files = self._create_config_files_with_streaming(
                    project_path, analysis, send_file_created, 90, 95
                )
                files_created.extend(config_files)
                
                # 7. Run comprehensive validation
                send_status('Running project validation...', 'validating', 95)
                validation_results = self._run_django_validation(str(project_path), progress_callback)
                
                # Check for critical errors
                critical_errors = [r for r in validation_results if r.level in [ValidationLevel.ERROR, ValidationLevel.CRITICAL]]
                if critical_errors:
                    send_status(f'⚠️ Project generated with {len(critical_errors)} validation errors', 'completed_with_warnings', 100)
                else:
                    send_status('✅ Project generation completed successfully!', 'completed', 100)
                
                return {
                    'success': True,
                    'files': [{'path': f} for f in files_created],
                    'message': f'Generated {len(files_created)} files for your {analysis.get("project_type", "Django")} project',
                    'project_id': project_id,
                    'analysis': analysis
                }
                
            except Exception as e:
                logger.error(f"Error during streaming generation: {e}")
                # Fallback to original method
                send_status('Switching to fallback generation...', 'generating', 50)
                return self.generate_project_from_prompt(user_prompt, project_id)
                
        except Exception as e:
            send_status(f'Generation failed: {str(e)}', 'error', 0)
            return {
                'success': False,
                'error': str(e)
            }

    def _generate_main_app_with_streaming(self, project_path, app_name, analysis, send_file_created, start_progress, end_progress):
        """Generate main app files with streaming updates"""
        files_created = []
        progress_step = (end_progress - start_progress) / 6  # 6 files to create
        current_progress = start_progress
        
        app_path = project_path / app_name
        app_path.mkdir(exist_ok=True)
        
        # Create __init__.py
        init_file = app_path / '__init__.py'
        self._save_file(init_file, '')
        files_created.append(str(init_file))
        current_progress += progress_step
        send_file_created(f'{app_name}/__init__.py', '', current_progress)
        
        # Create models.py (First in sequence)
        models_content = self._generate_models_file(analysis)
        models_file = app_path / 'models.py'
        self._save_file(models_file, models_content, component_type='models', progress_callback=send_file_created)
        files_created.append(str(models_file))
        current_progress += progress_step
        send_file_created(f'{app_name}/models.py', models_content, current_progress)
        
        # Create views.py (After models)
        views_content = self._generate_views_file(analysis)
        views_file = app_path / 'views.py'
        self._save_file(views_file, views_content, component_type='views', progress_callback=send_file_created)
        files_created.append(str(views_file))
        current_progress += progress_step
        send_file_created(f'{app_name}/views.py', views_content, current_progress)
        
        # Create urls.py (After views)
        urls_content = self._generate_app_urls_file(analysis)
        urls_file = app_path / 'urls.py'
        self._save_file(urls_file, urls_content, component_type='urls', progress_callback=send_file_created)
        files_created.append(str(urls_file))
        current_progress += progress_step
        send_file_created(f'{app_name}/urls.py', urls_content, current_progress)
        
        # Create admin.py
        admin_content = self._generate_admin_file(analysis)
        admin_file = app_path / 'admin.py'
        self._save_file(admin_file, admin_content)
        files_created.append(str(admin_file))
        current_progress += progress_step
        send_file_created(f'{app_name}/admin.py', admin_content, current_progress)
        
        # Create apps.py
        apps_content = self._generate_apps_file(analysis, app_name)
        apps_file = app_path / 'apps.py'
        self._save_file(apps_file, apps_content)
        files_created.append(str(apps_file))
        current_progress += progress_step
        send_file_created(f'{app_name}/apps.py', apps_content, current_progress)
        
        return files_created
    
    def _create_templates_with_streaming(self, project_path, analysis, send_file_created, start_progress, end_progress):
        """Create templates with streaming updates"""
        files_created = []
        
        # Create templates structure
        templates_path = project_path / 'templates'
        templates_path.mkdir(exist_ok=True)
        
        app_name = analysis.get('main_app', 'main')
        app_templates_path = templates_path / app_name
        app_templates_path.mkdir(exist_ok=True)
        
        progress_step = (end_progress - start_progress) / 3  # 3 template files
        current_progress = start_progress
        
        # Create base.html
        base_content = self._generate_base_template(analysis)
        base_file = app_templates_path / 'base.html'
        self._save_file(base_file, base_content)
        files_created.append(str(base_file))
        current_progress += progress_step
        send_file_created(f'templates/{app_name}/base.html', base_content, current_progress)
        
        # Create home.html
        home_content = self._generate_home_template(analysis)
        home_file = app_templates_path / 'home.html'
        self._save_file(home_file, home_content)
        files_created.append(str(home_file))
        current_progress += progress_step
        send_file_created(f'templates/{app_name}/home.html', home_content, current_progress)
        
        # Create form template
        form_content = self._generate_form_template(analysis)
        form_file = app_templates_path / 'create.html'
        self._save_file(form_file, form_content)
        files_created.append(str(form_file))
        current_progress += progress_step
        send_file_created(f'templates/{app_name}/create.html', form_content, current_progress)
        
        return files_created
    
    def _create_config_files_with_streaming(self, project_path, analysis, send_file_created, start_progress, end_progress):
        """Create configuration files with streaming updates"""
        files_created = []
        
        progress_step = (end_progress - start_progress) / 2  # 2 config files
        current_progress = start_progress
        
        # Create requirements.txt
        requirements_content = self._generate_requirements_file(analysis)
        requirements_file = project_path / 'requirements.txt'
        self._save_file(requirements_file, requirements_content)
        files_created.append(str(requirements_file))
        current_progress += progress_step
        send_file_created('requirements.txt', requirements_content, current_progress)
        
        # Create Dockerfile
        dockerfile_content = self._generate_dockerfile(analysis)
        dockerfile = project_path / 'Dockerfile'
        self._save_file(dockerfile, dockerfile_content)
        files_created.append(str(dockerfile))
        current_progress += progress_step
        send_file_created('Dockerfile', dockerfile_content, current_progress)
        
        return files_created


    # Helper function to test the generator
    def test_generator():
        """Test the smart project generator with various prompts."""
        
        test_prompts = [
            "Create a recipe sharing platform with user ratings and comments",
            "Build a task management system with kanban board",
            "Make a blog with rich text editor and social sharing",
            "Create an e-commerce site for handmade crafts",
            "Build a social media platform for photographers",
            "Create a learning management system with video courses",
            "Make a real estate listing website with search filters",
            "Build a fitness tracking app with workout plans",
            "Create a job board with company profiles",
            "Make a dating app with matching algorithm"
        ]
        
        generator = SmartProjectGenerator('./generated_projects')
        
        for i, prompt in enumerate(test_prompts):
            print(f"\nTesting prompt {i+1}: {prompt}")
            project_id = f"project_{i+1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            result = generator.generate_project_from_prompt(prompt, project_id)
            
            if result['success']:
                print(f"✅ Successfully generated: {result['project_name']}")
                print(f"   Path: {result['project_path']}")
                print(f"   Files: {result['files_generated']}")
            else:
                print(f"❌ Failed: {result['error']}")

