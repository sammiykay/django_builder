import json
import os
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

from django.conf import settings
from ..models import Project, ProjectFile, ChatMessage, ChatThread
from .claude_service import ClaudeService
from .container_service import ContainerService

logger = logging.getLogger(__name__)

class ConversationService:
    """
    Handles conversational AI workflow with full project context and error fixing capabilities.
    Similar to Bolt.ai - maintains conversation history and can fix errors automatically.
    """
    
    def __init__(self):
        self.claude_service = ClaudeService()
        self.container_service = ContainerService()
    
    def handle_conversation(
        self, 
        project: Project, 
        chat_thread: ChatThread,
        user_message: str,
        is_error_report: bool = False,
        error_type: str = ""
    ) -> Dict[str, Any]:
        """
        Main conversation handler with full project context and error fixing.
        
        Args:
            project: The Django project instance
            chat_thread: The conversation thread
            user_message: User's message/request
            is_error_report: Whether this is an error report
            error_type: Type of error if applicable
            
        Returns:
            Dict containing response, files modified, and suggestions
        """
        try:
            # Build comprehensive project context
            project_context = self._build_project_context(project)
            
            # Get conversation history
            conversation_history = self._get_conversation_history(chat_thread)
            
            # Determine the type of request and appropriate handler
            if is_error_report:
                return self._handle_error_report(
                    project, project_context, conversation_history, 
                    user_message, error_type
                )
            else:
                return self._handle_general_request(
                    project, project_context, conversation_history, user_message
                )
                
        except Exception as e:
            logger.error(f"Conversation handling failed: {e}")
            return {
                'message': f"I encountered an error while processing your request: {str(e)}",
                'files_modified': [],
                'code_changes': {},
                'suggestions': [],
                'error_fixed': False
            }
    
    def _build_project_context(self, project: Project) -> Dict[str, Any]:
        """Build comprehensive context about the project for Claude"""
        
        # Get project files with content
        project_files = ProjectFile.objects.filter(project=project)
        
        # Categorize files for better context
        models_files = []
        views_files = []
        templates_files = []
        other_files = []
        
        for file in project_files:
            file_info = {
                'path': file.path,
                'content': file.content[:2000],  # Limit content to avoid token overflow
                'type': file.file_type,
                'is_ai_generated': file.is_ai_generated,
                'size': len(file.content)
            }
            
            if 'models.py' in file.path:
                models_files.append(file_info)
            elif 'views.py' in file.path:
                views_files.append(file_info)
            elif 'templates' in file.path:
                templates_files.append(file_info)
            else:
                other_files.append(file_info)
        
        # Get recent command executions
        recent_executions = project.executions.order_by('-executed_at')[:5]
        execution_history = [
            {
                'command': exec.command,
                'output': exec.output[:500],  # Limit output
                'error': exec.error_output[:500],
                'exit_code': exec.exit_code,
                'executed_at': exec.executed_at.isoformat()
            }
            for exec in recent_executions
        ]
        
        return {
            'project_name': project.name,
            'project_description': project.description,
            'project_type': project.project_type,
            'complexity_level': project.complexity_level,
            'django_version': project.django_version,
            'main_app_name': project.main_app_name,
            'is_running': project.is_running,
            'container_port': project.container_port,
            'files': {
                'models': models_files,
                'views': views_files,
                'templates': templates_files,
                'other': other_files
            },
            'total_files': project_files.count(),
            'recent_executions': execution_history,
            'key_features': project.key_features or [],
            'generated_features': project.generated_features or []
        }
    
    def _get_conversation_history(self, chat_thread: ChatThread) -> List[Dict[str, str]]:
        """Get recent conversation history for context"""
        recent_messages = ChatMessage.objects.filter(
            thread=chat_thread
        ).order_by('-timestamp')[:chat_thread.context_length]
        
        history = []
        for msg in reversed(recent_messages):  # Reverse to get chronological order
            history.append({
                'role': msg.role,
                'content': msg.content,
                'message_type': msg.message_type,
                'timestamp': msg.timestamp.isoformat(),
                'files_modified': msg.files_modified
            })
        
        return history
    
    def _handle_error_report(
        self, 
        project: Project,
        project_context: Dict[str, Any],
        conversation_history: List[Dict[str, str]],
        error_message: str,
        error_type: str
    ) -> Dict[str, Any]:
        """Handle error reports with automatic fixing"""
        
        # Analyze the error and determine possible solutions
        error_analysis_prompt = self._build_error_analysis_prompt(
            project_context, conversation_history, error_message, error_type
        )
        
        try:
            # Get error analysis from Claude
            analysis_response = self.claude_service.client.messages.create(
                model="claude-3-7-sonnet-20250219",
                max_tokens=2000,
                temperature=0.1,
                messages=[{"role": "user", "content": error_analysis_prompt}]
            )
            
            analysis = analysis_response.content[0].text.strip()
            
            # Check if Claude suggests code fixes
            if "```" in analysis and ("python" in analysis.lower() or "django" in analysis.lower()):
                # Extract and apply code fixes
                fixes_applied = self._apply_code_fixes(project, analysis)
                
                return {
                    'message': f"Error analyzed and fixes applied:\n\n{analysis}",
                    'files_modified': fixes_applied.get('files_modified', []),
                    'code_changes': fixes_applied.get('code_changes', {}),
                    'suggestions': self._extract_suggestions(analysis),
                    'error_fixed': len(fixes_applied.get('files_modified', [])) > 0
                }
            else:
                # Provide analysis without code changes
                return {
                    'message': analysis,
                    'files_modified': [],
                    'code_changes': {},
                    'suggestions': self._extract_suggestions(analysis),
                    'error_fixed': False
                }
                
        except Exception as e:
            logger.error(f"Error analysis failed: {e}")
            return {
                'message': f"I understand you're experiencing an error, but I had trouble analyzing it: {str(e)}",
                'files_modified': [],
                'code_changes': {},
                'suggestions': ["Try checking the Django documentation", "Review recent code changes"],
                'error_fixed': False
            }
    
    def _handle_general_request(
        self,
        project: Project,
        project_context: Dict[str, Any],
        conversation_history: List[Dict[str, str]],
        user_message: str
    ) -> Dict[str, Any]:
        """Handle general conversation requests"""
        
        # Build context-aware prompt
        general_prompt = self._build_general_conversation_prompt(
            project_context, conversation_history, user_message
        )
        
        try:
            # Get response from Claude
            response = self.claude_service.client.messages.create(
                model="claude-3-7-sonnet-20250219",
                max_tokens=2000,
                temperature=0.2,
                messages=[{"role": "user", "content": general_prompt}]
            )
            
            ai_response = response.content[0].text.strip()
            
            # Check if response includes code that should be applied
            if "```" in ai_response and any(keyword in user_message.lower() for keyword in 
                ['add', 'create', 'implement', 'build', 'make', 'generate']):
                
                # Apply code changes if user is requesting implementation
                code_changes = self._apply_code_fixes(project, ai_response)
                
                return {
                    'message': ai_response,
                    'files_modified': code_changes.get('files_modified', []),
                    'code_changes': code_changes.get('code_changes', {}),
                    'suggestions': self._extract_suggestions(ai_response),
                    'error_fixed': False
                }
            else:
                # Just conversational response
                return {
                    'message': ai_response,
                    'files_modified': [],
                    'code_changes': {},
                    'suggestions': self._extract_suggestions(ai_response),
                    'error_fixed': False
                }
                
        except Exception as e:
            logger.error(f"General conversation failed: {e}")
            return {
                'message': f"I had trouble processing your request: {str(e)}",
                'files_modified': [],
                'code_changes': {},
                'suggestions': [],
                'error_fixed': False
            }
    
    def _build_error_analysis_prompt(
        self,
        project_context: Dict[str, Any],
        conversation_history: List[Dict[str, str]],
        error_message: str,
        error_type: str
    ) -> str:
        """Build prompt for error analysis"""
        
        context_summary = self._format_project_context(project_context)
        history_summary = self._format_conversation_history(conversation_history)
        
        return f"""
You are an expert Django developer helping debug and fix errors in a Django project.

PROJECT CONTEXT:
{context_summary}

RECENT CONVERSATION:
{history_summary}

ERROR REPORT:
Type: {error_type}
Message: {error_message}

Please analyze this error and provide:
1. Root cause analysis
2. Step-by-step solution
3. Code fixes if needed (use proper code blocks with file paths)
4. Prevention suggestions

If you can provide code fixes, use this format:
```python
# File: path/to/file.py
# Action: create/update/fix
[code here]
```

Focus on practical, actionable solutions that will resolve the error.
"""
    
    def _build_general_conversation_prompt(
        self,
        project_context: Dict[str, Any],
        conversation_history: List[Dict[str, str]],
        user_message: str
    ) -> str:
        """Build prompt for general conversation"""
        
        context_summary = self._format_project_context(project_context)
        history_summary = self._format_conversation_history(conversation_history)
        
        return f"""
You are an expert Django developer assistant working on a specific project.

PROJECT CONTEXT:
{context_summary}

RECENT CONVERSATION:
{history_summary}

USER REQUEST: {user_message}

Please provide helpful assistance based on the project context and conversation history.
If the user is asking you to implement something, provide code using this format:

```python
# File: path/to/file.py
# Action: create/update/add
[code here]
```

Be conversational, helpful, and specific to this Django project.
"""
    
    def _format_project_context(self, context: Dict[str, Any]) -> str:
        """Format project context for prompts"""
        
        files_summary = []
        for category, files in context['files'].items():
            if files:
                files_summary.append(f"- {category.title()}: {len(files)} files")
        
        return f"""
Name: {context['project_name']}
Type: {context['project_type']}
Django Version: {context['django_version']}
Main App: {context['main_app_name']}
Status: {'Running' if context['is_running'] else 'Stopped'}

Files Overview:
{chr(10).join(files_summary)}

Key Features: {', '.join(context['key_features'])}
"""
    
    def _format_conversation_history(self, history: List[Dict[str, str]]) -> str:
        """Format conversation history for prompts"""
        
        if not history:
            return "No previous conversation"
        
        formatted_history = []
        for msg in history[-5:]:  # Last 5 messages
            formatted_history.append(f"{msg['role']}: {msg['content'][:150]}...")
        
        return chr(10).join(formatted_history)
    
    def _apply_code_fixes(self, project: Project, ai_response: str) -> Dict[str, Any]:
        """Extract and apply code fixes from AI response"""
        
        files_modified = []
        code_changes = {}
        
        try:
            # Parse code blocks from AI response
            code_blocks = self._extract_code_blocks(ai_response)
            
            for code_block in code_blocks:
                file_path = code_block.get('file_path')
                action = code_block.get('action', 'update')
                code_content = code_block.get('content')
                
                if file_path and code_content:
                    # Apply the code change
                    success = self._apply_single_code_change(
                        project, file_path, code_content, action
                    )
                    
                    if success:
                        files_modified.append(file_path)
                        code_changes[file_path] = {
                            'action': action,
                            'content': code_content[:500]  # Truncate for response
                        }
            
            return {
                'files_modified': files_modified,
                'code_changes': code_changes
            }
            
        except Exception as e:
            logger.error(f"Code fix application failed: {e}")
            return {
                'files_modified': [],
                'code_changes': {}
            }
    
    def _extract_code_blocks(self, ai_response: str) -> List[Dict[str, str]]:
        """Extract code blocks with file paths from AI response"""
        
        code_blocks = []
        lines = ai_response.split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Look for code block start
            if line.startswith('```'):
                # Find file path and action in comments
                file_path = None
                action = 'update'
                code_lines = []
                
                i += 1
                while i < len(lines) and not lines[i].strip().startswith('```'):
                    code_line = lines[i]
                    
                    # Check for file path comment
                    if code_line.strip().startswith('# File:'):
                        file_path = code_line.split('# File:')[1].strip()
                    elif code_line.strip().startswith('# Action:'):
                        action = code_line.split('# Action:')[1].strip()
                    else:
                        code_lines.append(code_line)
                    
                    i += 1
                
                if file_path and code_lines:
                    code_blocks.append({
                        'file_path': file_path,
                        'action': action,
                        'content': '\n'.join(code_lines)
                    })
            
            i += 1
        
        return code_blocks
    
    def _apply_single_code_change(
        self, 
        project: Project, 
        file_path: str, 
        code_content: str, 
        action: str
    ) -> bool:
        """Apply a single code change to a project file"""
        
        try:
            if action in ['create', 'new']:
                # Create new file
                project_file, created = ProjectFile.objects.update_or_create(
                    project=project,
                    path=file_path,
                    defaults={
                        'content': code_content,
                        'file_type': file_path.split('.')[-1] if '.' in file_path else 'txt',
                        'is_ai_generated': True,
                        'ai_merge_status': 'new'
                    }
                )
            else:
                # Update existing file
                try:
                    project_file = ProjectFile.objects.get(project=project, path=file_path)
                    project_file.original_content = project_file.content
                    project_file.content = code_content
                    project_file.is_ai_generated = True
                    project_file.ai_merge_status = 'merged'
                    project_file.save()
                except ProjectFile.DoesNotExist:
                    # File doesn't exist, create it
                    project_file = ProjectFile.objects.create(
                        project=project,
                        path=file_path,
                        content=code_content,
                        file_type=file_path.split('.')[-1] if '.' in file_path else 'txt',
                        is_ai_generated=True,
                        ai_merge_status='new'
                    )
            
            # Write to filesystem
            self.container_service.save_file_content(
                str(project.id), file_path, code_content
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to apply code change to {file_path}: {e}")
            return False
    
    def _extract_suggestions(self, ai_response: str) -> List[str]:
        """Extract actionable suggestions from AI response"""
        
        suggestions = []
        
        # Look for common suggestion patterns
        suggestion_indicators = [
            "suggest", "recommend", "consider", "you might", "you could",
            "try", "also", "next step", "additionally"
        ]
        
        lines = ai_response.split('\n')
        for line in lines:
            line_lower = line.lower().strip()
            if any(indicator in line_lower for indicator in suggestion_indicators):
                suggestion = line.strip()
                if len(suggestion) > 10 and len(suggestion) < 200:
                    suggestions.append(suggestion)
        
        return suggestions[:5]  # Limit to 5 suggestions