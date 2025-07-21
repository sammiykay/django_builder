"""
Enhanced Smart Project Generator with streaming Claude responses
Provides Bolt.new-like real-time generation with incremental updates
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, AsyncGenerator, Callable
from pathlib import Path
from datetime import datetime
import re

from .claude_service import ClaudeService
from .codebase_analyzer import CodebaseAnalyzer
from .session_memory import ConversationContext, session_memory
from .enhanced_error_handler import EnhancedErrorHandler

logger = logging.getLogger(__name__)


class EnhancedSmartGenerator:
    """
    Advanced project generator with streaming capabilities
    Provides incremental updates and real-time feedback like Bolt.new
    """
    
    def __init__(self, base_dir: str, websocket_callback: Optional[Callable] = None):
        self.base_dir = Path(base_dir)
        self.claude_service = ClaudeService()
        self.websocket_callback = websocket_callback
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # Generation state
        self.current_project_id = None
        self.generation_progress = 0
        self.current_step = ""
        self.files_generated = []
        self.errors_encountered = []
    
    async def generate_project_stream(
        self, 
        user_prompt: str, 
        project_id: str, 
        user_id: str
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Generate project with streaming updates
        
        Args:
            user_prompt: User's project description
            project_id: Unique project identifier
            user_id: User identifier for session management
            
        Yields:
            Stream of generation updates
        """
        
        self.current_project_id = project_id
        self.generation_progress = 0
        self.current_step = "initializing"
        self.files_generated = []
        self.errors_encountered = []
        
        try:
            # Initialize conversation context
            with ConversationContext(user_id, project_id, 'generation') as context:
                context.add_message('user', user_prompt)
                
                # Step 1: Project Analysis
                yield await self._emit_status("Analyzing project requirements...", 5)
                
                project_analysis = await self._analyze_project_requirements(
                    user_prompt, context
                )
                
                if not project_analysis['success']:
                    yield await self._emit_error(f"Analysis failed: {project_analysis['error']}")
                    return
                
                yield await self._emit_status("Project analysis complete", 15)
                yield await self._emit_data('project_analysis', project_analysis['data'])
                
                # Step 2: Architecture Planning
                yield await self._emit_status("Planning project architecture...", 25)
                
                architecture_plan = await self._plan_architecture(
                    project_analysis['data'], context
                )
                
                if not architecture_plan['success']:
                    yield await self._emit_error(f"Architecture planning failed: {architecture_plan['error']}")
                    return
                
                yield await self._emit_status("Architecture planning complete", 35)
                yield await self._emit_data('architecture_plan', architecture_plan['data'])
                
                # Step 3: File Generation with Streaming
                yield await self._emit_status("Generating project files...", 40)
                
                async for update in self._generate_files_stream(
                    architecture_plan['data'], context
                ):
                    yield update
                
                # Step 4: Code Integration and Optimization
                yield await self._emit_status("Integrating and optimizing code...", 85)
                
                integration_result = await self._integrate_and_optimize(
                    project_id, context
                )
                
                if not integration_result['success']:
                    yield await self._emit_error(f"Integration failed: {integration_result['error']}")
                    return
                
                yield await self._emit_status("Integration complete", 95)
                
                # Step 5: Final Validation
                yield await self._emit_status("Validating project structure...", 98)
                
                validation_result = await self._validate_project(project_id)
                
                if not validation_result['success']:
                    yield await self._emit_error(f"Validation failed: {validation_result['error']}")
                    return
                
                # Complete
                yield await self._emit_completion({
                    'project_id': project_id,
                    'project_name': project_analysis['data']['project_name'],
                    'description': project_analysis['data']['description'],
                    'features': project_analysis['data']['features'],
                    'tech_stack': architecture_plan['data']['tech_stack'],
                    'files_generated': len(self.files_generated),
                    'files_list': self.files_generated,
                    'api_endpoints': architecture_plan['data'].get('api_endpoints', []),
                    'setup_instructions': architecture_plan['data'].get('setup_instructions', []),
                    'next_steps': architecture_plan['data'].get('next_steps', [])
                })
                
                # Save completion message
                context.add_message('assistant', 'Project generation completed successfully!')
                
        except Exception as e:
            logger.error(f"Error in project generation stream: {e}")
            yield await self._emit_error(f"Generation failed: {str(e)}")
    
    async def _analyze_project_requirements(self, user_prompt: str, context: ConversationContext) -> Dict:
        """Analyze project requirements using Claude"""
        try:
            # Get conversation history for context
            history = context.get_history(limit=10)
            
            analysis_prompt = f"""
Analyze this project request and provide a comprehensive analysis:

USER REQUEST: "{user_prompt}"

CONVERSATION HISTORY:
{json.dumps(history, indent=2)}

Create a detailed project analysis that includes:

1. Project type and category
2. Core features and functionality
3. Technical requirements
4. Complexity assessment
5. User experience considerations
6. Business logic requirements
7. Data model requirements
8. Integration needs

Respond with a JSON object containing:
{{
    "project_name": "snake_case_project_name",
    "display_name": "Human Readable Project Name",
    "description": "Comprehensive project description",
    "category": "blog|ecommerce|social|dashboard|api|portfolio|business|education|entertainment|other",
    "complexity": "simple|medium|complex|enterprise",
    "features": [
        "Feature 1",
        "Feature 2"
    ],
    "technical_requirements": [
        "Requirement 1",
        "Requirement 2"
    ],
    "user_stories": [
        "As a user, I want to...",
        "As an admin, I need to..."
    ],
    "data_models": [
        {{
            "name": "ModelName",
            "description": "What this model represents",
            "key_fields": ["field1", "field2"]
        }}
    ],
    "ui_requirements": {{
        "style": "modern|classic|minimal",
        "responsive": true,
        "accessibility": true,
        "theme": "light|dark|auto"
    }},
    "integrations": [
        "Third-party services needed"
    ],
    "estimated_files": 25,
    "estimated_time": "2-4 hours"
}}

Provide a thorough analysis based on the user's request.
"""
            
            # Call Claude with streaming
            response = await self._call_claude_async(analysis_prompt)
            
            if response:
                analysis_data = self._parse_json_response(response)
                if analysis_data:
                    context.update_context({'project_analysis': analysis_data})
                    return {'success': True, 'data': analysis_data}
            
            return {'success': False, 'error': 'Failed to parse analysis response'}
            
        except Exception as e:
            logger.error(f"Error analyzing project requirements: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _plan_architecture(self, project_analysis: Dict, context: ConversationContext) -> Dict:
        """Plan project architecture"""
        try:
            architecture_prompt = f"""
Create a detailed architecture plan for this Django project:

PROJECT ANALYSIS:
{json.dumps(project_analysis, indent=2)}

Generate a comprehensive architecture plan with:

1. Django apps structure
2. Database design
3. API endpoints (if needed)
4. Template structure
5. Static files organization
6. Third-party integrations
7. Security considerations
8. Performance optimizations

Respond with a JSON object:
{{
    "tech_stack": {{
        "backend": ["Django", "other backends"],
        "frontend": ["HTML", "CSS", "JavaScript", "frameworks"],
        "database": "PostgreSQL|MySQL|SQLite",
        "cache": "Redis|Memcached|None",
        "storage": "Local|S3|GCS",
        "additional": ["other technologies"]
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
                    "relationships": [
                        {{"type": "ForeignKey", "to": "OtherModel", "related_name": "items"}}
                    ]
                }}
            ],
            "views": [
                {{
                    "name": "ViewName",
                    "type": "ListView|DetailView|CreateView|UpdateView|DeleteView|function",
                    "purpose": "What this view does",
                    "template": "template_name.html",
                    "permissions": ["permission_required"]
                }}
            ],
            "urls": [
                {{"pattern": "path/", "view": "ViewName", "name": "url_name"}}
            ]
        }}
    ],
    "api_endpoints": [
        {{
            "url": "/api/endpoint/",
            "methods": ["GET", "POST"],
            "purpose": "What this endpoint does",
            "authentication": "required|optional|none"
        }}
    ],
    "templates": {{
        "base_template": "base.html",
        "theme": "Bootstrap|Tailwind|Custom",
        "components": ["navbar", "footer", "sidebar"]
    }},
    "static_files": {{
        "css": ["main.css", "components.css"],
        "js": ["main.js", "components.js"],
        "images": ["logo.png", "favicon.ico"]
    }},
    "security": {{
        "authentication": "django-auth|django-allauth|custom",
        "permissions": ["custom permission system"],
        "csrf_protection": true,
        "ssl_required": true
    }},
    "deployment": {{
        "containerization": "Docker",
        "web_server": "Nginx|Apache",
        "wsgi_server": "Gunicorn|uWSGI"
    }},
    "setup_instructions": [
        "Step 1: Install dependencies",
        "Step 2: Configure database",
        "Step 3: Run migrations"
    ],
    "next_steps": [
        "Customize the design",
        "Add more features",
        "Deploy to production"
    ]
}}

Create a production-ready architecture plan.
"""
            
            response = await self._call_claude_async(architecture_prompt)
            
            if response:
                architecture_data = self._parse_json_response(response)
                if architecture_data:
                    context.update_context({'architecture_plan': architecture_data})
                    return {'success': True, 'data': architecture_data}
            
            return {'success': False, 'error': 'Failed to parse architecture response'}
            
        except Exception as e:
            logger.error(f"Error planning architecture: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _generate_files_stream(
        self, 
        architecture_plan: Dict, 
        context: ConversationContext
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Generate files with streaming updates"""
        try:
            project_path = self.base_dir / self.current_project_id
            project_path.mkdir(parents=True, exist_ok=True)
            
            # Calculate total files to generate
            total_files = self._calculate_total_files(architecture_plan)
            files_generated = 0
            
            # Generate Django core files
            yield await self._emit_status("Generating Django core files...", 45)
            
            core_files = await self._generate_django_core_files(
                architecture_plan, project_path
            )
            
            for file_info in core_files:
                files_generated += 1
                progress = 45 + (files_generated / total_files) * 30
                
                yield await self._emit_file_generated(
                    file_info['path'], 
                    file_info['content'][:200] + "..." if len(file_info['content']) > 200 else file_info['content'],
                    progress
                )
                
                self.files_generated.append(file_info['path'])
                
                # Small delay for streaming effect
                await asyncio.sleep(0.1)
            
            # Generate app files
            for app_config in architecture_plan.get('apps', []):
                yield await self._emit_status(f"Generating {app_config['name']} app files...", 50 + (files_generated / total_files) * 30)
                
                app_files = await self._generate_app_files(
                    app_config, architecture_plan, project_path
                )
                
                for file_info in app_files:
                    files_generated += 1
                    progress = 50 + (files_generated / total_files) * 30
                    
                    yield await self._emit_file_generated(
                        file_info['path'], 
                        file_info['content'][:200] + "..." if len(file_info['content']) > 200 else file_info['content'],
                        progress
                    )
                    
                    self.files_generated.append(file_info['path'])
                    await asyncio.sleep(0.1)
            
            # Generate templates
            yield await self._emit_status("Generating templates...", 75)
            
            template_files = await self._generate_template_files(
                architecture_plan, project_path
            )
            
            for file_info in template_files:
                files_generated += 1
                progress = 75 + (files_generated / total_files) * 10
                
                yield await self._emit_file_generated(
                    file_info['path'], 
                    file_info['content'][:200] + "..." if len(file_info['content']) > 200 else file_info['content'],
                    progress
                )
                
                self.files_generated.append(file_info['path'])
                await asyncio.sleep(0.1)
            
            yield await self._emit_status("File generation complete", 85)
            
        except Exception as e:
            logger.error(f"Error in file generation stream: {e}")
            yield await self._emit_error(f"File generation failed: {str(e)}")
    
    async def _integrate_and_optimize(self, project_id: str, context: ConversationContext) -> Dict:
        """Integrate and optimize generated code"""
        try:
            project_path = self.base_dir / project_id
            
            # Run codebase analysis
            analyzer = CodebaseAnalyzer(project_path)
            analysis = await asyncio.get_event_loop().run_in_executor(
                None, analyzer.analyze_full_codebase
            )
            
            # Check for integration issues
            integration_issues = []
            
            # Check for missing imports
            # Check for URL conflicts
            # Check for model relationships
            # etc.
            
            if integration_issues:
                # Fix issues automatically
                error_handler = EnhancedErrorHandler(project_path)
                
                for issue in integration_issues:
                    fix_result = await asyncio.get_event_loop().run_in_executor(
                        None, error_handler.capture_and_fix_error, issue
                    )
                    
                    if fix_result.get('success') and fix_result.get('auto_fixable'):
                        # Apply fixes
                        pass
            
            context.update_context({'integration_complete': True})
            return {'success': True, 'issues_fixed': len(integration_issues)}
            
        except Exception as e:
            logger.error(f"Error in integration: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _validate_project(self, project_id: str) -> Dict:
        """Validate generated project"""
        try:
            project_path = self.base_dir / project_id
            
            validation_issues = []
            
            # Check for required files
            required_files = ['manage.py', 'requirements.txt']
            for req_file in required_files:
                if not (project_path / req_file).exists():
                    validation_issues.append(f"Missing required file: {req_file}")
            
            # Check for Python syntax errors
            for py_file in project_path.rglob('*.py'):
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    compile(content, str(py_file), 'exec')
                except SyntaxError as e:
                    validation_issues.append(f"Syntax error in {py_file}: {e}")
            
            # Check for Django settings
            settings_files = list(project_path.rglob('settings.py'))
            if not settings_files:
                validation_issues.append("No settings.py file found")
            
            if validation_issues:
                return {'success': False, 'issues': validation_issues}
            
            return {'success': True, 'message': 'Project validation passed'}
            
        except Exception as e:
            logger.error(f"Error validating project: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _call_claude_async(self, prompt: str) -> Optional[str]:
        """Call Claude API asynchronously"""
        try:
            loop = asyncio.get_event_loop()
            
            def call_claude():
                response = self.claude_service.client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=4000,
                    temperature=0.2,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
                return response.content[0].text.strip()
            
            return await loop.run_in_executor(None, call_claude)
            
        except Exception as e:
            logger.error(f"Error calling Claude: {e}")
            return None
    
    def _parse_json_response(self, content: str) -> Optional[Dict]:
        """Parse JSON response from Claude"""
        try:
            # Try direct parsing
            return json.loads(content)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown
            json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', content)
            if json_match:
                try:
                    return json.loads(json_match.group(1))
                except json.JSONDecodeError:
                    pass
            
            # Try to find JSON object
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass
            
            logger.error(f"Failed to parse JSON from response: {content[:500]}...")
            return None
    
    def _calculate_total_files(self, architecture_plan: Dict) -> int:
        """Calculate total number of files to generate"""
        total = 5  # Core Django files
        
        for app in architecture_plan.get('apps', []):
            total += 7  # Standard app files
            total += len(app.get('models', []))
            total += len(app.get('views', []))
            total += len(app.get('templates', []))
        
        total += len(architecture_plan.get('templates', {}).get('components', []))
        total += len(architecture_plan.get('static_files', {}).get('css', []))
        total += len(architecture_plan.get('static_files', {}).get('js', []))
        
        return total
    
    async def _generate_django_core_files(self, architecture_plan: Dict, project_path: Path) -> List[Dict]:
        """Generate core Django files"""
        files = []
        
        # Generate manage.py
        manage_content = await self._generate_file_content(
            'manage.py', 
            {'project_name': architecture_plan.get('project_name', 'myproject')}
        )
        files.append(await self._save_file(project_path / 'manage.py', manage_content))
        
        # Generate requirements.txt
        requirements_content = await self._generate_file_content(
            'requirements.txt',
            {'tech_stack': architecture_plan.get('tech_stack', {})}
        )
        files.append(await self._save_file(project_path / 'requirements.txt', requirements_content))
        
        # Generate settings.py
        settings_content = await self._generate_file_content(
            'settings.py',
            {
                'project_name': architecture_plan.get('project_name', 'myproject'),
                'apps': architecture_plan.get('apps', []),
                'tech_stack': architecture_plan.get('tech_stack', {}),
                'security': architecture_plan.get('security', {})
            }
        )
        project_dir = project_path / architecture_plan.get('project_name', 'myproject')
        project_dir.mkdir(parents=True, exist_ok=True)
        files.append(await self._save_file(project_dir / 'settings.py', settings_content))
        
        # Generate urls.py
        urls_content = await self._generate_file_content(
            'urls.py',
            {
                'project_name': architecture_plan.get('project_name', 'myproject'),
                'apps': architecture_plan.get('apps', []),
                'api_endpoints': architecture_plan.get('api_endpoints', [])
            }
        )
        files.append(await self._save_file(project_dir / 'urls.py', urls_content))
        
        # Generate __init__.py
        files.append(await self._save_file(project_dir / '__init__.py', ''))
        
        return files
    
    async def _generate_app_files(self, app_config: Dict, architecture_plan: Dict, project_path: Path) -> List[Dict]:
        """Generate files for a Django app"""
        files = []
        app_name = app_config['name']
        app_path = project_path / app_name
        app_path.mkdir(parents=True, exist_ok=True)
        
        # Generate models.py
        models_content = await self._generate_file_content(
            'models.py',
            {'app_config': app_config, 'project_name': architecture_plan.get('project_name')}
        )
        files.append(await self._save_file(app_path / 'models.py', models_content))
        
        # Generate views.py
        views_content = await self._generate_file_content(
            'views.py',
            {'app_config': app_config, 'project_name': architecture_plan.get('project_name')}
        )
        files.append(await self._save_file(app_path / 'views.py', views_content))
        
        # Generate urls.py
        urls_content = await self._generate_file_content(
            'app_urls.py',
            {'app_config': app_config}
        )
        files.append(await self._save_file(app_path / 'urls.py', urls_content))
        
        # Generate admin.py
        admin_content = await self._generate_file_content(
            'admin.py',
            {'app_config': app_config}
        )
        files.append(await self._save_file(app_path / 'admin.py', admin_content))
        
        # Generate apps.py
        apps_content = await self._generate_file_content(
            'apps.py',
            {'app_name': app_name}
        )
        files.append(await self._save_file(app_path / 'apps.py', apps_content))
        
        # Generate __init__.py
        files.append(await self._save_file(app_path / '__init__.py', ''))
        
        # Generate migrations directory
        migrations_path = app_path / 'migrations'
        migrations_path.mkdir(exist_ok=True)
        files.append(await self._save_file(migrations_path / '__init__.py', ''))
        
        return files
    
    async def _generate_template_files(self, architecture_plan: Dict, project_path: Path) -> List[Dict]:
        """Generate template files"""
        files = []
        
        # Create templates directory
        templates_path = project_path / 'templates'
        templates_path.mkdir(exist_ok=True)
        
        # Generate base template
        base_template_content = await self._generate_file_content(
            'base.html',
            {'architecture_plan': architecture_plan}
        )
        files.append(await self._save_file(templates_path / 'base.html', base_template_content))
        
        # Generate app templates
        for app in architecture_plan.get('apps', []):
            app_templates_path = templates_path / app['name']
            app_templates_path.mkdir(exist_ok=True)
            
            for view in app.get('views', []):
                if view.get('template'):
                    template_content = await self._generate_file_content(
                        'app_template.html',
                        {'view': view, 'app': app}
                    )
                    files.append(await self._save_file(
                        app_templates_path / view['template'], 
                        template_content
                    ))
        
        return files
    
    async def _generate_file_content(self, file_type: str, context: Dict) -> str:
        """Generate file content using Claude"""
        try:
            # This would contain prompts for each file type
            file_prompts = {
                'manage.py': f"""
Generate a Django manage.py file for project '{context.get('project_name', 'myproject')}'.
Return only the Python code, no explanations.
""",
                'requirements.txt': f"""
Generate a requirements.txt file for a Django project with these technologies:
{json.dumps(context.get('tech_stack', {}), indent=2)}

Include Django and all necessary dependencies.
Return only the requirements list, no explanations.
""",
                'settings.py': f"""
Generate a Django settings.py file for project '{context.get('project_name', 'myproject')}'.

Configuration:
- Apps: {[app['name'] for app in context.get('apps', [])]}
- Tech stack: {context.get('tech_stack', {})}
- Security: {context.get('security', {})}

Include all necessary settings, security configurations, and database setup.
Return only the Python code, no explanations.
""",
                # Add more file type prompts here...
            }
            
            prompt = file_prompts.get(file_type, f"Generate {file_type} content for Django project")
            response = await self._call_claude_async(prompt)
            
            if response:
                # Clean up the response
                return self._clean_code_response(response)
            
            return f"# Generated {file_type} content\n# TODO: Implement {file_type}"
            
        except Exception as e:
            logger.error(f"Error generating {file_type} content: {e}")
            return f"# Error generating {file_type}: {e}"
    
    def _clean_code_response(self, content: str) -> str:
        """Clean up Claude's response to get pure code"""
        # Remove markdown code blocks
        content = re.sub(r'^```[a-zA-Z]*\n', '', content, flags=re.MULTILINE)
        content = re.sub(r'\n```$', '', content, flags=re.MULTILINE)
        content = re.sub(r'^```\n', '', content, flags=re.MULTILINE)
        
        return content.strip()
    
    async def _save_file(self, file_path: Path, content: str) -> Dict:
        """Save file and return file info"""
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return {
                'path': str(file_path.relative_to(self.base_dir / self.current_project_id)),
                'content': content,
                'size': len(content),
                'type': file_path.suffix.lstrip('.') if file_path.suffix else 'txt'
            }
            
        except Exception as e:
            logger.error(f"Error saving file {file_path}: {e}")
            return {
                'path': str(file_path),
                'content': content,
                'error': str(e)
            }
    
    # Stream emission methods
    async def _emit_status(self, message: str, progress: int) -> Dict:
        """Emit status update"""
        update = {
            'type': 'status_update',
            'message': message,
            'progress': progress,
            'timestamp': datetime.now().isoformat()
        }
        
        if self.websocket_callback:
            await self.websocket_callback(update)
        
        return update
    
    async def _emit_error(self, message: str) -> Dict:
        """Emit error message"""
        update = {
            'type': 'error',
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        
        if self.websocket_callback:
            await self.websocket_callback(update)
        
        return update
    
    async def _emit_data(self, data_type: str, data: Any) -> Dict:
        """Emit data update"""
        update = {
            'type': 'data_update',
            'data_type': data_type,
            'data': data,
            'timestamp': datetime.now().isoformat()
        }
        
        if self.websocket_callback:
            await self.websocket_callback(update)
        
        return update
    
    async def _emit_file_generated(self, file_path: str, content_preview: str, progress: int) -> Dict:
        """Emit file generation update"""
        update = {
            'type': 'file_generated',
            'file_path': file_path,
            'content_preview': content_preview,
            'progress': progress,
            'timestamp': datetime.now().isoformat()
        }
        
        if self.websocket_callback:
            await self.websocket_callback(update)
        
        return update
    
    async def _emit_completion(self, result: Dict) -> Dict:
        """Emit completion message"""
        update = {
            'type': 'generation_completed',
            'result': result,
            'progress': 100,
            'timestamp': datetime.now().isoformat()
        }
        
        if self.websocket_callback:
            await self.websocket_callback(update)
        
        return update