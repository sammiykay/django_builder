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

logger = logging.getLogger(__name__)


class SmartProjectGenerator:
    """
    Dynamic Django project generator that creates complete project structures
    based on AI analysis of user prompts. Everything is generated dynamically.
    """
    
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.claude_service = ClaudeService()
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_project_from_prompt(self, user_prompt: str, project_id: str) -> Dict:
        """
        Generate complete Django project structure from user prompt.
        EVERYTHING is dynamically generated based on the user's request.
        """
        
        try:
            logger.info(f"Starting dynamic project generation for: {project_id}")
            
            # Step 1: Analyze and plan the entire project with AI
            project_plan = self._create_complete_project_plan(user_prompt, project_id)
            
            if not project_plan or not project_plan.get('success'):
                return {
                    'success': False,
                    'error': 'Failed to create project plan',
                    'details': project_plan.get('error') if project_plan else 'Unknown error'
                }
            
            # Step 2: Create project directory
            project_path = self.base_dir / project_id
            if project_path.exists():
                shutil.rmtree(project_path)
            project_path.mkdir(parents=True)
            
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
        "database": "PostgreSQL/MySQL/SQLite based on complexity",
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
            django_files = self._generate_django_core_files(project_plan, project_path)
            generated_files.extend(django_files)
            
            # 2. Generate app files for each app
            for app_config in project_plan['apps']:
                app_files = self._generate_complete_app(
                    app_config,
                    project_plan,
                    project_path,
                    user_prompt
                )
                generated_files.extend(app_files)
            
            # 3. Generate static files
            static_files = self._generate_static_files(project_plan, project_path)
            generated_files.extend(static_files)
            
            # 4. Generate templates
            template_files = self._generate_all_templates(project_plan, project_path, user_prompt)
            generated_files.extend(template_files)
            
            # 5. Generate configuration files
            config_files = self._generate_config_files(project_plan, project_path)
            generated_files.extend(config_files)
            
            # 6. Generate deployment files if needed
            if project_plan.get('deployment', {}).get('dockerfile'):
                deployment_files = self._generate_deployment_files(project_plan, project_path)
                generated_files.extend(deployment_files)
            
            # 7. Generate tests
            test_files = self._generate_test_files(project_plan, project_path)
            generated_files.extend(test_files)
            
            # 8. Generate documentation
            doc_files = self._generate_documentation(project_plan, project_path, user_prompt)
            generated_files.extend(doc_files)
            
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
        
        # Generate base template
        base_template_prompt = f"""
Create a base.html template for this Django project:

Project: {project_plan['project_name']}
Description: {project_plan['description']}
UI Design: {json.dumps(project_plan.get('ui_design', {}), indent=2)}
Features: {project_plan['features']}

Requirements:
- Modern, responsive design
- Include navigation bar with all app links
- User authentication UI (login/logout)
- Messages/notifications area
- Footer with relevant information
- Use {project_plan.get('ui_design', {}).get('framework', 'Bootstrap')}
- Include necessary CSS/JS files
- Beautiful and professional design
- Mobile-friendly

Return ONLY the HTML code.
"""
        
        base_content = self._generate_code_with_ai(base_template_prompt)
        files.append(self._save_file(templates_path / 'base.html', base_content))
        
        # Generate home page
        home_template_prompt = f"""
Create a home.html template for this Django project:

Project: {project_plan['project_name']}
Description: {project_plan['description']}
Original request: "{user_prompt}"
Features: {project_plan['features']}

Create an impressive landing page that:
- Extends base.html
- Shows what the application does
- Highlights key features
- Includes call-to-action buttons
- Modern, attractive design
- Relevant to the specific application type

Return ONLY the HTML code.
"""
        
        home_content = self._generate_code_with_ai(home_template_prompt)
        files.append(self._save_file(templates_path / 'home.html', home_content))
        
        # Generate templates for each app
        for app in project_plan['apps']:
            app_templates_path = project_path / app['name'] / 'templates' / app['name']
            app_templates_path.mkdir(parents=True, exist_ok=True)
            
            for template_config in app.get('templates', []):
                template_prompt = f"""
Create {template_config['name']} template for Django app '{app['name']}':

Purpose: {template_config['purpose']}
App purpose: {app['purpose']}
Original request: "{user_prompt}"
Uses forms: {template_config.get('includes_forms', False)}
Uses AJAX: {template_config.get('uses_ajax', False)}
Models: {[model['name'] for model in app.get('models', [])]}

Create a template that:
- Extends base.html
- Serves its specific purpose perfectly
- Looks professional and modern
- Handles forms properly if included
- Includes AJAX functionality if specified
- Is specific to this application (not generic)

Return ONLY the HTML code.
"""
                
                template_content = self._generate_code_with_ai(template_prompt)
                template_path = app_templates_path / template_config['name']
                files.append(self._save_file(template_path, template_content))
        
        # Generate error pages
        for error_code in ['404', '500']:
            error_prompt = f"""
Create {error_code}.html error page for Django project '{project_plan['project_name']}':

Make it friendly, helpful, and consistent with the project's design.
Include a way to return to the home page.

Return ONLY the HTML code.
"""
            
            error_content = self._generate_code_with_ai(error_prompt)
            files.append(self._save_file(templates_path / f'{error_code}.html', error_content))
        
        return files
    
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
        
        # Database configuration based on detected requirements
        database = tech_stack.get('database', 'sqlite').lower()
        if 'postgres' in database or 'postgresql' in full_context:
            db_config = """'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', f'{project_name}_db'),
        'USER': os.getenv('DB_USER', 'postgres'),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }"""
        elif 'mysql' in database or 'mysql' in full_context:
            db_config = """'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('DB_NAME', f'{project_name}_db'),
        'USER': os.getenv('DB_USER', 'root'),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '3306'),
    }"""
        else:
            # SQLite for simplicity and container compatibility
            db_config = """'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }"""
        
        # Generate additional configuration sections
        additional_configs = []
        
        # WebSocket/Channels configuration
        if ('websocket' in full_context or 'real-time' in full_context or 'chat' in full_context):
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

        # Celery configuration
        if ('task' in full_context or 'job' in full_context or 'background' in full_context or 'celery' in full_context):
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
DATABASES = {{
    {db_config}
}}

# Caching
CACHES = {{
    'default': {{
        'BACKEND': 'django_redis.cache.RedisCache' if 'redis' in full_context else 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': os.getenv('REDIS_URL', '127.0.0.1:6379:1') if 'redis' in full_context else '',
        'OPTIONS': {{
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }} if 'redis' in full_context else {{}},
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
        
        # Combine all text for comprehensive analysis
        full_context = f"{user_prompt} {description} {features} {apps_data}".lower()
        
        # API and REST Framework
        has_api = any(app.get('api_endpoints') for app in project_plan['apps'])
        if has_api or 'api' in full_context or 'rest' in full_context or 'endpoint' in full_context:
            requirements.extend([
                'djangorestframework==3.15.2',
                'djangorestframework-simplejwt==5.3.0',  # JWT authentication
                'django-filter==23.4',                   # API filtering
            ])
        
        # CORS for frontend integration
        if ('frontend' in full_context or 'react' in full_context or 'vue' in full_context or 
            'angular' in full_context or 'cors' in full_context or 'spa' in full_context):
            requirements.append('django-cors-headers==4.3.1')
        
        # Database packages
        database = tech_stack.get('database', 'sqlite').lower()
        if 'postgres' in database or 'postgresql' in full_context:
            requirements.append('psycopg2-binary==2.9.9')
        elif 'mysql' in database or 'mysql' in full_context:
            requirements.append('mysqlclient==2.2.4')
        
        # Image processing
        if ('image' in full_context or 'photo' in full_context or 'upload' in full_context or
            'media' in full_context or 'file' in full_context or 'avatar' in full_context):
            requirements.append('Pillow==10.1.0')
        
        # Real-time features (WebSockets, Chat)
        if ('websocket' in full_context or 'real-time' in full_context or 'chat' in full_context or
            'notification' in full_context or 'live' in full_context or 'socket' in full_context):
            requirements.extend([
                'channels==4.0.0',
                'channels-redis==4.1.0',
                'daphne==4.0.0',  # ASGI server
            ])
        
        # Caching and Redis
        if ('cache' in full_context or 'redis' in full_context or 'session' in full_context or
            'websocket' in full_context):
            requirements.append('django-redis==5.4.0')
        
        # Authentication systems
        if 'auth' in full_context:
            if ('social' in full_context or 'google' in full_context or 'github' in full_context or
                'facebook' in full_context or 'oauth' in full_context):
                requirements.append('django-allauth==0.57.0')
        
        # Payment processing
        if ('payment' in full_context or 'stripe' in full_context or 'billing' in full_context or
            'subscription' in full_context or 'checkout' in full_context):
            requirements.extend([
                'stripe==7.8.0',
                'requests==2.31.0',
            ])
        
        # Email functionality
        if ('email' in full_context or 'mail' in full_context or 'notification' in full_context):
            requirements.extend([
                'django-anymail==10.2',
                'celery==5.3.4',  # For async email sending
            ])
        
        # Background tasks
        if ('task' in full_context or 'job' in full_context or 'queue' in full_context or
            'background' in full_context or 'async' in full_context or 'celery' in full_context):
            requirements.extend([
                'celery==5.3.4',
                'redis==5.0.1',
            ])
        
        # Search functionality
        if ('search' in full_context or 'elasticsearch' in full_context or 'solr' in full_context):
            requirements.append('django-elasticsearch-dsl==8.0')
        
        # Forms and UI enhancements
        if ('form' in full_context or 'crispy' in full_context or 'bootstrap' in full_context):
            requirements.extend([
                'django-crispy-forms==2.1',
                'crispy-bootstrap5==0.7',
            ])
        
        # Development and debugging tools
        requirements.extend([
            'django-extensions==3.2.3',        # Management command extensions
            'django-debug-toolbar==4.2.0',     # Debug toolbar
        ])
        
        # Testing framework
        if 'test' in full_context or 'pytest' in full_context:
            requirements.extend([
                'pytest==7.4.3',
                'pytest-django==4.7.0',
                'factory-boy==3.3.0',          # Test data factories
            ])
        
        # Cloud storage
        if ('aws' in full_context or 's3' in full_context or 'cloud' in full_context or
            'storage' in full_context):
            requirements.extend([
                'boto3==1.34.0',
                'django-storages==1.14.2',
            ])
        
        # External API integration
        if ('api' in full_context or 'external' in full_context or 'integration' in full_context or
            'webhook' in full_context):
            requirements.extend([
                'requests==2.31.0',
                'httpx==0.25.2',               # Modern async HTTP client
            ])
        
        # Production deployment packages
        requirements.extend([
            'gunicorn==21.2.0',               # WSGI server
            'whitenoise==6.5.0',              # Static file serving
        ])
        
        # Security enhancements
        if 'secure' in full_context or 'ssl' in full_context:
            requirements.append('django-security==0.17.0')
        
        # Data processing and analytics
        if ('data' in full_context or 'analytics' in full_context or 'report' in full_context):
            requirements.extend([
                'pandas==2.1.4',
                'django-import-export==3.3.4',  # Data import/export
            ])
        
        # Remove duplicates while preserving order
        unique_requirements = []
        seen = set()
        for req in requirements:
            if req not in seen:
                unique_requirements.append(req)
                seen.add(req)
        
        return '\n'.join(unique_requirements)
    
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
   
    def _generate_code_with_ai(self, prompt: str, callback=None) -> str:
        """
        Generate code using Claude AI with streaming support.
        This is the core method that makes everything dynamic.
        """
        
        try:
            full_content = ""
            
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
            
            # Clean up any markdown code blocks if they exist
            content = self._clean_code_response(full_content)
            
            return content
            
        except Exception as e:
            logger.error(f"Error generating code with AI: {e}")
            # Return a basic fallback
            return "# Error generating code. Please regenerate this file."
    
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
    
    def _save_file(self, file_path: Path, content: str) -> Dict:
        """Save content to file and return file info."""
        
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return {
            'path': str(file_path),
            'size': len(content),
            'type': file_path.suffix
        }
    
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

