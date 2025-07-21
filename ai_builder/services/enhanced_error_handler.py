"""
Enhanced Error Handler for Django AI Builder
Captures stderr, exceptions, and tracebacks to send to Claude for intelligent error fixing
"""

import logging
import traceback
import sys
import subprocess
import json
import re
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime

from .claude_service import ClaudeService

logger = logging.getLogger(__name__)


class EnhancedErrorHandler:
    """
    Advanced error handling system that captures and analyzes errors
    to provide intelligent fixes using Claude AI
    """
    
    def __init__(self, project_path: Path):
        self.project_path = Path(project_path)
        self.claude_service = ClaudeService()
        self.error_history = []
        
    def capture_and_fix_error(self, error_data: Dict) -> Dict:
        """
        Main method to capture error and generate fix using Claude
        
        Args:
            error_data: Dictionary containing error information
            
        Returns:
            Dictionary with fix suggestions and code changes
        """
        try:
            # Analyze the error
            error_analysis = self._analyze_error(error_data)
            
            # Get project context
            project_context = self._get_project_context()
            
            # Generate fix using Claude
            fix_result = self._generate_fix_with_claude(error_analysis, project_context)
            
            # Apply fixes if possible
            if fix_result.get('auto_fixable', False):
                applied_fixes = self._apply_automatic_fixes(fix_result)
                fix_result['applied_fixes'] = applied_fixes
            
            # Store in error history
            self._store_error_history(error_analysis, fix_result)
            
            return fix_result
            
        except Exception as e:
            logger.error(f"Error in enhanced error handler: {e}")
            return {
                'success': False,
                'error': f"Failed to process error: {str(e)}",
                'original_error': error_data
            }
    
    def _analyze_error(self, error_data: Dict) -> Dict:
        """
        Analyze error data to extract useful information
        """
        error_type = error_data.get('error_type', 'unknown')
        error_message = error_data.get('error_message', '')
        traceback_str = error_data.get('traceback', '')
        command = error_data.get('command', '')
        stderr = error_data.get('stderr', '')
        stdout = error_data.get('stdout', '')
        
        analysis = {
            'timestamp': datetime.now().isoformat(),
            'error_type': error_type,
            'error_message': error_message,
            'traceback': traceback_str,
            'command': command,
            'stderr': stderr,
            'stdout': stdout,
            'severity': self._determine_severity(error_type, error_message),
            'category': self._categorize_error(error_type, error_message, traceback_str),
            'affected_files': self._extract_affected_files(traceback_str, stderr),
            'suggested_actions': self._get_preliminary_actions(error_type, error_message)
        }
        
        return analysis
    
    def _determine_severity(self, error_type: str, error_message: str) -> str:
        """Determine error severity level"""
        high_severity_patterns = [
            'IntegrityError', 'DataError', 'ProgrammingError',
            'ImproperlyConfigured', 'SystemError', 'MemoryError'
        ]
        
        medium_severity_patterns = [
            'ValidationError', 'PermissionError', 'FileNotFoundError',
            'ImportError', 'ModuleNotFoundError', 'AttributeError'
        ]
        
        for pattern in high_severity_patterns:
            if pattern.lower() in error_message.lower() or pattern.lower() in error_type.lower():
                return 'high'
        
        for pattern in medium_severity_patterns:
            if pattern.lower() in error_message.lower() or pattern.lower() in error_type.lower():
                return 'medium'
        
        return 'low'
    
    def _categorize_error(self, error_type: str, error_message: str, traceback_str: str) -> str:
        """Categorize error type"""
        categories = {
            'database': ['IntegrityError', 'DataError', 'ProgrammingError', 'migration'],
            'import': ['ImportError', 'ModuleNotFoundError', 'cannot import'],
            'template': ['TemplateDoesNotExist', 'TemplateSyntaxError', 'template'],
            'url': ['NoReverseMatch', 'Resolver404', 'url'],
            'model': ['AttributeError', 'FieldError', 'model'],
            'view': ['TypeError', 'ValueError', 'view'],
            'form': ['ValidationError', 'form'],
            'static': ['FileNotFoundError', 'static', 'media'],
            'settings': ['ImproperlyConfigured', 'settings'],
            'permission': ['PermissionError', 'permission'],
            'syntax': ['SyntaxError', 'IndentationError', 'syntax']
        }
        
        error_text = (error_type + ' ' + error_message + ' ' + traceback_str).lower()
        
        for category, patterns in categories.items():
            if any(pattern.lower() in error_text for pattern in patterns):
                return category
        
        return 'general'
    
    def _extract_affected_files(self, traceback_str: str, stderr: str) -> List[str]:
        """Extract file paths from traceback and stderr"""
        files = []
        
        # Extract from traceback
        file_pattern = r'File "([^"]+)"'
        traceback_files = re.findall(file_pattern, traceback_str)
        files.extend(traceback_files)
        
        # Extract from stderr
        stderr_files = re.findall(file_pattern, stderr)
        files.extend(stderr_files)
        
        # Filter to project files only
        project_files = []
        for file_path in files:
            if self.project_path.name in file_path or file_path.startswith('./'):
                project_files.append(file_path)
        
        return list(set(project_files))  # Remove duplicates
    
    def _get_preliminary_actions(self, error_type: str, error_message: str) -> List[str]:
        """Get preliminary action suggestions"""
        actions = []
        
        if 'migration' in error_message.lower():
            actions.extend([
                'Run python manage.py makemigrations',
                'Run python manage.py migrate',
                'Check for conflicting migrations'
            ])
        
        if 'importerror' in error_type.lower() or 'modulenotfounderror' in error_type.lower():
            actions.extend([
                'Check if module is installed',
                'Verify PYTHONPATH settings',
                'Check for typos in import statements'
            ])
        
        if 'templatenotexist' in error_message.lower():
            actions.extend([
                'Create the missing template file',
                'Check TEMPLATES setting in settings.py',
                'Verify template directory structure'
            ])
        
        return actions
    
    def _get_project_context(self) -> Dict:
        """
        Get comprehensive project context for Claude
        """
        try:
            context = {
                'project_structure': self._get_project_structure(),
                'key_files': self._get_key_files_content(),
                'installed_apps': self._get_installed_apps(),
                'database_models': self._get_database_models(),
                'url_patterns': self._get_url_patterns(),
                'recent_changes': self._get_recent_file_changes(),
                'requirements': self._get_requirements()
            }
            
            return context
            
        except Exception as e:
            logger.error(f"Error getting project context: {e}")
            return {'error': 'Failed to get project context'}
    
    def _get_project_structure(self) -> Dict:
        """Get project file structure"""
        structure = {}
        
        try:
            for root, dirs, files in self.project_path.walk():
                # Skip common directories
                dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'node_modules', 'venv', 'env']]
                
                rel_root = root.relative_to(self.project_path)
                structure[str(rel_root)] = {
                    'directories': dirs,
                    'files': files
                }
                
        except Exception as e:
            logger.error(f"Error getting project structure: {e}")
            structure = {'error': 'Failed to get structure'}
        
        return structure
    
    def _get_key_files_content(self) -> Dict:
        """Get content of key project files"""
        key_files = {}
        
        important_files = [
            'settings.py', 'urls.py', 'wsgi.py', 'asgi.py',
            'models.py', 'views.py', 'forms.py', 'admin.py',
            'requirements.txt', 'manage.py'
        ]
        
        try:
            for file_path in self.project_path.rglob('*'):
                if file_path.is_file() and file_path.name in important_files:
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            if len(content) < 10000:  # Limit file size
                                key_files[str(file_path.relative_to(self.project_path))] = content
                    except Exception as e:
                        logger.warning(f"Could not read {file_path}: {e}")
                        
        except Exception as e:
            logger.error(f"Error getting key files: {e}")
        
        return key_files
    
    def _get_installed_apps(self) -> List[str]:
        """Extract INSTALLED_APPS from settings"""
        settings_files = list(self.project_path.rglob('settings.py'))
        apps = []
        
        for settings_file in settings_files:
            try:
                with open(settings_file, 'r') as f:
                    content = f.read()
                    
                # Extract INSTALLED_APPS
                match = re.search(r'INSTALLED_APPS\s*=\s*\[(.*?)\]', content, re.DOTALL)
                if match:
                    apps_str = match.group(1)
                    # Extract app names
                    app_matches = re.findall(r"['\"]([^'\"]+)['\"]", apps_str)
                    apps.extend(app_matches)
                    
            except Exception as e:
                logger.warning(f"Could not read settings file {settings_file}: {e}")
        
        return list(set(apps))
    
    def _get_database_models(self) -> Dict:
        """Get database models information"""
        models = {}
        
        try:
            for model_file in self.project_path.rglob('models.py'):
                try:
                    with open(model_file, 'r') as f:
                        content = f.read()
                        
                    # Extract model class names
                    model_classes = re.findall(r'class\s+(\w+)\s*\([^)]*Model[^)]*\):', content)
                    if model_classes:
                        models[str(model_file.relative_to(self.project_path))] = model_classes
                        
                except Exception as e:
                    logger.warning(f"Could not read model file {model_file}: {e}")
                    
        except Exception as e:
            logger.error(f"Error getting database models: {e}")
        
        return models
    
    def _get_url_patterns(self) -> Dict:
        """Get URL patterns information"""
        urls = {}
        
        try:
            for url_file in self.project_path.rglob('urls.py'):
                try:
                    with open(url_file, 'r') as f:
                        content = f.read()
                        
                    # Extract URL patterns
                    url_patterns = re.findall(r"path\s*\(\s*['\"]([^'\"]*)['\"]", content)
                    if url_patterns:
                        urls[str(url_file.relative_to(self.project_path))] = url_patterns
                        
                except Exception as e:
                    logger.warning(f"Could not read URL file {url_file}: {e}")
                    
        except Exception as e:
            logger.error(f"Error getting URL patterns: {e}")
        
        return urls
    
    def _get_recent_file_changes(self) -> List[Dict]:
        """Get recent file modifications"""
        changes = []
        
        try:
            # Get files modified in the last hour
            from datetime import datetime, timedelta
            recent_time = datetime.now() - timedelta(hours=1)
            
            for file_path in self.project_path.rglob('*.py'):
                try:
                    stat = file_path.stat()
                    if datetime.fromtimestamp(stat.st_mtime) > recent_time:
                        changes.append({
                            'file': str(file_path.relative_to(self.project_path)),
                            'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                        })
                except Exception as e:
                    logger.warning(f"Could not get stats for {file_path}: {e}")
                    
        except Exception as e:
            logger.error(f"Error getting recent changes: {e}")
        
        return changes
    
    def _get_requirements(self) -> List[str]:
        """Get project requirements"""
        requirements = []
        
        req_files = ['requirements.txt', 'requirements/base.txt', 'requirements/development.txt']
        
        for req_file in req_files:
            req_path = self.project_path / req_file
            if req_path.exists():
                try:
                    with open(req_path, 'r') as f:
                        reqs = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                        requirements.extend(reqs)
                except Exception as e:
                    logger.warning(f"Could not read requirements file {req_path}: {e}")
        
        return list(set(requirements))
    
    def _generate_fix_with_claude(self, error_analysis: Dict, project_context: Dict) -> Dict:
        """
        Generate fix using Claude with full context
        """
        try:
            prompt = f"""
You are an expert Django developer tasked with fixing a critical error in a Django project.

**ERROR ANALYSIS:**
- Error Type: {error_analysis['error_type']}
- Error Message: {error_analysis['error_message']}
- Category: {error_analysis['category']}
- Severity: {error_analysis['severity']}
- Affected Files: {error_analysis['affected_files']}

**TRACEBACK:**
{error_analysis['traceback']}

**STDERR OUTPUT:**
{error_analysis['stderr']}

**COMMAND THAT FAILED:**
{error_analysis['command']}

**PROJECT CONTEXT:**
- Installed Apps: {project_context.get('installed_apps', [])}
- Database Models: {project_context.get('database_models', {})}
- URL Patterns: {project_context.get('url_patterns', {})}
- Recent Changes: {project_context.get('recent_changes', [])}
- Requirements: {project_context.get('requirements', [])}

**KEY FILES CONTENT:**
{json.dumps(project_context.get('key_files', {}), indent=2)}

**PROJECT STRUCTURE:**
{json.dumps(project_context.get('project_structure', {}), indent=2)}

**TASK:**
1. Analyze the error thoroughly
2. Identify the root cause
3. Provide a comprehensive fix
4. Suggest preventive measures

**RESPONSE FORMAT:**
{{
    "error_diagnosis": "Detailed explanation of what went wrong",
    "root_cause": "The fundamental issue causing this error",
    "fix_steps": [
        "Step 1: Specific action to take",
        "Step 2: Another specific action",
        "..."
    ],
    "code_changes": {{
        "file_path": {{
            "action": "create|modify|delete",
            "content": "New file content or changes to make",
            "line_numbers": [1, 2, 3] // lines to modify for existing files
        }}
    }},
    "commands_to_run": [
        "python manage.py migrate",
        "python manage.py collectstatic"
    ],
    "auto_fixable": true/false,
    "confidence_level": "high|medium|low",
    "additional_context": "Any additional information that might be helpful",
    "preventive_measures": [
        "How to prevent this error in the future"
    ]
}}

Provide a complete, actionable solution that will definitively fix this error.
"""

            response = self.claude_service.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4000,
                temperature=0.1,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            content = response.content[0].text.strip()
            
            # Parse JSON response
            try:
                fix_data = json.loads(content)
                fix_data['success'] = True
                return fix_data
            except json.JSONDecodeError:
                # Try to extract JSON from markdown
                json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', content)
                if json_match:
                    try:
                        fix_data = json.loads(json_match.group(1))
                        fix_data['success'] = True
                        return fix_data
                    except json.JSONDecodeError:
                        pass
                
                # Fallback to text response
                return {
                    'success': True,
                    'error_diagnosis': 'Could not parse structured response',
                    'fix_steps': [content],
                    'auto_fixable': False,
                    'confidence_level': 'medium'
                }
            
        except Exception as e:
            logger.error(f"Error generating fix with Claude: {e}")
            return {
                'success': False,
                'error': f"Failed to generate fix: {str(e)}"
            }
    
    def _apply_automatic_fixes(self, fix_result: Dict) -> List[Dict]:
        """
        Apply automatic fixes when possible
        """
        applied_fixes = []
        
        if not fix_result.get('auto_fixable', False):
            return applied_fixes
        
        code_changes = fix_result.get('code_changes', {})
        
        for file_path, changes in code_changes.items():
            try:
                full_path = self.project_path / file_path
                action = changes.get('action', 'modify')
                
                if action == 'create':
                    # Create new file
                    full_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(full_path, 'w', encoding='utf-8') as f:
                        f.write(changes['content'])
                    
                    applied_fixes.append({
                        'file': file_path,
                        'action': 'created',
                        'success': True
                    })
                    
                elif action == 'modify':
                    # Modify existing file
                    if full_path.exists():
                        # Backup original
                        backup_path = full_path.with_suffix(full_path.suffix + '.backup')
                        full_path.rename(backup_path)
                        
                        # Write new content
                        with open(full_path, 'w', encoding='utf-8') as f:
                            f.write(changes['content'])
                        
                        applied_fixes.append({
                            'file': file_path,
                            'action': 'modified',
                            'backup': str(backup_path),
                            'success': True
                        })
                    
                elif action == 'delete':
                    # Delete file
                    if full_path.exists():
                        full_path.unlink()
                        applied_fixes.append({
                            'file': file_path,
                            'action': 'deleted',
                            'success': True
                        })
                
            except Exception as e:
                logger.error(f"Error applying fix to {file_path}: {e}")
                applied_fixes.append({
                    'file': file_path,
                    'action': changes.get('action', 'unknown'),
                    'success': False,
                    'error': str(e)
                })
        
        return applied_fixes
    
    def _store_error_history(self, error_analysis: Dict, fix_result: Dict):
        """Store error and fix in history"""
        history_entry = {
            'timestamp': error_analysis['timestamp'],
            'error_analysis': error_analysis,
            'fix_result': fix_result,
            'project_path': str(self.project_path)
        }
        
        self.error_history.append(history_entry)
        
        # Keep only last 100 entries
        if len(self.error_history) > 100:
            self.error_history = self.error_history[-100:]
    
    def get_error_history(self) -> List[Dict]:
        """Get error history"""
        return self.error_history
    
    def capture_command_error(self, command: str, stdout: str, stderr: str, exit_code: int) -> Dict:
        """
        Capture error from command execution
        """
        error_data = {
            'error_type': 'command_execution_error',
            'error_message': f"Command failed with exit code {exit_code}",
            'command': command,
            'stdout': stdout,
            'stderr': stderr,
            'exit_code': exit_code,
            'traceback': stderr  # stderr often contains traceback
        }
        
        return self.capture_and_fix_error(error_data)
    
    def capture_exception_error(self, exception: Exception, context: Dict = None) -> Dict:
        """
        Capture error from Python exception
        """
        error_data = {
            'error_type': type(exception).__name__,
            'error_message': str(exception),
            'traceback': ''.join(traceback.format_exception(type(exception), exception, exception.__traceback__)),
            'context': context or {}
        }
        
        return self.capture_and_fix_error(error_data)