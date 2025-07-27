"""
WebSocket Consumers for Django AI Builder
Provides real-time streaming like Bolt.new using Django Channels
"""

import json
import asyncio
import logging
import threading
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.exceptions import ObjectDoesNotExist

from .models import Project, ProjectFile, ChatMessage, ChatThread
from .services.enhanced_error_handler import EnhancedErrorHandler
from .services.codebase_analyzer import CodebaseAnalyzer
from .services.claude_service import ClaudeService
from .services.container_service import ContainerService
from .services.smart_project_generator import SmartProjectGenerator

logger = logging.getLogger(__name__)


class ProjectGenerationConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time project generation
    Streams live updates during AI project creation
    """
    
    async def connect(self):
        """Handle WebSocket connection"""
        self.project_id = self.scope['url_route']['kwargs']['project_id']
        self.room_group_name = f'project_{self.project_id}'
        
        print(f"📡 WebSocket connection attempt for project: {self.project_id}")
        print(f"📡 User: {self.scope.get('user')}")
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        # For now, accept all connections but check permissions later
        # TODO: Add proper authentication check
        try:
            await self.accept()
            
            # Try to get project for info
            project = await self.get_project()
            project_name = project.name if project else f"Project {self.project_id}"
            
            # Send initial connection message
            await self.send_message({
                'type': 'connection_established',
                'message': f'Connected to {project_name}',
                'project_id': str(self.project_id),
                'timestamp': datetime.now().isoformat()
            })
            
            print(f"📡 WebSocket connected successfully for project: {self.project_id}")
            
        except Exception as e:
            logger.error(f"Error connecting to project WebSocket: {e}")
            print(f"❌ WebSocket connection failed: {e}")
            await self.close()
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'generate_project':
                await self.handle_generate_project(data)
            elif message_type == 'chat_message':
                await self.handle_chat_message(data)
            elif message_type == 'fix_error':
                await self.handle_error_fix(data)
            elif message_type == 'analyze_codebase':
                await self.handle_codebase_analysis(data)
            elif message_type == 'execute_command':
                await self.handle_command_execution(data)
            else:
                await self.send_error('Unknown message type')
                
        except json.JSONDecodeError:
            await self.send_error('Invalid JSON format')
        except Exception as e:
            logger.error(f"Error handling WebSocket message: {e}")
            await self.send_error(f'Error processing message: {str(e)}')
    
    async def handle_generate_project(self, data: Dict):
        """Handle project generation with streaming updates"""
        try:
            user_prompt = data.get('message', '')
            if not user_prompt:
                await self.send_error('Message is required')
                return
            
            project = await self.get_project()
            if not project:
                await self.send_error('Project not found')
                return
            
            # Start generation process
            await self.send_message({
                'type': 'generation_started',
                'message': 'Starting project generation...',
                'status': 'initializing'
            })
            
            # Run generation in background
            asyncio.create_task(self.stream_project_generation(project, user_prompt))
            
        except Exception as e:
            logger.error(f"Error starting project generation: {e}")
            await self.send_error(f'Generation failed: {str(e)}')
    
    async def stream_project_generation(self, project, user_prompt: str):
        """Stream project generation updates"""
        try:
            # Initialize services
            container_service = ContainerService()
            user = self.scope.get('user')
            generator = SmartProjectGenerator(container_service.projects_dir, user=user)
            
            # Update project with prompt
            await self.update_project_with_prompt(project, user_prompt)
            
            # Send status update
            await self.send_message({
                'type': 'status_update',
                'message': 'Analyzing your requirements...',
                'status': 'analyzing'
            })
            
            # Generate project with streaming updates
            async def status_callback(update):
                """Send real-time updates to the frontend"""
                await self.send_message({
                    'type': 'status_update',
                    'message': update.get('message', ''),
                    'status': update.get('status', 'generating'),
                    'progress': update.get('progress', 0)
                })
            
            result = await generator.generate_project_from_prompt_streaming(
                user_prompt,
                str(project.id),
                status_callback=status_callback
            )
            
            if not result.get('success'):
                await self.send_error(f"Generation failed: {result.get('error', 'Unknown error')}")
                return
            
            # Send progress updates for file creation
            await self.send_message({
                'type': 'status_update',
                'message': 'Project structure created! Processing files...',
                'status': 'processing_files'
            })
            
            # Process and save files with progress updates
            await self.process_generated_files(project, container_service)
            
            # Update project status
            await self.update_project_completion(project, result)
            
            # Send completion message
            await self.send_message({
                'type': 'generation_completed',
                'message': 'Project generation completed successfully!',
                'project_structure': {
                    'project_name': result['project_name'],
                    'description': result['description'],
                    'features': result['features'],
                    'tech_stack': result['tech_stack']
                },
                'files_generated': result['files_generated'],
                'api_endpoints': result.get('api_endpoints', []),
                'access_url': result.get('access_url', 'http://localhost:8000')
            })
            
        except Exception as e:
            logger.error(f"Error in project generation stream: {e}")
            await self.send_error(f'Generation error: {str(e)}')
    
    async def process_generated_files(self, project, container_service):
        """Process generated files with progress updates"""
        try:
            project_path = Path(container_service.projects_dir) / str(project.id)
            
            # Count total files
            all_files = list(project_path.rglob('*'))
            total_files = len([f for f in all_files if f.is_file() and not f.name.startswith('.')])
            
            processed_files = 0
            
            # Process each file
            for file_path in all_files:
                if file_path.is_file() and not file_path.name.startswith('.'):
                    try:
                        # Get relative path
                        relative_path = file_path.relative_to(project_path)
                        
                        # Read file content
                        with open(file_path, 'r', encoding='utf-8') as f:
                            file_content = f.read()
                        
                        # Save to database
                        await self.save_project_file(project, str(relative_path), file_content, file_path.suffix)
                        
                        processed_files += 1
                        progress = (processed_files / total_files) * 100
                        
                        # Send progress update
                        await self.send_message({
                            'type': 'file_processed',
                            'file': str(relative_path),
                            'progress': progress,
                            'files_processed': processed_files,
                            'total_files': total_files
                        })
                        
                        # Small delay to make progress visible
                        await asyncio.sleep(0.1)
                        
                    except Exception as e:
                        logger.error(f"Error processing file {file_path}: {e}")
                        
        except Exception as e:
            logger.error(f"Error processing generated files: {e}")
            await self.send_error(f'File processing error: {str(e)}')
    
    async def handle_chat_message(self, data: Dict):
        """Handle chat message with AI"""
        try:
            message = data.get('message', '')
            if not message:
                await self.send_error('Message is required')
                return
            
            project = await self.get_project()
            if not project:
                await self.send_error('Project not found')
                return
            
            # Send thinking status
            await self.send_message({
                'type': 'ai_thinking',
                'message': 'AI is processing your request...'
            })
            
            # Process chat message
            response = await self.process_chat_message(project, message)
            
            # Send response
            await self.send_message({
                'type': 'ai_response',
                'message': response['content'],
                'files_modified': response.get('files_modified', []),
                'suggestions': response.get('suggestions', [])
            })
            
        except Exception as e:
            logger.error(f"Error handling chat message: {e}")
            await self.send_error(f'Chat error: {str(e)}')
    
    async def handle_error_fix(self, data: Dict):
        """Handle error fixing with enhanced error handler"""
        try:
            error_data = data.get('error_data', {})
            if not error_data:
                await self.send_error('Error data is required')
                return
            
            project = await self.get_project()
            if not project:
                await self.send_error('Project not found')
                return
            
            # Send analyzing status
            await self.send_message({
                'type': 'error_analysis_started',
                'message': 'Analyzing error and generating fix...'
            })
            
            # Use enhanced error handler
            container_service = ContainerService()
            project_path = Path(container_service.projects_dir) / str(project.id)
            error_handler = EnhancedErrorHandler(project_path)
            
            # Process error
            fix_result = await asyncio.get_event_loop().run_in_executor(
                None,
                error_handler.capture_and_fix_error,
                error_data
            )
            
            if fix_result.get('success'):
                await self.send_message({
                    'type': 'error_fix_generated',
                    'error_diagnosis': fix_result.get('error_diagnosis', ''),
                    'fix_steps': fix_result.get('fix_steps', []),
                    'code_changes': fix_result.get('code_changes', {}),
                    'auto_fixable': fix_result.get('auto_fixable', False),
                    'confidence_level': fix_result.get('confidence_level', 'medium')
                })
                
                # Apply fixes if auto-fixable
                if fix_result.get('auto_fixable'):
                    await self.send_message({
                        'type': 'applying_fixes',
                        'message': 'Applying automatic fixes...'
                    })
                    
                    applied_fixes = fix_result.get('applied_fixes', [])
                    await self.send_message({
                        'type': 'fixes_applied',
                        'applied_fixes': applied_fixes,
                        'message': f'Applied {len(applied_fixes)} fixes automatically'
                    })
            else:
                await self.send_error(f"Error analysis failed: {fix_result.get('error', 'Unknown error')}")
            
        except Exception as e:
            logger.error(f"Error handling error fix: {e}")
            await self.send_error(f'Error fix failed: {str(e)}')
    
    async def handle_codebase_analysis(self, data: Dict):
        """Handle codebase analysis request"""
        try:
            project = await self.get_project()
            if not project:
                await self.send_error('Project not found')
                return
            
            # Send analyzing status
            await self.send_message({
                'type': 'codebase_analysis_started',
                'message': 'Analyzing codebase structure and patterns...'
            })
            
            # Analyze codebase
            container_service = ContainerService()
            project_path = Path(container_service.projects_dir) / str(project.id)
            analyzer = CodebaseAnalyzer(project_path)
            
            analysis = await asyncio.get_event_loop().run_in_executor(
                None,
                analyzer.analyze_full_codebase
            )
            
            # Send analysis results
            await self.send_message({
                'type': 'codebase_analysis_completed',
                'analysis': {
                    'project_metadata': analysis.get('project_metadata', {}),
                    'django_structure': analysis.get('django_structure', {}),
                    'code_quality': analysis.get('code_quality', {}),
                    'context_summary': analysis.get('context_summary', {})
                },
                'message': 'Codebase analysis completed'
            })
            
        except Exception as e:
            logger.error(f"Error handling codebase analysis: {e}")
            await self.send_error(f'Codebase analysis failed: {str(e)}')
    
    async def handle_command_execution(self, data: Dict):
        """Handle command execution with streaming output"""
        try:
            command = data.get('command', '')
            if not command:
                await self.send_error('Command is required')
                return
            
            project = await self.get_project()
            if not project:
                await self.send_error('Project not found')
                return
            
            # Send execution started
            await self.send_message({
                'type': 'command_execution_started',
                'command': command,
                'message': f'Executing: {command}'
            })
            
            # Execute command
            container_service = ContainerService()
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                container_service.execute_command,
                str(project.id),
                command
            )
            
            # Send execution result
            await self.send_message({
                'type': 'command_execution_completed',
                'command': command,
                'output': result.get('output', ''),
                'error': result.get('error', ''),
                'exit_code': result.get('exit_code', 0),
                'success': result.get('exit_code', 0) == 0
            })
            
        except Exception as e:
            logger.error(f"Error handling command execution: {e}")
            await self.send_error(f'Command execution failed: {str(e)}')
    
    async def send_message(self, message: Dict):
        """Send message to WebSocket"""
        message['timestamp'] = datetime.now().isoformat()
        await self.send(text_data=json.dumps(message))
    
    async def send_error(self, error_message: str):
        """Send error message to WebSocket"""
        await self.send_message({
            'type': 'error',
            'message': error_message
        })
    
    @database_sync_to_async
    def get_project(self):
        """Get project from database"""
        try:
            user = self.scope['user']
            if user.is_anonymous:
                return None
            return Project.objects.get(
                id=self.project_id,
                owner=user
            )
        except (ObjectDoesNotExist, AttributeError, ValueError) as e:
            logger.error(f"Error getting project {self.project_id}: {e}")
            return None
    
    @database_sync_to_async
    def update_project_with_prompt(self, project, user_prompt: str):
        """Update project with user prompt"""
        project.ai_generation_status = 'generating'
        project.last_prompt = user_prompt
        project.save()
        
        # Save user message
        ChatMessage.objects.create(
            project=project,
            role='user',
            content=user_prompt
        )
    
    @database_sync_to_async
    def save_project_file(self, project, file_path: str, content: str, file_extension: str):
        """Save project file to database"""
        ProjectFile.objects.update_or_create(
            project=project,
            path=file_path,
            defaults={
                'content': content,
                'file_type': file_extension.lstrip('.') if file_extension else 'txt',
                'is_ai_generated': True,
                'ai_merge_status': 'new'
            }
        )
    
    @database_sync_to_async
    def update_project_completion(self, project, result: Dict):
        """Update project after completion"""
        project.django_project_created = True
        project.main_app_name = result.get('project_name', 'main')
        project.ai_generation_status = 'completed'
        project.name = result.get('project_name', project.name)
        project.description = result.get('description', project.description)
        project.save()
        
        # Save AI response
        ai_response_content = f"""
Successfully generated a complete Django project: **{result['project_name']}**

**Project Overview:**
- **Description:** {result['description']}
- **Features:** {', '.join(result['features'])}
- **Files Generated:** {result['files_generated']}

**Technology Stack:**
- **Backend:** {', '.join(result['tech_stack']['backend'])}
- **Frontend:** {', '.join(result['tech_stack']['frontend'])}
- **Database:** {result['tech_stack']['database']}

Your project is ready to use at: {result['access_url']}
"""
        
        ChatMessage.objects.create(
            project=project,
            role='assistant',
            content=ai_response_content
        )
    
    @database_sync_to_async
    def process_chat_message(self, project, message: str):
        """Process chat message with AI"""
        # This would integrate with your existing chat logic
        # For now, return a simple response
        return {
            'content': f"I received your message: {message}",
            'files_modified': [],
            'suggestions': []
        }


class ProjectFileWatcher(AsyncWebsocketConsumer):
    """
    WebSocket consumer for watching file changes in real-time
    """
    
    async def connect(self):
        """Handle WebSocket connection"""
        self.project_id = self.scope['url_route']['kwargs']['project_id']
        self.room_group_name = f'project_files_{self.project_id}'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        # Check permission
        try:
            project = await self.get_project()
            if not project:
                await self.close()
                return
                
            await self.accept()
            
            # Send initial file list
            files = await self.get_project_files(project)
            await self.send_message({
                'type': 'file_list',
                'files': files
            })
            
        except Exception as e:
            logger.error(f"Error connecting to file watcher: {e}")
            await self.close()
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Handle incoming messages"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'watch_file':
                await self.handle_watch_file(data)
            elif message_type == 'save_file':
                await self.handle_save_file(data)
            elif message_type == 'get_file_content':
                await self.handle_get_file_content(data)
            
        except Exception as e:
            logger.error(f"Error handling file watcher message: {e}")
            await self.send_error(str(e))
    
    async def handle_watch_file(self, data: Dict):
        """Handle file watching request"""
        file_path = data.get('file_path', '')
        
        # Add file to watched files
        await self.send_message({
            'type': 'file_watched',
            'file_path': file_path,
            'message': f'Now watching {file_path}'
        })
    
    async def handle_save_file(self, data: Dict):
        """Handle file save request"""
        file_path = data.get('file_path', '')
        content = data.get('content', '')
        
        if not file_path:
            await self.send_error('File path is required')
            return
        
        project = await self.get_project()
        if not project:
            await self.send_error('Project not found')
            return
        
        # Save file
        await self.save_project_file(project, file_path, content)
        
        # Notify all watchers
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'file_changed',
                'file_path': file_path,
                'content': content,
                'timestamp': datetime.now().isoformat()
            }
        )
    
    async def handle_get_file_content(self, data: Dict):
        """Handle get file content request"""
        file_path = data.get('file_path', '')
        
        if not file_path:
            await self.send_error('File path is required')
            return
        
        project = await self.get_project()
        if not project:
            await self.send_error('Project not found')
            return
        
        # Get file content
        content = await self.get_file_content(project, file_path)
        
        await self.send_message({
            'type': 'file_content',
            'file_path': file_path,
            'content': content
        })
    
    async def file_changed(self, event):
        """Handle file change event"""
        await self.send_message({
            'type': 'file_changed',
            'file_path': event['file_path'],
            'content': event['content'],
            'timestamp': event['timestamp']
        })
    
    async def send_message(self, message: Dict):
        """Send message to WebSocket"""
        message['timestamp'] = datetime.now().isoformat()
        await self.send(text_data=json.dumps(message))
    
    async def send_error(self, error_message: str):
        """Send error message"""
        await self.send_message({
            'type': 'error',
            'message': error_message
        })
    
    @database_sync_to_async
    def get_project(self):
        """Get project from database"""
        try:
            user = self.scope['user']
            if user.is_anonymous:
                return None
            return Project.objects.get(
                id=self.project_id,
                owner=user
            )
        except (ObjectDoesNotExist, AttributeError, ValueError) as e:
            logger.error(f"Error getting project {self.project_id}: {e}")
            return None
    
    @database_sync_to_async
    def get_project_files(self, project):
        """Get project files list"""
        files = ProjectFile.objects.filter(project=project)
        return [
            {
                'path': f.path,
                'type': f.file_type,
                'size': f.size,
                'modified': f.updated_at.isoformat()
            }
            for f in files
        ]
    
    @database_sync_to_async
    def save_project_file(self, project, file_path: str, content: str):
        """Save project file"""
        ProjectFile.objects.update_or_create(
            project=project,
            path=file_path,
            defaults={
                'content': content,
                'file_type': Path(file_path).suffix.lstrip('.') if '.' in file_path else 'txt'
            }
        )
    
    @database_sync_to_async
    def get_file_content(self, project, file_path: str):
        """Get file content"""
        try:
            file_obj = ProjectFile.objects.get(project=project, path=file_path)
            return file_obj.content
        except ObjectDoesNotExist:
            return ''


class ProjectLogsConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for streaming project logs
    """
    
    async def connect(self):
        """Handle WebSocket connection"""
        self.project_id = self.scope['url_route']['kwargs']['project_id']
        self.room_group_name = f'project_logs_{self.project_id}'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send initial connection message
        await self.send_message({
            'type': 'connection_established',
            'message': f'Connected to logs for project {self.project_id}',
        })
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Handle incoming messages"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'start_streaming':
                await self.handle_start_streaming(data)
            elif message_type == 'stop_streaming':
                await self.handle_stop_streaming(data)
                
        except Exception as e:
            logger.error(f"Error handling logs message: {e}")
            await self.send_error(str(e))
    
    async def handle_start_streaming(self, data: Dict):
        """Start streaming logs"""
        await self.send_message({
            'type': 'streaming_started',
            'message': 'Log streaming started'
        })
    
    async def handle_stop_streaming(self, data: Dict):
        """Stop streaming logs"""
        await self.send_message({
            'type': 'streaming_stopped',
            'message': 'Log streaming stopped'
        })
    
    async def log_message(self, event):
        """Handle log message event"""
        await self.send_message({
            'type': 'log',
            'message': event['message'],
            'level': event.get('level', 'info'),
            'source': event.get('source', 'system')
        })
    
    async def send_message(self, message: Dict):
        """Send message to WebSocket"""
        message['timestamp'] = datetime.now().isoformat()
        await self.send(text_data=json.dumps(message))
    
    async def send_error(self, error_message: str):
        """Send error message"""
        await self.send_message({
            'type': 'error',
            'message': error_message
        })


class ContainerLogsConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for streaming container logs and terminal output
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.container_service = None
        self.streaming_active = False
    
    async def connect(self):
        """Handle WebSocket connection"""
        self.project_id = self.scope['url_route']['kwargs']['project_id']
        self.room_group_name = f'container_logs_{self.project_id}'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        self.container_service = ContainerService()
        
        # Send initial connection message
        await self.send_message({
            'type': 'connection_established',
            'message': f'Connected to container logs for project {self.project_id}',
        })
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection with proper cleanup"""
        self.streaming_active = False
        
        # Clean up any background operations
        if hasattr(self, 'container_service'):
            try:
                # Stop any running containers if needed
                logger.info(f"Cleaning up container operations for project {self.project_id}")
                # Note: We don't force stop here as the container might be legitimately running
            except Exception as e:
                logger.error(f"Error during container cleanup: {e}")
        
        try:
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
        except Exception as e:
            logger.error(f"Error during channel group cleanup: {e}")
        
        logger.info(f"ContainerLogsConsumer disconnected for project {self.project_id}")
    
    async def receive(self, text_data):
        """Handle incoming messages"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            logger.info(f"📨 Container WebSocket received message: {message_type} - {data}")
            print(f"📨 Container WebSocket received message: {message_type} - {data}")
            
            if message_type == 'start_container':
                await self.handle_start_container(data)
            elif message_type == 'stop_container':
                await self.handle_stop_container(data)
            elif message_type == 'execute_command':
                await self.handle_execute_command(data)
            else:
                logger.warning(f"Unknown message type received: {message_type}")
                await self.send_error(f'Unknown message type: {message_type}')
                
        except Exception as e:
            logger.error(f"Error handling container message: {e}")
            await self.send_error(str(e))
    
    async def handle_start_container(self, data: Dict):
        """Start container with streaming logs"""
        try:
            port = data.get('port', 8001)
            
            logger.info(f"🚀 Starting container for project {self.project_id} on port {port}")
            print(f"🚀 Starting container for project {self.project_id} on port {port}")
            
            await self.send_message({
                'type': 'container_starting',
                'message': f'Starting container for project {self.project_id}...'
            })
            
            
            self.streaming_active = True
            
            # Start container with callback for streaming - with interpreter shutdown protection
            def stream_callback(log_text):
                try:
                    import sys
                    import asyncio
                    
                    # Check if interpreter is shutting down
                    if sys.is_finalizing() or not hasattr(self, 'channel_layer'):
                        print(f"📤 Skipping callback due to interpreter shutdown")
                        return
                    
                    print(f"📤 Container log received: {repr(log_text)}")
                    
                    # Store reference to self for async context
                    consumer_self = self
                    
                    # Use async_to_sync with proper exception handling
                    from asgiref.sync import async_to_sync
                    
                    @async_to_sync
                    async def send_via_multiple_methods():
                        try:
                            # Check again if we're shutting down
                            if sys.is_finalizing():
                                print(f"📤 Skipping send due to interpreter shutdown")
                                return False
                                
                            # Method 1: Try direct WebSocket send (bypass channel layer)
                            print(f"📤 METHOD 1: Trying direct WebSocket send")
                            await consumer_self.send_log(log_text)
                            print(f"📤 METHOD 1: Direct WebSocket send successful")
                            
                            # Method 2: Try channel layer (original method)
                            print(f"📤 METHOD 2: Trying channel layer send to group: {consumer_self.room_group_name}")
                            await consumer_self.channel_layer.group_send(
                                consumer_self.room_group_name,
                                {
                                    'type': 'container_log',
                                    'message': log_text
                                }
                            )
                            print(f"📤 METHOD 2: Channel layer send successful")
                            return True
                        except RuntimeError as e:
                            if "cannot schedule new futures after interpreter shutdown" in str(e):
                                print(f"📤 Interpreter shutting down, gracefully skipping callback")
                                return False
                            print(f"❌ Runtime error in send methods: {e}")
                            return False
                        except Exception as e:
                            print(f"❌ Error in send methods: {e}")
                            return False
                    
                    # Execute the send with shutdown protection
                    try:
                        success = send_via_multiple_methods()
                        if not success:
                            print(f"❌ Both send methods failed")
                    except RuntimeError as e:
                        if "cannot schedule new futures after interpreter shutdown" in str(e):
                            print(f"📤 Gracefully handling interpreter shutdown")
                            return
                        raise
                    
                except Exception as e:
                    print(f"❌ Error in stream callback: {e}")
                    logger.error(f"Stream callback error: {e}")
            
            # Run container start in thread
            # Protect against interpreter shutdown
            try:
                result = await asyncio.get_event_loop().run_in_executor(
                    None,
                    self.container_service.start_container,
                    self.project_id,
                    port,
                    stream_callback
                )
            except RuntimeError as e:
                if "cannot schedule new futures after interpreter shutdown" in str(e):
                    logger.info("Gracefully handling interpreter shutdown during container start")
                    return
                raise
            
            if result.get('error'):
                self.streaming_active = False  # Stop streaming on error
                await self.send_error(f"Container start failed: {result['error']}")
            else:
                await self.send_message({
                    'type': 'container_started',
                    'container_id': result.get('container_id'),
                    'port': result.get('port'),
                    'status': result.get('status'),
                    'message': f'Container started successfully on port {result.get("port")}'
                })
                # Keep streaming active for ongoing logs
                
        except Exception as e:
            logger.error(f"Error starting container: {e}")
            await self.send_error(f'Container start error: {str(e)}')
    
    async def handle_stop_container(self, data: Dict):
        """Stop container"""
        try:
            self.streaming_active = False
            
            await self.send_message({
                'type': 'container_stopping',
                'message': f'Stopping container for project {self.project_id}...'
            })
            
            # Stop container
            await asyncio.get_event_loop().run_in_executor(
                None,
                self.container_service.stop_container,
                self.project_id
            )
            
            await self.send_message({
                'type': 'container_stopped',
                'message': 'Container stopped successfully'
            })
                
        except Exception as e:
            logger.error(f"Error stopping container: {e}")
            await self.send_error(f'Container stop error: {str(e)}')
    
    async def handle_execute_command(self, data: Dict):
        """Execute command in container"""
        try:
            command = data.get('command', '')
            if not command:
                await self.send_error('Command is required')
                return
            
            await self.send_message({
                'type': 'command_started',
                'command': command,
                'message': f'Executing: {command}'
            })
            
            # Execute command
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                self.container_service.execute_command,
                self.project_id,
                command
            )
            
            await self.send_message({
                'type': 'command_completed',
                'command': command,
                'output': result.get('output', ''),
                'error': result.get('error', ''),
                'exit_code': result.get('exit_code', 0),
                'success': result.get('success', False)
            })
                
        except Exception as e:
            logger.error(f"Error executing command: {e}")
            await self.send_error(f'Command execution error: {str(e)}')
    

    async def send_log(self, log_text: str):
        """Send log message"""
        print(f"📡 Sending log to WebSocket: {log_text.strip()}")
        message = {
            'type': 'log',
            'message': log_text,
            'source': 'container'
        }
        print(f"📡 Message being sent: {message}")
        await self.send_message(message)
        print(f"📡 Message sent successfully via send_message")
    
    async def container_log(self, event):
        """Handle container log event"""
        message = event.get('message', '')
        print(f"📡 Received container_log event: {message.strip()}")
        print(f"📡 About to send log to WebSocket client")
        await self.send_log(message)
        print(f"📡 Log sent to WebSocket client successfully")
    
    async def send_message(self, message: Dict):
        """Send message to WebSocket"""
        message['timestamp'] = datetime.now().isoformat()
        await self.send(text_data=json.dumps(message))
    
    async def send_error(self, error_message: str):
        """Send error message"""
        await self.send_message({
            'type': 'error',
            'message': error_message
        })

class AIStreamingConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time AI file generation streaming
    Provides live updates as AI creates and modifies files
    """
    
    async def connect(self):
        """Handle WebSocket connection"""
        self.project_id = self.scope['url_route']['kwargs']['project_id']
        self.room_group_name = f'ai_streaming_{self.project_id}'
        
        print(f"🎯 AI Streaming WebSocket connection for project: {self.project_id}")
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send connection confirmation
        await self.send_message({
            'type': 'connected',
            'message': 'AI streaming connection established',
            'project_id': self.project_id
        })
        
        print(f"✅ AI Streaming WebSocket connected for project: {self.project_id}")
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        print(f"❌ AI Streaming WebSocket disconnected for project: {self.project_id}")
        
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Handle received WebSocket messages"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            print(f"🎯 AI Streaming received message: {message_type}")
            
            if message_type == 'start_generation':
                await self.handle_start_generation(data)
            else:
                print(f"Unknown AI streaming message type: {message_type}")
                
        except json.JSONDecodeError:
            await self.send_error('Invalid JSON data')
        except Exception as e:
            logger.error(f"Error in AI streaming receive: {e}")
            await self.send_error(f'Error processing message: {str(e)}')
    
    async def handle_start_generation(self, data):
        """Handle AI generation start request"""
        requirements = data.get('requirements', '')
        
        if not requirements:
            await self.send_error('No requirements provided')
            return
        
        print(f"🚀 Starting AI generation for project {self.project_id}")
        
        # Send generation started event
        await self.send_message({
            'type': 'generation_started',
            'message': 'AI generation started',
            'requirements': requirements
        })
        
        try:
            # Get project
            project = await self.get_project(self.project_id)
            if not project:
                await self.send_error('Project not found')
                return
            
            # Start generation in background task
            asyncio.create_task(self.run_ai_generation(project, requirements))
            
        except Exception as e:
            logger.error(f"Error starting AI generation: {e}")
            await self.send_error(f'Failed to start generation: {str(e)}')
    
    async def run_ai_generation(self, project, requirements):
        """Run AI generation in background"""
        try:
            # Send progress updates
            await self.send_message({
                'type': 'status_update',
                'message': 'Analyzing requirements...'
            })
            
            # Generate files with streaming
            result = await self.stream_file_generation(project, requirements)
            
            if result.get('success'):
                await self.send_message({
                    'type': 'generation_completed',
                    'message': 'AI generation completed successfully',
                    'files_count': result.get('files_count', 0)
                })
            else:
                await self.send_error(result.get('error', 'Generation failed'))
                
        except Exception as e:
            logger.error(f"Error in AI generation: {e}")
            await self.send_error(f'Generation error: {str(e)}')
    
    async def stream_file_generation(self, project, requirements):
        """Stream file generation with real-time updates using SmartProjectGenerator"""
        try:
            await self.send_message({
                'type': 'status_update',
                'message': 'Initializing AI generation system...'
            })
            
            # Import the real generator
            from ai_builder.services.smart_project_generator import SmartProjectGenerator
            from ai_builder.services.container_service import ContainerService
            
            # Capture the current event loop before entering thread
            loop = asyncio.get_event_loop()
            
            # Setup progress callback for streaming
            def progress_callback(event_data: dict):
                """Callback for streaming progress updates"""
                # Use call_soon_threadsafe to schedule from a thread
                loop.call_soon_threadsafe(
                    lambda: asyncio.create_task(self.send_message(event_data))
                )
            
            # Get container service
            container_service = ContainerService()
            
            # Create generator with user context
            user = await self.get_project_user(project)
            generator = SmartProjectGenerator(str(container_service.projects_dir), user=user)
            
            await self.send_message({
                'type': 'status_update',
                'message': 'Starting AI project generation...'
            })
            
            # Run the actual AI generation with streaming
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                generator.generate_project_from_prompt_streaming,
                requirements,
                str(project.id),
                progress_callback
            )
            
            if result.get('success'):
                # Send final completion message
                await self.send_message({
                    'type': 'status_update',
                    'message': f'Generation completed! Created {result.get("files_count", 0)} files.'
                })
                
                return {
                    'success': True,
                    'files_count': result.get('files_count', 0),
                    'project_name': result.get('project_name', ''),
                    'description': result.get('description', '')
                }
            else:
                await self.send_error(f"Generation failed: {result.get('error', 'Unknown error')}")
                return {
                    'success': False,
                    'error': result.get('error', 'Unknown error')
                }
            
        except Exception as e:
            logger.error(f"Error in stream_file_generation: {e}")
            await self.send_error(f"Generation error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @database_sync_to_async
    def get_project(self, project_id):
        """Get project from database"""
        try:
            return Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return None
    
    @database_sync_to_async
    def get_project_user(self, project):
        """Get user associated with project"""
        try:
            return project.owner
        except AttributeError:
            return None
    
    async def send_message(self, message: Dict):
        """Send message to WebSocket"""
        message['timestamp'] = datetime.now().isoformat()
        await self.send(text_data=json.dumps(message))
    
    async def send_error(self, error_message: str):
        """Send error message"""
        await self.send_message({
            'type': 'error',
            'message': error_message
        })
    
    # Channel layer event handlers
    async def ai_streaming_message(self, event):
        """Handle AI streaming message from channel layer"""
        await self.send_message(event['message'])
    
    async def file_update(self, event):
        """Handle file update from channel layer"""
        await self.send_message({
            'type': 'file_updated',
            'data': event['data']
        })
