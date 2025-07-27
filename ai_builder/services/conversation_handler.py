import os
import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional
from django.utils import timezone
from .claude_service import ClaudeService
from .file_merger import CodeMerger
from .container_service import ContainerService
from ..models import (
    Project, ProjectFile, ChatMessage, ChatThread, 
    ProjectSession, ErrorLog, UsageAnalytics, UserProfile
)

logger = logging.getLogger(__name__)


class ConversationHandler:
    """
    Enhanced conversational workflow with persistent threading, error handling, and analytics.
    Provides continuity across sessions and intelligent context management.
    """
    
    def __init__(self, project: Project = None, container_service: ContainerService = None, user=None):
        self.project = project
        self.container_service = container_service or ContainerService()
        self.claude_service = ClaudeService(user=user)
        self.code_merger = CodeMerger()
        self.chat_thread = None
        self.current_session = None
        self.user = user
        
    def handle_message(self, project_id: str, message: str, user=None, 
                      is_error_report: bool = False, error_type: str = '', 
                      error_source: str = '') -> Dict:
        """
        Enhanced message handling with persistent threading and analytics
        """
        start_time = time.time()
        
        try:
            # Get or set project
            if not self.project and project_id:
                try:
                    self.project = Project.objects.get(id=project_id)
                except Project.DoesNotExist:
                    return {'error': 'Project not found', 'success': False}
            
            if not self.project:
                return {'error': 'No project specified', 'success': False}
            
            # Get or create chat thread
            self.chat_thread = self._get_or_create_thread()
            
            # Track user analytics
            if user:
                self._track_action(user, 'ai_generation', {
                    'message_length': len(message),
                    'is_error_report': is_error_report,
                    'error_type': error_type
                })
            
            # Check token limits
            if user and not self._check_token_limits(user, len(message) * 2):
                return {
                    'error': 'Token limit exceeded for this billing period',
                    'success': False
                }
            
            # Save user message
            user_message = ChatMessage.objects.create(
                project=self.project,
                thread=self.chat_thread,
                role='user',
                content=message,
                message_type='error_report' if is_error_report else 'normal',
                is_error_report=is_error_report,
                error_type=error_type,
                error_source=error_source
            )
            
            # Get conversation context
            context = self._get_conversation_context()
            
            # Generate AI response
            ai_response = self._generate_ai_response(message, context, is_error_report)
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Save AI response
            ai_message = ChatMessage.objects.create(
                project=self.project,
                thread=self.chat_thread,
                role='assistant',
                content=ai_response.get('content', ''),
                processing_time=processing_time,
                tokens_used=ai_response.get('tokens_used', 0)
            )
            
            # Update user token usage
            if user and ai_response.get('tokens_used'):
                self._record_token_usage(user, ai_response['tokens_used'])
            
            # Update thread activity
            self.chat_thread.last_activity = timezone.now()
            self.chat_thread.save()
            
            return {
                'success': True,
                'response': ai_response.get('content', ''),
                'message_id': ai_message.id,
                'thread_id': self.chat_thread.thread_id,
                'processing_time': processing_time,
                'tokens_used': ai_response.get('tokens_used', 0)
            }
            
        except Exception as e:
            logger.error(f"Error in handle_message: {e}")
            
            # Log error for analytics
            if user:
                self._track_action(user, 'error_occurred', {
                    'error_message': str(e),
                    'error_type': 'conversation_handler_error'
                }, success=False)
            
            return {
                'success': False,
                'error': str(e),
                'processing_time': time.time() - start_time
            }
    
    def handle_error_report(self, project_id: str, error_data: Dict, user=None) -> Dict:
        """
        Handle error reports with automatic fix suggestions
        """
        try:
            # Log the error
            error_log = ErrorLog.objects.create(
                project_id=project_id,
                session=self.current_session,
                error_type=error_data.get('error_type', 'runtime'),
                error_message=error_data.get('error_message', ''),
                error_traceback=error_data.get('traceback', ''),
                file_path=error_data.get('file_path', ''),
                line_number=error_data.get('line_number'),
                command_executed=error_data.get('command', ''),
                user_action=error_data.get('user_action', '')
            )
            
            # Generate auto-fix suggestion
            fix_prompt = f"""
Error Analysis and Fix Request:

Project: {self.project.name if self.project else 'Unknown'}
Error Type: {error_data.get('error_type', 'Unknown')}
Error Message: {error_data.get('error_message', '')}
File: {error_data.get('file_path', '')}
Line: {error_data.get('line_number', 'Unknown')}

Traceback:
{error_data.get('traceback', '')}

Please analyze this error and provide:
1. Root cause explanation
2. Specific fix instructions  
3. Code changes needed (if applicable)
4. Prevention tips for similar errors

Be concise but thorough in your analysis.
"""
            
            # Get AI fix suggestion
            fix_response = self.handle_message(
                project_id, 
                fix_prompt, 
                user=user, 
                is_error_report=True,
                error_type=error_data.get('error_type', ''),
                error_source=error_data.get('file_path', '')
            )
            
            if fix_response.get('success'):
                error_log.claude_thread_used = self.chat_thread.thread_id
                error_log.tokens_used_for_fix = fix_response.get('tokens_used', 0)
                error_log.save()
            
            return {
                'success': True,
                'error_log_id': error_log.id,
                'fix_suggestion': fix_response.get('response', ''),
                'auto_fix_available': self._can_auto_fix(error_data),
                'tokens_used': fix_response.get('tokens_used', 0)
            }
            
        except Exception as e:
            logger.error(f"Error handling error report: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_or_create_thread(self) -> ChatThread:
        """Get or create persistent chat thread for project"""
        thread, created = ChatThread.objects.get_or_create(
            project=self.project,
            defaults={'is_active': True}
        )
        return thread
    
    def _get_conversation_context(self) -> Dict:
        """Get conversation context with threading support"""
        if not self.chat_thread:
            return {}
        
        # Get recent messages from this thread
        recent_messages = ChatMessage.objects.filter(
            thread=self.chat_thread,
            project=self.project
        ).order_by('-timestamp')[:self.chat_thread.context_length]
        
        # Get project context
        project_context = self._get_project_context()
        
        return {
            'thread_id': self.chat_thread.thread_id,
            'recent_messages': [
                {
                    'role': msg.role,
                    'content': msg.content,
                    'timestamp': msg.timestamp.isoformat(),
                    'message_type': msg.message_type
                }
                for msg in reversed(recent_messages)
            ],
            'project_context': project_context,
            'conversation_length': self.chat_thread.messages.count()
        }
    
    def _generate_ai_response(self, message: str, context: Dict, is_error_report: bool = False) -> Dict:
        """Generate AI response with enhanced context"""
        
        # Build enhanced prompt with conversation context
        system_prompt = self._build_system_prompt(context, is_error_report)
        
        try:
            response = self.claude_service.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4000,
                temperature=0.1 if is_error_report else 0.3,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": message}
                ]
            )
            
            return {
                'content': response.content[0].text,
                'tokens_used': response.usage.input_tokens + response.usage.output_tokens
            }
            
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            return {
                'content': f"I encountered an error while processing your request: {str(e)}",
                'tokens_used': 0
            }
    
    def _build_system_prompt(self, context: Dict, is_error_report: bool = False) -> str:
        """Build enhanced system prompt with conversation context"""
        
        base_prompt = """You are an expert Django developer assistant working on a specific project. 
You have access to the full conversation history and project context.

Project Context:
"""
        
        if context.get('project_context'):
            project_info = context['project_context']
            base_prompt += f"""
- Project: {project_info.get('project_name', 'Unknown')}
- Django App: {project_info.get('main_app_name', 'main')}
- Files: {project_info.get('file_count', 0)} files
- Models: {', '.join(project_info.get('existing_models', []))}
- Views: {', '.join(project_info.get('existing_views', []))}
"""
        
        if context.get('recent_messages'):
            base_prompt += f"\nRecent Conversation ({len(context['recent_messages'])} messages):\n"
            for msg in context['recent_messages'][-5:]:  # Last 5 messages for context
                base_prompt += f"- {msg['role'].title()}: {msg['content'][:100]}...\n"
        
        if is_error_report:
            base_prompt += """
IMPORTANT: This is an error report. Focus on:
1. Identifying the root cause
2. Providing specific, actionable fix instructions
3. Explaining why the error occurred
4. Suggesting prevention measures
"""
        else:
            base_prompt += """
Provide helpful, accurate responses based on the conversation context.
When suggesting code changes, be specific and consider the existing project structure.
"""
        
        return base_prompt
    
    def _check_token_limits(self, user, estimated_tokens: int) -> bool:
        """Check if user can use the estimated tokens"""
        try:
            profile = UserProfile.objects.get(user=user)
            return profile.can_use_tokens(estimated_tokens)
        except UserProfile.DoesNotExist:
            # Create profile with default limits
            profile = UserProfile.objects.create(user=user)
            return profile.can_use_tokens(estimated_tokens)
    
    def _record_token_usage(self, user, tokens_used: int):
        """Record token usage for user"""
        try:
            profile = UserProfile.objects.get(user=user)
            profile.use_tokens(tokens_used)
            profile.total_ai_requests += 1
            profile.save()
        except UserProfile.DoesNotExist:
            profile = UserProfile.objects.create(
                user=user,
                total_tokens_used=tokens_used,
                monthly_tokens_used=tokens_used,
                total_ai_requests=1
            )
    
    def _track_action(self, user, action_type: str, action_data: Dict, 
                     success: bool = True, response_time_ms: int = None):
        """Track user action for analytics"""
        try:
            UsageAnalytics.objects.create(
                user=user,
                project=self.project,
                session=self.current_session,
                action_type=action_type,
                action_data=action_data,
                success=success,
                response_time_ms=response_time_ms
            )
        except Exception as e:
            logger.error(f"Error tracking action: {e}")
    
    def _can_auto_fix(self, error_data: Dict) -> bool:
        """Determine if error can be automatically fixed"""
        auto_fixable_errors = [
            'syntax error',
            'indentation error', 
            'missing import',
            'undefined variable',
            'missing comma',
            'missing colon'
        ]
        
        error_msg = error_data.get('error_message', '').lower()
        return any(pattern in error_msg for pattern in auto_fixable_errors)
    
    def resume_thread(self, thread_id: str, from_message_id: str = None) -> Dict:
        """Resume conversation from a specific thread and optionally a specific message"""
        try:
            self.chat_thread = ChatThread.objects.get(
                thread_id=thread_id,
                project=self.project
            )
            
            if from_message_id:
                messages = ChatMessage.objects.filter(
                    thread=self.chat_thread,
                    id__gte=from_message_id
                ).order_by('timestamp')
            else:
                messages = ChatMessage.objects.filter(
                    thread=self.chat_thread
                ).order_by('-timestamp')[:self.chat_thread.context_length]
            
            return {
                'success': True,
                'thread_id': thread_id,
                'messages': [
                    {
                        'id': msg.id,
                        'role': msg.role,
                        'content': msg.content,
                        'timestamp': msg.timestamp.isoformat(),
                        'message_type': msg.message_type
                    }
                    for msg in messages
                ],
                'message': f'Resumed conversation with {messages.count()} messages in context'
            }
            
        except ChatThread.DoesNotExist:
            return {
                'success': False,
                'error': f'Thread {thread_id} not found for this project'
            }
        except Exception as e:
            logger.error(f"Error resuming thread: {e}")
            return {
                'success': False,
                'error': str(e)
            }
        
    def handle_conversation_request(self, user_prompt: str) -> Dict:
        """
        Handle a conversational request from the user.
        Analyzes the request type and processes accordingly.
        """
        try:
            logger.info(f"Starting conversation request: {user_prompt[:50]}...")
            
            # Get project context
            project_context = self._get_project_context()
            logger.info(f"Got project context for: {project_context.get('project_name', 'Unknown')}")
            
            # Analyze request type
            request_analysis = self._analyze_request_type(user_prompt, project_context)
            logger.info(f"Request analysis result: {request_analysis.get('type', 'unknown')}")
            
            if request_analysis['type'] == 'new_feature':
                logger.info("Routing to _handle_new_feature")
                return self._handle_new_feature(user_prompt, project_context)
            elif request_analysis['type'] == 'modify_existing':
                logger.info("Routing to _handle_modification")
                return self._handle_modification(user_prompt, project_context, request_analysis)
            elif request_analysis['type'] == 'add_model':
                logger.info("Routing to _handle_add_model")
                return self._handle_add_model(user_prompt, project_context)
            elif request_analysis['type'] == 'enhance_existing':
                logger.info("Routing to _handle_enhancement")
                return self._handle_enhancement(user_prompt, project_context, request_analysis)
            else:
                logger.info("Routing to _handle_general_request")
                return self._handle_general_request(user_prompt, project_context)
                
        except Exception as e:
            logger.error(f"Error handling conversation request: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return {
                'success': False,
                'error': str(e),
                'message': f"Error processing request: {str(e)}"
            }
    
    def _get_project_context(self) -> Dict:
        """Get comprehensive project context including files, models, and structure."""
        
        # Get all project files
        project_files = ProjectFile.objects.filter(project=self.project)
        
        # Get recent chat history for context
        recent_messages = ChatMessage.objects.filter(
            project=self.project
        ).order_by('-created_at')[:10]
        
        # Analyze existing models
        existing_models = self._extract_existing_models(project_files)
        
        # Analyze existing views
        existing_views = self._extract_existing_views(project_files)
        
        # Analyze existing URLs
        existing_urls = self._extract_existing_urls(project_files)
        
        return {
            'project_name': self.project.name,
            'project_id': str(self.project.id),
            'django_project_created': self.project.django_project_created,
            'main_app_name': self.project.main_app_name or 'main',
            'files': [{'path': f.path, 'type': f.file_type, 'size': f.size} for f in project_files],
            'file_count': project_files.count(),
            'existing_models': existing_models,
            'existing_views': existing_views,
            'existing_urls': existing_urls,
            'recent_conversation': [
                {'role': m.role, 'content': m.content[:200]} 
                for m in recent_messages
            ],
            'apps_structure': self._get_apps_structure(project_files)
        }
    
    def _analyze_request_type(self, user_prompt: str, context: Dict) -> Dict:
        """Analyze what type of request this is and what needs to be done."""
        
        # Quick pattern matching for common requests
        prompt_lower = user_prompt.lower()
        
        # Check for view/visit tracking requests
        if any(keyword in prompt_lower for keyword in ['view', 'visit', 'track', 'count']):
            if any(keyword in prompt_lower for keyword in ['model', 'add', 'create']):
                return {
                    'type': 'add_model',
                    'confidence': 0.9,
                    'target_files': [f"{context['main_app_name']}/models.py", f"{context['main_app_name']}/admin.py"],
                    'target_models': context['existing_models'],
                    'action_needed': 'create',
                    'description': 'Add view tracking model',
                    'requires_new_model': True,
                    'requires_migration': True,
                    'affected_components': ['models', 'admin']
                }
        
        # Check for model-related requests
        if 'model' in prompt_lower and any(keyword in prompt_lower for keyword in ['add', 'create', 'new']):
            return {
                'type': 'add_model',
                'confidence': 0.8,
                'target_files': [f"{context['main_app_name']}/models.py"],
                'action_needed': 'create',
                'description': 'Add new model',
                'requires_new_model': True,
                'requires_migration': True,
                'affected_components': ['models', 'admin']
            }
        
        # Use AI analysis for complex requests
        analysis_prompt = f"""
Analyze this user request in the context of an existing Django project and determine what type of action is needed.

USER REQUEST: "{user_prompt}"

EXISTING PROJECT CONTEXT:
- Project: {context['project_name']}
- Main App: {context['main_app_name']}
- Files: {len(context['files'])} files
- Existing Models: {context['existing_models']}
- Existing Views: {context['existing_views']}
- Recent Conversation: {context['recent_conversation'][:3]}

Analyze the request and respond with JSON:
{{
  "type": "new_feature|modify_existing|add_model|enhance_existing|general",
  "confidence": 0.0-1.0,
  "target_files": ["file1.py", "file2.py"],
  "target_models": ["Model1", "Model2"],
  "action_needed": "create|modify|enhance|delete",
  "description": "Brief description of what needs to be done",
  "requires_new_model": true/false,
  "requires_migration": true/false,
  "affected_components": ["models", "views", "urls", "templates", "admin"]
}}

Examples:
- "add a model that shows view count" → type: "add_model"
- "modify the Post model to include tags" → type: "modify_existing", target_models: ["Post"]
- "add authentication to blog posts" → type: "enhance_existing"
- "create a comment system" → type: "new_feature"
- "fix the homepage view" → type: "modify_existing", target_files: ["views.py"]
"""
        
        try:
            response = self.claude_service.client.messages.create(
                model="claude-opus-4-20250514",
                max_tokens=1000,
                temperature=0.1,
                messages=[
                    {"role": "user", "content": analysis_prompt}
                ]
            )
            
            content = response.content[0].text.strip()
            analysis = self._parse_json_response(content)
            
            # Ensure the analysis has required fields
            if analysis and isinstance(analysis, dict) and 'type' in analysis:
                return analysis
            else:
                return {
                    'type': 'general',
                    'confidence': 0.5,
                    'description': 'General request',
                    'target_files': [],
                    'action_needed': 'enhance',
                    'requires_new_model': False,
                    'requires_migration': False,
                    'affected_components': ['views']
                }
            
        except Exception as e:
            logger.error(f"Error analyzing request type: {e}")
            return {
                'type': 'general',
                'confidence': 0.5,
                'description': f'Error analyzing request: {str(e)}',
                'target_files': [],
                'action_needed': 'enhance',
                'requires_new_model': False,
                'requires_migration': False,
                'affected_components': ['views']
            }
    
    def _parse_json_response(self, content: str) -> Dict:
        """Parse JSON response from AI with fallback strategies."""
        import re
        
        try:
            # Direct JSON parsing
            return json.loads(content)
        except json.JSONDecodeError:
            pass
        
        try:
            # Remove markdown and try again
            cleaned = re.sub(r'```json\s*', '', content)
            cleaned = re.sub(r'```\s*$', '', cleaned.strip())
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass
        
        try:
            # Extract JSON object
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass
        
        logger.error(f"Failed to parse JSON response: {content[:200]}...")
        return {}
    
    def _handle_add_model(self, user_prompt: str, context: Dict) -> Dict:
        """Handle requests to add new models to existing apps."""
        
        # Get existing models.py content
        existing_models_content = ""
        existing_admin_content = ""
        
        try:
            models_file = ProjectFile.objects.filter(
                project=self.project,
                path__endswith='models.py'
            ).first()
            if models_file:
                existing_models_content = models_file.content
        except Exception as e:
            logger.warning(f"Could not find models.py: {e}")
        
        try:
            admin_file = ProjectFile.objects.filter(
                project=self.project,
                path__endswith='admin.py'
            ).first()
            if admin_file:
                existing_admin_content = admin_file.content
        except Exception as e:
            logger.warning(f"Could not find admin.py: {e}")
        
        model_prompt = f"""
Generate Django code to add a new model to an existing Django project based on this request:

USER REQUEST: "{user_prompt}"

EXISTING PROJECT CONTEXT:
- Project: {context['project_name']}
- Main App: {context['main_app_name']}
- Existing Models: {context['existing_models']}
- Existing Files: {len(context['files'])} files

EXISTING MODELS.PY CONTENT:
{existing_models_content}

EXISTING ADMIN.PY CONTENT:
{existing_admin_content}

IMPORTANT REQUIREMENTS:
- Add the new model to the existing models.py file (merge with existing content)
- Create any necessary relationships with existing models
- Update admin.py to register the new model
- If the request is about tracking views/visits, create a comprehensive model that tracks:
  - The item being viewed (ForeignKey to existing model)
  - IP address for unique view tracking
  - Timestamp of view
  - Optional user tracking for registered users
  - Helper methods to count views
- Use correct Django imports
- Ensure the new model integrates well with existing models
- Add helper methods and properties for easy view counting

EXAMPLE: If adding view tracking to a blog Post model, create something like:
```python
class PostView(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='views')
    ip_address = models.GenericIPAddressField()
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        unique_together = ['post', 'ip_address']
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"View of {self.post.title} from {self.ip_address}"

# Also add a property to the Post model:
# @property
# def view_count(self):
#     return self.views.count()
```

Generate the complete updated files with the new model integrated.

Respond with JSON:
{{
  "explanation": "Description of what was added",
  "files": [
    {{
      "path": "{context['main_app_name']}/models.py",
      "content": "Complete updated models.py with new model",
      "action": "modify"
    }},
    {{
      "path": "{context['main_app_name']}/admin.py",
      "content": "Updated admin.py with new model registration",
      "action": "modify"
    }}
  ],
  "commands": [
    "python manage.py makemigrations",
    "python manage.py migrate"
  ]
}}

CRITICAL JSON FORMATTING RULES:
- NEVER use triple quotes inside JSON strings
- Use escaped quotes for quotes inside content  
- Use \\n for line breaks in content strings
- Ensure all JSON is properly formatted and parseable
- Keep content strings as single-line with \\n for line breaks
"""
        
        try:
            response = self.claude_service.client.messages.create(
                model="claude-opus-4-20250514",
                max_tokens=3000,
                temperature=0.1,
                messages=[
                    {"role": "user", "content": model_prompt}
                ]
            )
            
            content = response.content[0].text.strip()
            result = self._parse_json_response(content)
            
            if result and result.get('files'):
                return self._process_file_updates(result, user_prompt)
            else:
                # Fallback: try to create a basic response
                return {
                    'success': False,
                    'error': 'Failed to parse AI response',
                    'message': 'Could not generate model code. Please try rephrasing your request.',
                    'files': [],
                    'commands': []
                }
                
        except Exception as e:
            logger.error(f"Error handling add model: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': f"Error adding model: {str(e)}"
            }
    
    def _handle_modification(self, user_prompt: str, context: Dict, analysis: Dict) -> Dict:
        """Handle requests to modify existing code."""
        
        target_files = analysis.get('target_files', [])
        target_models = analysis.get('target_models', [])
        
        # Get existing file contents - be more flexible with file paths
        existing_files_content = {}
        available_files = []
        
        # Get all project files
        all_project_files = ProjectFile.objects.filter(project=self.project)
        
        for target_file in target_files:
            # Try exact match first
            project_file = all_project_files.filter(path=target_file).first()
            
            # If not found, try partial match
            if not project_file:
                filename = target_file.split('/')[-1]  # Get just the filename
                project_file = all_project_files.filter(path__endswith=filename).first()
            
            if project_file:
                existing_files_content[project_file.path] = project_file.content
                available_files.append(project_file.path)
            else:
                logger.warning(f"File {target_file} not found in project")
        
        # If no specific files found, get common Django files
        if not existing_files_content:
            common_files = ['models.py', 'views.py', 'urls.py', 'admin.py', 'forms.py']
            for common_file in common_files:
                project_file = all_project_files.filter(path__endswith=common_file).first()
                if project_file:
                    existing_files_content[project_file.path] = project_file.content
                    available_files.append(project_file.path)
        
        # If still no files found, use fallback approach
        if not existing_files_content:
            # Get any Django files that exist
            for project_file in all_project_files.filter(path__endswith='.py')[:5]:
                existing_files_content[project_file.path] = project_file.content
                available_files.append(project_file.path)
        
        modification_prompt = f"""
Modify existing Django code based on this request:

USER REQUEST: "{user_prompt}"

EXISTING PROJECT CONTEXT:
- Project: {context['project_name']}
- Available Files: {available_files}
- Target Models: {target_models}
- Action Needed: {analysis.get('action_needed', 'modify')}

EXISTING FILE CONTENTS:
{json.dumps(existing_files_content, indent=2)}

REQUIREMENTS:
- Modify the existing code to fulfill the user's request
- Work with the available files only
- Maintain existing functionality
- Use correct Django imports
- Ensure code is production-ready
- If files are missing, create them with appropriate content

Respond with JSON containing the modified files:
{{
  "explanation": "Description of changes made",
  "files": [
    {{
      "path": "actual_file_path",
      "content": "Complete modified file content",
      "action": "modify"
    }}
  ],
  "commands": ["any necessary commands"]
}}

CRITICAL JSON FORMATTING RULES:
- NEVER use triple quotes inside JSON strings
- Use escaped quotes for quotes inside content
- Use \\n for line breaks in content strings
- Ensure all JSON is properly formatted and parseable
- Keep content strings as single-line with \\n for line breaks
"""
        
        try:
            response = self.claude_service.client.messages.create(
                model="claude-opus-4-20250514",
                max_tokens=3000,
                temperature=0.1,
                messages=[
                    {"role": "user", "content": modification_prompt}
                ]
            )
            
            content = response.content[0].text.strip()
            result = self._parse_json_response(content)
            
            if result and result.get('files'):
                return self._process_file_updates(result, user_prompt)
            else:
                # Fallback: try to create a basic response
                return {
                    'success': False,
                    'error': 'Failed to parse AI response',
                    'message': 'Could not generate modification code. Please try rephrasing your request.',
                    'files': [],
                    'commands': []
                }
                
        except Exception as e:
            logger.error(f"Error handling modification: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': f"Error modifying code: {str(e)}"
            }
    
    def _handle_enhancement(self, user_prompt: str, context: Dict, analysis: Dict) -> Dict:
        """Handle requests to enhance existing functionality."""
        
        enhancement_prompt = f"""
Enhance existing Django project functionality based on this request:

USER REQUEST: "{user_prompt}"

EXISTING PROJECT CONTEXT:
- Project: {context['project_name']}
- Main App: {context['main_app_name']}
- Existing Models: {context['existing_models']}
- Existing Views: {context['existing_views']}
- Affected Components: {analysis.get('affected_components', [])}

REQUIREMENTS:
- Enhance the existing functionality without breaking current features
- Add new features that integrate well with existing code
- Use correct Django imports and best practices
- Create any necessary new files or modify existing ones
- Ensure all enhancements are complete and functional

Respond with JSON containing all necessary file changes:
{{
  "explanation": "Description of enhancements made",
  "files": [
    {{
      "path": "file_path",
      "content": "Complete file content with enhancements",
      "action": "modify|create"
    }}
  ],
  "commands": ["any necessary commands"]
}}

CRITICAL JSON FORMATTING RULES:
- NEVER use triple quotes inside JSON strings
- Use escaped quotes for quotes inside content
- Use \\n for line breaks in content strings
- Ensure all JSON is properly formatted and parseable
- Keep content strings as single-line with \\n for line breaks
"""
        
        try:
            response = self.claude_service.client.messages.create(
                model="claude-opus-4-20250514",
                max_tokens=4000,
                temperature=0.1,
                messages=[
                    {"role": "user", "content": enhancement_prompt}
                ]
            )
            
            content = response.content[0].text.strip()
            result = self._parse_json_response(content)
            
            if result:
                return self._process_file_updates(result, user_prompt)
            else:
                return {
                    'success': False,
                    'error': 'Failed to parse AI response',
                    'message': 'Could not generate enhancement code'
                }
                
        except Exception as e:
            logger.error(f"Error handling enhancement: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': f"Error enhancing functionality: {str(e)}"
            }
    
    def _handle_new_feature(self, user_prompt: str, context: Dict) -> Dict:
        """Handle requests to add completely new features."""
        
        try:
            # Generate code for new feature using Claude directly
            feature_prompt = f"""
Add a new feature to this existing Django project:

USER REQUEST: "{user_prompt}"

PROJECT CONTEXT:
- Project: {context['project_name']}
- Main App: {context['main_app_name']}
- Existing Models: {context['existing_models']}
- Existing Views: {context['existing_views']}

Create the necessary code for this new feature. Keep it simple and functional.
Generate only the essential files needed.

Respond with JSON:
{{
  "files": [
    {{
      "path": "main/models.py",
      "content": "# New model code here"
    }}
  ],
  "explanation": "Brief explanation of what was added"
}}
"""
            
            response = self.claude_service.client.messages.create(
                model="claude-opus-4-20250514",
                max_tokens=4000,
                temperature=0.1,
                messages=[
                    {"role": "user", "content": feature_prompt}
                ]
            )
            
            ai_content = response.content[0].text.strip()
            
            # Try to parse the response
            try:
                import json
                result = json.loads(ai_content)
                
                return {
                    'success': True,
                    'message': result.get('explanation', f"Added new feature: {user_prompt[:100]}..."),
                    'processing_type': 'new_feature',
                    'files': result.get('files', []),
                    'commands': []
                }
            except json.JSONDecodeError:
                return {
                    'success': True,
                    'message': f"Added new feature: {user_prompt[:100]}...",
                    'processing_type': 'new_feature',
                    'files': [],
                    'commands': []
                }
                
        except Exception as e:
            logger.error(f"Error handling new feature: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': f"Error adding new feature: {str(e)}"
            }
    
    def _handle_general_request(self, user_prompt: str, context: Dict) -> Dict:
        """Handle general requests that don't fit other categories."""
        
        # Instead of using viewset directly, use the SmartProjectGenerator
        try:
            from .smart_project_generator import SmartProjectGenerator
            
            # Get the container service projects directory
            projects_dir = self.container_service.projects_dir
            generator = SmartProjectGenerator(projects_dir, user=self.user)
            
            # Generate a simple enhancement
            simple_prompt = f"""
Enhance the existing Django project based on this request:

USER REQUEST: "{user_prompt}"

PROJECT CONTEXT:
- Project: {context['project_name']}
- Existing Models: {context['existing_models']}
- Main App: {context['main_app_name']}

Generate simple improvements or additions. Keep it basic and functional.
"""
            
            # Use the code generation part of smart generator
            response = self.claude_service.client.messages.create(
                model="claude-opus-4-20250514",
                max_tokens=4000,
                temperature=0.1,
                messages=[
                    {"role": "user", "content": simple_prompt}
                ]
            )
            
            ai_content = response.content[0].text.strip()
            
            # Return a simple success response
            return {
                'success': True,
                'message': f"Processed your request: {user_prompt[:100]}...",
                'processing_type': 'general_enhancement',
                'files': [],
                'commands': []
            }
            
        except Exception as e:
            logger.error(f"Error handling general request: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': f"Error processing request: {str(e)}"
            }
    
    def _process_file_updates(self, result: Dict, user_prompt: str) -> Dict:
        """Process file updates by merging with existing files or creating new ones."""
        
        saved_files = []
        merge_conflicts = []
        
        try:
            for file_info in result.get('files', []):
                file_path = file_info['path']
                new_content = file_info['content']
                action = file_info.get('action', 'create')
                
                # Check if file exists - try flexible matching
                existing_file = None
                
                # Try exact match first
                try:
                    existing_file = ProjectFile.objects.get(
                        project=self.project, 
                        path=file_path
                    )
                except ProjectFile.DoesNotExist:
                    # Try partial match by filename
                    filename = file_path.split('/')[-1]
                    existing_file = ProjectFile.objects.filter(
                        project=self.project,
                        path__endswith=filename
                    ).first()
                
                if existing_file:
                    # Update existing file
                    if action == 'modify':
                        # For models.py, use smarter merging for view tracking
                        if file_path.endswith('models.py') and 'view' in user_prompt.lower():
                            # Use the new content directly for model additions
                            existing_file.content = new_content
                            existing_file.is_ai_generated = True
                            existing_file.ai_merge_status = 'enhanced'
                            existing_file.save()
                        else:
                            # Merge content with existing file
                            merge_result = self.code_merger.merge_file_content(
                                existing_file.content,
                                new_content,
                                file_path
                            )
                            
                            existing_file.content = merge_result['merged_content']
                            existing_file.is_ai_generated = True
                            existing_file.ai_merge_status = 'merged' if merge_result['success'] else 'conflict'
                            existing_file.save()
                            
                            if merge_result['conflicts']:
                                merge_conflicts.extend([
                                    f"{existing_file.path}: {conflict}" 
                                    for conflict in merge_result['conflicts']
                                ])
                    else:
                        # Update existing file
                        existing_file.content = new_content
                        existing_file.is_ai_generated = True
                        existing_file.ai_merge_status = 'updated'
                        existing_file.save()
                    
                    saved_files.append({
                        'path': existing_file.path,
                        'action': action,
                        'status': 'updated'
                    })
                    
                    # Save to filesystem with correct path
                    self.container_service.save_file_content(
                        str(self.project.id),
                        existing_file.path,
                        new_content
                    )
                    
                else:
                    # Create new file
                    project_file = ProjectFile.objects.create(
                        project=self.project,
                        path=file_path,
                        content=new_content,
                        file_type=file_path.split('.')[-1] if '.' in file_path else 'txt',
                        is_ai_generated=True,
                        ai_merge_status='new'
                    )
                    
                    saved_files.append({
                        'path': file_path,
                        'action': 'create',
                        'status': 'created'
                    })
                    
                    # Save to filesystem
                    self.container_service.save_file_content(
                        str(self.project.id),
                        file_path,
                        new_content
                    )
            
            # Create a better response message for view tracking
            message = result.get('explanation', 'Successfully processed request')
            if 'view' in user_prompt.lower() and 'track' in user_prompt.lower():
                message = f"✅ Added view tracking functionality! {message}"
            
            return {
                'success': True,
                'message': message,
                'files': saved_files,
                'merge_conflicts': merge_conflicts,
                'commands': result.get('commands', []),
                'processing_type': 'conversational_update'
            }
            
        except Exception as e:
            logger.error(f"Error processing file updates: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': f"Error updating files: {str(e)}"
            }
    
    def _extract_existing_models(self, project_files) -> List[str]:
        """Extract existing model names from project files."""
        models = []
        
        for file in project_files:
            if file.path.endswith('models.py'):
                content = file.content
                # Simple regex to find model definitions
                import re
                model_matches = re.findall(r'class\s+(\w+)\s*\([^)]*Model[^)]*\):', content)
                models.extend(model_matches)
        
        return list(set(models))
    
    def _extract_existing_views(self, project_files) -> List[str]:
        """Extract existing view names from project files."""
        views = []
        
        for file in project_files:
            if file.path.endswith('views.py'):
                content = file.content
                # Simple regex to find view definitions
                import re
                view_matches = re.findall(r'class\s+(\w+)\s*\([^)]*View[^)]*\):', content)
                function_matches = re.findall(r'def\s+(\w+)\s*\([^)]*request[^)]*\):', content)
                views.extend(view_matches + function_matches)
        
        return list(set(views))
    
    def _extract_existing_urls(self, project_files) -> List[str]:
        """Extract existing URL patterns from project files."""
        urls = []
        
        for file in project_files:
            if file.path.endswith('urls.py'):
                content = file.content
                # Simple regex to find URL patterns
                import re
                url_matches = re.findall(r'path\s*\(\s*[\'"]([^\'"]*)[\'"]', content)
                urls.extend(url_matches)
        
        return list(set(urls))
    
    def _get_apps_structure(self, project_files) -> Dict:
        """Get the structure of Django apps in the project."""
        apps = {}
        
        for file in project_files:
            if '/' in file.path:
                app_name = file.path.split('/')[0]
                if app_name not in apps:
                    apps[app_name] = []
                apps[app_name].append(file.path.split('/')[-1])
        
        return apps
    
    def _parse_json_response(self, content: str) -> Dict:
        """Parse JSON response from AI with multiple fallback strategies."""
        
        import re
        
        try:
            # Direct JSON parsing
            return json.loads(content)
        except json.JSONDecodeError:
            pass
        
        try:
            # Remove markdown and try again
            cleaned = re.sub(r'```json\s*', '', content)
            cleaned = re.sub(r'```\s*$', '', cleaned)
            cleaned = cleaned.strip()
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass
        
        # Handle triple quotes in JSON strings
        try:
            # Replace triple quotes with escaped quotes
            fixed_content = content.replace('"""', '\\"\\"\\"')
            return json.loads(fixed_content)
        except json.JSONDecodeError:
            pass
        
        # Advanced parsing for multiline strings with triple quotes
        try:
            # Find and extract file information manually
            files = []
            
            # Pattern to match file objects with triple-quoted content
            file_pattern = r'\{\s*"path"\s*:\s*"([^"]+)"\s*,\s*"content"\s*:\s*"""([^"]*(?:"[^"]*"[^"]*)*?)"""\s*(?:,\s*"action"\s*:\s*"([^"]*)")?\s*\}'
            
            file_matches = re.findall(file_pattern, content, re.DOTALL)
            
            for match in file_matches:
                path = match[0]
                file_content = match[1]
                action = match[2] if match[2] else "modify"
                
                # Clean up the content
                file_content = file_content.replace('\\"', '"')  # Fix escaped quotes
                file_content = file_content.strip()
                
                files.append({
                    "path": path,
                    "content": file_content,
                    "action": action
                })
            
            # Extract explanation
            explanation_match = re.search(r'"explanation"\s*:\s*"([^"]*)"', content)
            explanation = explanation_match.group(1) if explanation_match else "Generated code successfully"
            
            # Extract commands
            commands_match = re.search(r'"commands"\s*:\s*\[(.*?)\]', content, re.DOTALL)
            commands = []
            if commands_match:
                commands_content = commands_match.group(1)
                command_matches = re.findall(r'"([^"]*)"', commands_content)
                commands = command_matches
            
            if not commands:
                commands = ["python manage.py makemigrations", "python manage.py migrate"]
            
            if files:
                return {
                    "explanation": explanation,
                    "files": files,
                    "commands": commands
                }
            
        except Exception as e:
            logger.error(f"Advanced parsing failed: {e}")
        
        # Extract JSON object with balanced braces
        try:
            start_idx = content.find('{')
            if start_idx != -1:
                brace_count = 0
                end_idx = -1
                in_string = False
                escape_next = False
                
                for i, char in enumerate(content[start_idx:], start_idx):
                    if escape_next:
                        escape_next = False
                        continue
                    
                    if char == '\\':
                        escape_next = True
                        continue
                    
                    if char == '"' and not escape_next:
                        in_string = not in_string
                    elif not in_string:
                        if char == '{':
                            brace_count += 1
                        elif char == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                end_idx = i
                                break
                
                if end_idx != -1:
                    json_str = content[start_idx:end_idx + 1]
                    # Try to fix triple quotes issue
                    json_str = re.sub(r'"""\s*([^"]*(?:"[^"]*"[^"]*)*?)\s*"""', r'"\1"', json_str, flags=re.DOTALL)
                    return json.loads(json_str)
        except json.JSONDecodeError:
            pass
        
        # Last resort: manual extraction
        try:
            explanation_match = re.search(r'"explanation"\s*:\s*"([^"]*)"', content)
            explanation = explanation_match.group(1) if explanation_match else "Generated code successfully"
            
            return {
                "explanation": explanation,
                "files": [],
                "commands": ["python manage.py makemigrations", "python manage.py migrate"]
            }
            
        except Exception as e:
            logger.error(f"All JSON parsing strategies failed: {e}")
            logger.error(f"Content preview: {content[:500]}...")
            return {}