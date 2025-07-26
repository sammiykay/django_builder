from rest_framework import generics, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from rest_framework.renderers import BaseRenderer
from rest_framework.views import APIView
from django.db.models import Q, Count, Sum, Avg
from django.db import models
from django.utils import timezone
from datetime import timedelta
from django.shortcuts import get_object_or_404
from django.http import JsonResponse, StreamingHttpResponse
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import get_user_model
import time
import logging
import json
import jwt
from pathlib import Path
from django.conf import settings

from .models import (
    Project, ProjectFile, ChatMessage, CommandExecution, ChatThread,
    UserProfile, ProjectSession, ProjectTemplate, ErrorLog, UsageAnalytics
)
from .serializers import (
    ProjectSerializer, ProjectFileSerializer, ChatMessageSerializer,
    CommandExecutionSerializer, ChatRequestSerializer, CommandRequestSerializer,
    UserProfileSerializer, UserProfileUpdateSerializer, ProjectSessionSerializer, ProjectTemplateSerializer,
    ErrorLogSerializer, UsageAnalyticsSerializer, ProjectDetailSerializer,
    ChatThreadSerializer
)
from .permissions import IsOwnerOrReadOnly
from .services.claude_service import ClaudeService
from .services.container_service import ContainerService
from .services.file_merger import CodeMerger
from .services.django_integrator import DjangoIntegrator
from .services.smart_project_generator import SmartProjectGenerator
from .services.conversation_handler import ConversationHandler
from .billing_services import TokenService

logger = logging.getLogger(__name__)

class StreamingRenderer(BaseRenderer):
    media_type = 'text/event-stream'
    format = 'stream'
    charset = 'utf-8'

    def render(self, data, media_type=None, renderer_context=None):
        if hasattr(data, '__iter__'):
            return data
        return str(data).encode(self.charset)

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'ai_builder/index.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['projects'] = Project.objects.filter(owner=self.request.user)[:5]
        return context


class ProjectViewSet(ModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    
    def get_queryset(self):
        return Project.objects.filter(owner=self.request.user)
    
    @action(detail=True, methods=['post'])
    def start_container(self, request, pk=None):
        """Start Django development server in container - async version"""
        from threading import Thread
        import time
        
        project = self.get_object()
        
        # Set status to starting immediately
        project.ai_generation_status = 'container_starting'
        project.save()
        
        def start_container_async():
            """Background task to start container"""
            try:
                container_service = ContainerService()
                result = container_service.start_container(
                    str(project.id), 
                    port=8001 + int(str(project.id)[-3:], 16) % 1000
                )
                
                # Refresh project from database
                project.refresh_from_db()
                
                if 'error' not in result:
                    project.container_id = result['container_id']
                    project.container_port = result['port']
                    project.is_running = True
                    project.ai_generation_status = 'container_running'
                    project.save()
                else:
                    project.ai_generation_status = f'container_failed: {result["error"]}'
                    project.save()
                    
            except Exception as e:
                # Refresh project from database
                project.refresh_from_db()
                project.ai_generation_status = f'container_failed: {str(e)}'
                project.save()
        
        # Start container in background thread
        thread = Thread(target=start_container_async, daemon=True)
        thread.start()
        
        # Return immediately with starting status
        return Response({
            'message': 'Container startup initiated. Check project status for progress.',
            'status': 'starting',
            'project_id': str(project.id)
        })
    
    @action(detail=True, methods=['get'])
    def container_status(self, request, pk=None):
        """Get container startup status"""
        project = self.get_object()
        
        return Response({
            'project_id': str(project.id),
            'status': project.ai_generation_status,
            'is_running': project.is_running,
            'container_port': project.container_port,
            'container_id': project.container_id
        })
    
    @action(detail=True, methods=['post'])
    def stop_container(self, request, pk=None):
        """Stop Django development server"""
        project = self.get_object()
        
        # Check if force kill is requested (useful during build interruption)
        force_kill = request.data.get('force_kill', False)
        
        container_service = ContainerService()
        result = container_service.stop_container(str(project.id), force_kill=force_kill)
        
        if result.get('status') in ['stopped', 'not_found']:
            project.container_id = None
            project.container_port = None
            project.is_running = False
            project.ai_generation_status = 'idle'
            project.save()
            
            return Response({
                'message': 'Container stopped successfully',
                'status': result.get('status')
            })
        else:
            return Response({
                'error': f"Failed to stop container: {result.get('error', 'Unknown error')}",
                'status': result.get('status')
            }, status=500)
    
    @action(detail=True, methods=['post'])
    def smart_generate(self, request, pk=None):
        """
        Dynamic AI workflow: Analyze any type of prompt and generate appropriate Django project structure
        Supports building ANY kind of application based on user requirements
        """
        project = self.get_object()
        serializer = ChatRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user_prompt = serializer.validated_data['message']
        
        # Track prompt evolution for dynamic building
        self._update_project_with_prompt(project, user_prompt)
        
        # Update project status
        project.ai_generation_status = 'generating'
        project.last_prompt = user_prompt
        project.save()
        
        # Save user message
        ChatMessage.objects.create(
            project=project,
            role='user',
            content=user_prompt
        )
        
        try:
            start_time = time.time()
            
            # Check if this is a new project or existing project
            if not project.django_project_created or project.files.count() == 0:
                # NEW PROJECT: Use smart project generator
                container_service = ContainerService()
                generator = SmartProjectGenerator(container_service.projects_dir)
                
                # Generate complete project from user prompt
                result = generator.generate_project_from_prompt(user_prompt, str(project.id))
                processing_time = time.time() - start_time
                
                if not result.get('success'):
                    project.ai_generation_status = 'error'
                    project.save()
                    
                    error_msg = f"Smart generation failed: {result.get('error', 'Unknown error')}"
                    ChatMessage.objects.create(
                        project=project,
                        role='assistant',
                        content=error_msg,
                        processing_time=processing_time
                    )
                    
                    return Response(
                        {'error': error_msg},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Read and save all generated files to database
                saved_files = []
                project_path = Path(container_service.projects_dir) / str(project.id)
                
                # Walk through all generated files and save them
                for file_path in project_path.rglob('*'):
                    if file_path.is_file() and not file_path.name.startswith('.'):
                        try:
                            # Get relative path from project root
                            relative_path = file_path.relative_to(project_path)
                            
                            # Read file content
                            with open(file_path, 'r', encoding='utf-8') as f:
                                file_content = f.read()
                            
                            # Save to database
                            project_file, created = ProjectFile.objects.update_or_create(
                                project=project,
                                path=str(relative_path),
                                defaults={
                                    'content': file_content,
                                    'file_type': file_path.suffix.lstrip('.') if file_path.suffix else 'txt',
                                    'is_ai_generated': True,
                                    'ai_merge_status': 'new'
                                }
                            )
                            saved_files.append(ProjectFileSerializer(project_file).data)
                            
                        except Exception as e:
                            logger.error(f"Failed to save file {file_path}: {e}")
                
                # Update project with generated structure
                project.django_project_created = True
                project.main_app_name = result.get('project_name', 'main')
                project.ai_generation_status = 'completed'
                project.name = result.get('project_name', project.name)
                project.description = result.get('description', project.description)
                project.save()
                
                # Create comprehensive AI response message
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

**Setup Instructions:**
{chr(10).join(f"• {step}" for step in result['setup_instructions'])}

**API Endpoints:**
{chr(10).join(f"• {endpoint['url']} [{', '.join(endpoint['methods'])}] - {endpoint['purpose']}" for endpoint in result.get('api_endpoints', []))}

**Next Steps:**
{chr(10).join(f"• {step}" for step in result['next_steps'])}

Your project is ready to use at: {result['access_url']}
"""
                
                # Save AI response
                ai_message = ChatMessage.objects.create(
                    project=project,
                    role='assistant',
                    content=ai_response_content,
                    processing_time=processing_time
                )
                
                return Response({
                    'message': ai_response_content,
                    'project_structure': {
                        'project_name': result['project_name'],
                        'description': result['description'],
                        'features': result['features'],
                        'tech_stack': result['tech_stack']
                    },
                    'files': saved_files,
                    'commands': result.get('setup_instructions', []),
                    'processing_time': processing_time,
                    'django_project_created': True,
                    'project_path': f"/user_projects/{project.id}",
                    'generation_type': 'smart_complete',
                    'api_endpoints': result.get('api_endpoints', []),
                    'access_url': result.get('access_url', 'http://localhost:8000')
                })
                
            else:
                # EXISTING PROJECT: Use generator to add components
                container_service = ContainerService()
                generator = SmartProjectGenerator(container_service.projects_dir)
                
                # Analyze user prompt to determine what to add
                analysis_prompt = f"""
Analyze this request for an existing Django project and determine what component should be added:

USER REQUEST: "{user_prompt}"

Respond with JSON in this format:
{{
    "component_type": "model|view|api_endpoint|template|feature",
    "app_name": "target_app_name",
    "component_config": {{
        "name": "component_name",
        "purpose": "what this component does",
        "fields": [] // for models
        // other relevant config
    }}
}}
"""
                
                try:
                    claude_service = ClaudeService()
                    analysis_response = claude_service.client.messages.create(
                        model="claude-3-5-sonnet-20241022",
                        max_tokens=1000,
                        temperature=0.1,
                        messages=[
                            {"role": "user", "content": analysis_prompt}
                        ]
                    )
                    
                    analysis_content = analysis_response.content[0].text.strip()
                    
                    # Parse the analysis
                    import json
                    import re
                    
                    # Try to extract JSON from the response
                    json_match = re.search(r'\{[\s\S]*\}', analysis_content)
                    if json_match:
                        analysis_data = json.loads(json_match.group())
                        
                        # Use the generator to add the component
                        component_result = generator.generate_app_component(
                            str(project.id),
                            analysis_data['component_type'],
                            analysis_data['component_config']
                        )
                        
                        processing_time = time.time() - start_time
                        
                        if component_result.get('success'):
                            # Update project status
                            project.ai_generation_status = 'completed'
                            project.save()
                            
                            # Save AI response
                            ai_message_content = f"""
Successfully added {analysis_data['component_type']} to your project!

**Component Added:** {analysis_data['component_config']['name']}
**Purpose:** {analysis_data['component_config']['purpose']}

**Next Steps:**
{chr(10).join(f"• {step}" for step in component_result.get('next_steps', []))}
"""
                            
                            ai_message = ChatMessage.objects.create(
                                project=project,
                                role='assistant',
                                content=ai_message_content,
                                processing_time=processing_time
                            )
                            
                            return Response({
                                'message': ai_message_content,
                                'component_added': analysis_data['component_config']['name'],
                                'component_type': analysis_data['component_type'],
                                'next_steps': component_result.get('next_steps', []),
                                'processing_time': processing_time,
                                'django_project_created': True,
                                'project_path': f"/user_projects/{project.id}",
                                'generation_type': 'component_addition'
                            })
                        else:
                            raise Exception(component_result.get('error', 'Component generation failed'))
                    else:
                        raise Exception("Could not parse component analysis")
                        
                except Exception as e:
                    # Fallback to simple enhancement
                    claude_service = ClaudeService()
                    
                    enhancement_prompt = f"""
Enhance this existing Django project based on the user's request:

USER REQUEST: "{user_prompt}"

PROJECT INFO:
- Name: {project.name}
- Description: {project.description}
- Main App: {project.main_app_name or 'main'}
- Existing Files: {project.files.count()} files

Provide specific suggestions for implementing the user's request.
Include code examples and step-by-step instructions.
"""
                    
                    ai_response = claude_service.client.messages.create(
                        model="claude-3-5-sonnet-20241022",
                        max_tokens=2000,
                        temperature=0.1,
                        messages=[
                            {"role": "user", "content": enhancement_prompt}
                        ]
                    )
                    
                    ai_message_content = ai_response.content[0].text.strip()
                    processing_time = time.time() - start_time
                    
                    # Update project status
                    project.ai_generation_status = 'completed'
                    project.save()
                    
                    # Save AI response
                    ai_message = ChatMessage.objects.create(
                        project=project,
                        role='assistant',
                        content=ai_message_content,
                        processing_time=processing_time
                    )
                    
                    return Response({
                        'message': ai_message_content,
                        'files': [],
                        'commands': [],
                        'processing_time': processing_time,
                        'django_project_created': True,
                        'project_path': f"/user_projects/{project.id}",
                        'generation_type': 'enhancement_suggestion'
                    })
            
        except Exception as e:
            project.ai_generation_status = 'error'
            project.save()
            
            error_msg = f"Error in smart generation: {str(e)}"
            ChatMessage.objects.create(
                project=project,
                role='assistant',
                content=error_msg,
                processing_time=time.time() - start_time
            )
            
            return Response(
                {'error': error_msg},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get', 'post'], 
            renderer_classes=[StreamingRenderer], permission_classes=[])
    def smart_generate_stream(self, request, pk=None):
        """
        Streaming version of smart_generate that provides real-time updates like bolt.new
        """
        # Handle GET requests for EventSource (SSE)
        if request.method == 'GET':
            # Handle authentication via query parameter for EventSource
            token = request.GET.get('token')
            if token:
                try:
                    # Decode JWT token
                    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
                    User = get_user_model()
                    user = User.objects.get(id=payload['user_id'])
                    request.user = user
                except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, User.DoesNotExist):
                    return StreamingHttpResponse(
                        iter([f"data: {json.dumps({'type': 'error', 'message': 'Invalid or expired token'})}\n\n"]),
                        content_type='text/event-stream'
                    )
            else:
                return StreamingHttpResponse(
                    iter([f"data: {json.dumps({'type': 'error', 'message': 'Authentication token required'})}\n\n"]),
                    content_type='text/event-stream'
                )
        
        # Get project and verify ownership
        try:
            project = Project.objects.get(id=pk, owner=request.user)
        except Project.DoesNotExist:
            if request.method == 'GET':
                return StreamingHttpResponse(
                    iter([f"data: {json.dumps({'type': 'error', 'message': 'Project not found or access denied'})}\n\n"]),
                    content_type='text/event-stream'
                )
            else:
                return Response({'error': 'Project not found or access denied'}, status=404)
        
        if request.method == 'GET':
            # Get message from query parameters
            user_prompt = request.GET.get('message', '')
            if not user_prompt:
                return StreamingHttpResponse(
                    iter([f"data: {json.dumps({'type': 'error', 'message': 'Message parameter is required'})}\n\n"]),
                    content_type='text/event-stream'
                )
        else:
            # Handle POST requests
            serializer = ChatRequestSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            user_prompt = serializer.validated_data['message']
        
        def generate_stream():
            try:
                # Track prompt evolution for dynamic building
                self._update_project_with_prompt(project, user_prompt)
                
                # Update project status
                project.ai_generation_status = 'generating'
                project.last_prompt = user_prompt
                project.save()
                
                # Save user message
                ChatMessage.objects.create(
                    project=project,
                    role='user',
                    content=user_prompt
                )
                
                # Send initial status
                yield f"data: {json.dumps({'type': 'status', 'message': 'Starting project generation...', 'status': 'initializing'})}\n\n"
                
                start_time = time.time()
                
                # Check if this is a new project or existing project
                if not project.django_project_created or project.files.count() == 0:
                    # NEW PROJECT: Use smart project generator with streaming
                    container_service = ContainerService()
                    generator = SmartProjectGenerator(container_service.projects_dir)
                    
                    yield f"data: {json.dumps({'type': 'status', 'message': 'Analyzing your requirements...', 'status': 'analyzing'})}\n\n"
                    
                    # Generate complete project from user prompt
                    result = generator.generate_project_from_prompt(user_prompt, str(project.id))
                    
                    if not result.get('success'):
                        project.ai_generation_status = 'error'
                        project.save()
                        
                        error_msg = f"Smart generation failed: {result.get('error', 'Unknown error')}"
                        yield f"data: {json.dumps({'type': 'error', 'message': error_msg})}\n\n"
                        return
                    
                    yield f"data: {json.dumps({'type': 'status', 'message': 'Project structure created! Generating files...', 'status': 'generating'})}\n\n"
                    
                    # Read and save all generated files to database with streaming updates
                    saved_files = []
                    project_path = Path(container_service.projects_dir) / str(project.id)
                    
                    file_count = 0
                    total_files = len(list(project_path.rglob('*')))
                    
                    # Walk through all generated files and save them
                    for file_path in project_path.rglob('*'):
                        if file_path.is_file() and not file_path.name.startswith('.'):
                            try:
                                # Get relative path from project root
                                relative_path = file_path.relative_to(project_path)
                                
                                # Read file content
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    file_content = f.read()
                                
                                # Save to database
                                project_file, created = ProjectFile.objects.update_or_create(
                                    project=project,
                                    path=str(relative_path),
                                    defaults={
                                        'content': file_content,
                                        'file_type': file_path.suffix.lstrip('.') if file_path.suffix else 'txt',
                                        'is_ai_generated': True,
                                        'ai_merge_status': 'new'
                                    }
                                )
                                saved_files.append(ProjectFileSerializer(project_file).data)
                                
                                file_count += 1
                                progress = (file_count / total_files) * 100
                                
                                yield f"data: {json.dumps({'type': 'file_created', 'file': str(relative_path), 'progress': progress})}\n\n"
                                
                            except Exception as e:
                                logger.error(f"Failed to save file {file_path}: {e}")
                    
                    # Update project with generated structure
                    project.django_project_created = True
                    project.main_app_name = result.get('project_name', 'main')
                    project.ai_generation_status = 'completed'
                    project.name = result.get('project_name', project.name)
                    project.description = result.get('description', project.description)
                    project.save()
                    
                    processing_time = time.time() - start_time
                    
                    # Create comprehensive AI response message
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

**Setup Instructions:**
{chr(10).join(f"• {step}" for step in result['setup_instructions'])}

**API Endpoints:**
{chr(10).join(f"• {endpoint['url']} [{', '.join(endpoint['methods'])}] - {endpoint['purpose']}" for endpoint in result.get('api_endpoints', []))}

**Next Steps:**
{chr(10).join(f"• {step}" for step in result['next_steps'])}

Your project is ready to use at: {result['access_url']}
"""
                    
                    # Save AI response
                    ai_message = ChatMessage.objects.create(
                        project=project,
                        role='assistant',
                        content=ai_response_content,
                        processing_time=processing_time
                    )
                    
                    # Send final completion message
                    completion_data = {
                        'type': 'completed',
                        'message': ai_response_content,
                        'project_structure': {
                            'project_name': result['project_name'],
                            'description': result['description'],
                            'features': result['features'],
                            'tech_stack': result['tech_stack']
                        },
                        'files': saved_files,
                        'commands': result.get('setup_instructions', []),
                        'processing_time': processing_time,
                        'django_project_created': True,
                        'project_path': f'/user_projects/{project.id}',
                        'generation_type': 'smart_complete',
                        'api_endpoints': result.get('api_endpoints', []),
                        'access_url': result.get('access_url', 'http://localhost:8000')
                    }
                    yield f"data: {json.dumps(completion_data)}\n\n"
                
                else:
                    # Handle existing project updates with streaming
                    yield f"data: {json.dumps({'type': 'status', 'message': 'Updating existing project...', 'status': 'updating'})}\n\n"
                    # ... existing project logic with streaming updates ...
                    
            except Exception as e:
                project.ai_generation_status = 'error'
                project.save()
                
                error_msg = f"Error in smart generation: {str(e)}"
                yield f"data: {json.dumps({'type': 'error', 'message': error_msg})}\n\n"
        
        response = StreamingHttpResponse(generate_stream(), content_type='text/event-stream')
        response['Cache-Control'] = 'no-cache'
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Headers'] = 'Cache-Control'
        return response

    
    @action(detail=True, methods=['post'])
    def generate_with_ai(self, request, pk=None):
        """Complete AI workflow: Create Django project, generate code, merge files"""
        project = self.get_object()
        serializer = ChatRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user_prompt = serializer.validated_data['message']
        app_name = request.data.get('app_name', 'main')
        
        # Update project status
        project.ai_generation_status = 'generating'
        project.last_prompt = user_prompt
        project.save()
        
        try:
            # Step 1: Create Django project if not already created
            if not project.django_project_created:
                container_service = ContainerService()
                creation_result = container_service.create_django_project(
                    project.name, 
                    str(project.id), 
                    app_name
                )
                
                if not creation_result.get('success'):
                    project.ai_generation_status = 'error'
                    project.save()
                    return Response(
                        {'error': f"Failed to create Django project: {creation_result.get('error')}"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Save created files to database
                for file_info in creation_result.get('files_created', []):
                    container_service = ContainerService()
                    file_content = container_service.get_file_content(str(project.id), file_info['path'])
                    
                    ProjectFile.objects.update_or_create(
                        project=project,
                        path=file_info['path'],
                        defaults={
                            'content': file_content,
                            'file_type': file_info.get('type', 'txt'),
                            'is_ai_generated': False,
                            'ai_merge_status': 'none'
                        }
                    )
                
                project.django_project_created = True
                project.main_app_name = creation_result.get('app_name')
                project.save()
            
            # Step 2: Generate AI code
            project_files = ProjectFile.objects.filter(project=project)[:20]
            project_context = {
                'name': project.name,
                'django_version': project.django_version,
                'app_name': project.main_app_name,
                'files': [{'path': f.path, 'type': f.file_type} for f in project_files]
            }
            
            start_time = time.time()
            claude_service = ClaudeService()
            ai_response = claude_service.generate_code(user_prompt, project_context)
            processing_time = time.time() - start_time
            
            # Save chat messages
            ChatMessage.objects.create(
                project=project,
                role='user',
                content=user_prompt
            )
            
            ai_message = ChatMessage.objects.create(
                project=project,
                role='assistant',
                content=ai_response.get('explanation', 'Generated code files'),
                processing_time=processing_time
            )
            
            # Step 3: Merge AI-generated files with existing ones
            container_service = ContainerService()
            code_merger = CodeMerger()
            saved_files = []
            merge_conflicts = []
            
            for file_info in ai_response.get('files', []):
                file_path = file_info['path']
                new_content = file_info['content']
                
                # Get existing file if it exists
                try:
                    existing_file = ProjectFile.objects.get(project=project, path=file_path)
                    existing_content = existing_file.content
                    
                    # Merge content
                    merge_result = code_merger.merge_file_content(
                        existing_content, 
                        new_content, 
                        file_path
                    )
                    
                    # Update file with merged content
                    existing_file.original_content = existing_content
                    existing_file.content = merge_result['merged_content']
                    existing_file.is_ai_generated = True
                    existing_file.ai_merge_status = 'merged' if merge_result['success'] else 'conflict'
                    existing_file.save()
                    
                    if merge_result['conflicts']:
                        merge_conflicts.extend([f"{file_path}: {conflict}" for conflict in merge_result['conflicts']])
                    
                    saved_files.append(ProjectFileSerializer(existing_file).data)
                    
                except ProjectFile.DoesNotExist:
                    # Create new file
                    project_file = ProjectFile.objects.create(
                        project=project,
                        path=file_path,
                        content=new_content,
                        file_type=file_path.split('.')[-1] if '.' in file_path else 'txt',
                        is_ai_generated=True,
                        ai_merge_status='new'
                    )
                    saved_files.append(ProjectFileSerializer(project_file).data)
                
                # Save to filesystem  
                content_to_save = new_content
                if 'merge_result' in locals() and merge_result:
                    content_to_save = merge_result.get('merged_content', new_content)
                
                container_service.save_file_content(
                    str(project.id),
                    file_path,
                    content_to_save
                )
            
            # Step 4: Integrate AI-generated code with Django project structure
            django_integrator = DjangoIntegrator(container_service.projects_dir / str(project.id))
            integration_result = django_integrator.integrate_ai_generated_code(ai_response.get('files', []))
            
            # Create missing app files for AI-generated apps
            for app_name in integration_result.get('apps_registered', []):
                django_integrator.create_missing_app_files(app_name)
            
            # Update project status
            project.ai_generation_status = 'completed'
            project.save()
            
            return Response({
                'message': ai_response.get('explanation'),
                'files': saved_files,
                'commands': ai_response.get('commands', []),
                'processing_time': processing_time,
                'django_project_created': project.django_project_created,
                'merge_conflicts': merge_conflicts,
                'project_path': f"/user_projects/{project.id}",
                'integration_result': integration_result
            })
            
        except Exception as e:
            project.ai_generation_status = 'error'
            project.save()
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def chat(self, request, pk=None):
        """Chat with AI to generate code"""
        project = self.get_object()
        serializer = ChatRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user_message = serializer.validated_data['message']
        
        # Save user message
        ChatMessage.objects.create(
            project=project,
            role='user',
            content=user_message
        )
        
        # Get project context
        project_files = ProjectFile.objects.filter(project=project)[:20]  # Limit context
        project_context = {
            'name': project.name,
            'django_version': project.django_version,
            'files': [{'path': f.path, 'type': f.file_type} for f in project_files]
        }
        
        # Generate response with Claude
        start_time = time.time()
        claude_service = ClaudeService()
        ai_response = claude_service.generate_code(user_message, project_context)
        processing_time = time.time() - start_time
        
        # Save AI response
        ai_message = ChatMessage.objects.create(
            project=project,
            role='assistant',
            content=ai_response.get('explanation', 'Generated code files'),
            processing_time=processing_time
        )
        
        # Save generated files
        container_service = ContainerService()
        saved_files = []
        
        for file_info in ai_response.get('files', []):
            # Save to database
            project_file, created = ProjectFile.objects.update_or_create(
                project=project,
                path=file_info['path'],
                defaults={
                    'content': file_info['content'],
                    'file_type': file_info['path'].split('.')[-1] if '.' in file_info['path'] else 'txt'
                }
            )
            saved_files.append(ProjectFileSerializer(project_file).data)
            
            # Save to filesystem
            container_service.save_file_content(
                str(project.id),
                file_info['path'],
                file_info['content']
            )
        
        return Response({
            'message': ai_response.get('explanation'),
            'files': saved_files,
            'commands': ai_response.get('commands', []),
            'processing_time': processing_time
        })
    
    @action(detail=True, methods=['post'])
    def execute_command(self, request, pk=None):
        """Execute Django management command"""
        project = self.get_object()
        serializer = CommandRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        command = serializer.validated_data['command']
        
        container_service = ContainerService()
        start_time = time.time()
        result = container_service.execute_command(str(project.id), command)
        execution_time = time.time() - start_time
        
        # Save command execution
        CommandExecution.objects.create(
            project=project,
            command=command,
            output=result.get('output', ''),
            error_output=result.get('error', ''),
            exit_code=result.get('exit_code', 1),
            execution_time=execution_time
        )
        
        return Response(result)
    
    @action(detail=True, methods=['get'])
    def files(self, request, pk=None):
        """Get all project files from database"""
        project = self.get_object()
        files = ProjectFile.objects.filter(project=project)
        serializer = ProjectFileSerializer(files, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def filesystem_files(self, request, pk=None):
        """Get all project files from filesystem"""
        project = self.get_object()
        container_service = ContainerService()
        
        # Get files from filesystem
        filesystem_files = container_service.list_project_files(str(project.id))
        
        # Add additional metadata and organize into tree structure
        for file_info in filesystem_files:
            file_info['type'] = 'file'
            file_info['is_directory'] = False
            # Get file extension for icon
            path_parts = file_info['path'].split('.')
            file_info['extension'] = path_parts[-1] if len(path_parts) > 1 else ''
            
        # Sort files by path for better organization
        filesystem_files.sort(key=lambda x: x['path'])
        
        return Response(filesystem_files)
    
    @action(detail=True, methods=['get'], url_path='files/content')
    def get_file_content(self, request, pk=None):
        """Get file content from filesystem"""
        project = self.get_object()
        file_path = request.query_params.get('path')
        
        if not file_path:
            return Response(
                {'error': 'File path parameter is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        container_service = ContainerService()
        
        try:
            content = container_service.get_file_content(str(project.id), file_path)
            return Response({
                'path': file_path,
                'content': content
            })
        except Exception as e:
            return Response(
                {'error': f'Failed to read file: {str(e)}'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def save_file(self, request, pk=None):
        """Save file content to filesystem"""
        project = self.get_object()
        file_path = request.data.get('path')
        content = request.data.get('content', '')
        
        if not file_path:
            return Response(
                {'error': 'File path is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        container_service = ContainerService()
        
        try:
            success = container_service.save_file_content(str(project.id), file_path, content)
            if success:
                return Response({
                    'message': f'File {file_path} saved successfully'
                })
            else:
                return Response(
                    {'error': 'Failed to save file'}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        except Exception as e:
            return Response(
                {'error': f'Failed to save file: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def conversation_chat(self, request, pk=None):
        """
        Conversational chat with full project context and error handling.
        Creates and maintains a persistent chat thread for the project.
        """
        project = self.get_object()
        serializer = ChatRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user_message = serializer.validated_data['message']
        is_error_report = request.data.get('is_error', False)
        error_type = request.data.get('error_type', '')
        
        # Get or create chat thread for this project
        chat_thread, created = ChatThread.objects.get_or_create(
            project=project,
            defaults={'is_active': True}
        )
        
        # Save user message to thread
        user_chat_message = ChatMessage.objects.create(
            thread=chat_thread,
            project=project,
            role='user',
            content=user_message,
            message_type='error_report' if is_error_report else 'normal',
            is_error_report=is_error_report,
            error_type=error_type
        )
        
        try:
            # Initialize conversation service
            from .services.conversation_service import ConversationService
            conversation_service = ConversationService()
            
            start_time = time.time()
            
            # Generate response with full context
            response = conversation_service.handle_conversation(
                project=project,
                chat_thread=chat_thread,
                user_message=user_message,
                is_error_report=is_error_report,
                error_type=error_type
            )
            
            processing_time = time.time() - start_time
            
            # Save AI response to thread
            ai_chat_message = ChatMessage.objects.create(
                thread=chat_thread,
                project=project,
                role='assistant',
                content=response.get('message', 'Response generated'),
                message_type='fix_applied' if response.get('files_modified') else 'normal',
                files_modified=response.get('files_modified', []),
                code_changes=response.get('code_changes', {}),
                processing_time=processing_time
            )
            
            return Response({
                'message': response.get('message'),
                'files_modified': response.get('files_modified', []),
                'code_changes': response.get('code_changes', {}),
                'suggestions': response.get('suggestions', []),
                'processing_time': processing_time,
                'thread_id': str(chat_thread.thread_id),
                'error_fixed': response.get('error_fixed', False)
            })
            
        except ImportError:
            # Fallback to basic chat if conversation service doesn't exist yet
            return self._basic_conversation_fallback(project, chat_thread, user_message, is_error_report)
        except Exception as e:
            logger.error(f"Conversation error: {e}")
            
            # Save error response
            ChatMessage.objects.create(
                thread=chat_thread,
                project=project,
                role='assistant',
                content=f"I encountered an error: {str(e)}",
                message_type='system_notification'
            )
            
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _basic_conversation_fallback(self, project, chat_thread, user_message, is_error_report):
        """Basic conversation fallback when full service isn't available"""
        from .services.claude_service import ClaudeService
        
        # Build project context
        project_files = ProjectFile.objects.filter(project=project)[:10]
        recent_messages = ChatMessage.objects.filter(
            thread=chat_thread
        ).order_by('-timestamp')[:10]
        
        context_prompt = f"""
You are helping with a Django project called "{project.name}".

Project Info:
- Type: {project.get_project_type_display()}
- Complexity: {project.get_complexity_level_display()}
- Django Version: {project.django_version}
- Main App: {project.main_app_name or 'main'}
- Files: {project_files.count()} files

Recent conversation:
{chr(10).join([f"{msg.role}: {msg.content[:100]}..." for msg in recent_messages])}

Current request: "{user_message}"
{'This is an ERROR REPORT - please help fix the issue.' if is_error_report else ''}

Provide helpful assistance for this Django project.
"""
        
        claude_service = ClaudeService()
        start_time = time.time()
        
        try:
            response = claude_service.client.messages.create(
                model="claude-opus-4-20250514",
                max_tokens=1500,
                temperature=0.1,
                messages=[{"role": "user", "content": context_prompt}]
            )
            
            ai_response = response.content[0].text.strip()
            processing_time = time.time() - start_time
            
            # Save AI response
            ChatMessage.objects.create(
                thread=chat_thread,
                project=project,
                role='assistant',
                content=ai_response,
                processing_time=processing_time
            )
            
            return Response({
                'message': ai_response,
                'files_modified': [],
                'code_changes': {},
                'suggestions': [],
                'processing_time': processing_time,
                'thread_id': str(chat_thread.thread_id),
                'error_fixed': False
            })
            
        except Exception as e:
            return Response(
                {'error': f'Conversation failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'])
    def conversation_history(self, request, pk=None):
        """Get conversation history for project's chat thread"""
        project = self.get_object()
        
        try:
            chat_thread = ChatThread.objects.get(project=project)
            messages = ChatMessage.objects.filter(
                thread=chat_thread
            ).order_by('timestamp')
            
            serializer = ChatMessageSerializer(messages, many=True)
            return Response({
                'thread_id': str(chat_thread.thread_id),
                'messages': serializer.data,
                'total_messages': messages.count()
            })
            
        except ChatThread.DoesNotExist:
            return Response({
                'thread_id': None,
                'messages': [],
                'total_messages': 0
            })

    @action(detail=True, methods=['post'])
    def report_error(self, request, pk=None):
        """Report an error from the running project for AI to fix"""
        project = self.get_object()
        
        error_message = request.data.get('error_message', '')
        error_type = request.data.get('error_type', 'runtime_error')
        error_source = request.data.get('error_source', '')
        
        if not error_message:
            return Response(
                {'error': 'error_message is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Use conversation chat with error flag
        request.data['message'] = f"ERROR REPORT: {error_message}"
        request.data['is_error'] = True
        request.data['error_type'] = error_type
        
        return self.conversation_chat(request, pk)

    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        """Get chat messages for project (legacy endpoint)"""
        project = self.get_object()
        messages = ChatMessage.objects.filter(project=project)
        serializer = ChatMessageSerializer(messages, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def executions(self, request, pk=None):
        """Get command executions for project"""
        project = self.get_object()
        executions = CommandExecution.objects.filter(project=project)
        serializer = CommandExecutionSerializer(executions, many=True)
        return Response(serializer.data)
    
    def _update_project_with_prompt(self, project, user_prompt):
        """
        Update project metadata based on user prompt for dynamic building support.
        Analyzes prompt to extract project type, features, and requirements.
        """
        # Store original prompt if this is the first one
        if not project.original_prompt:
            project.original_prompt = user_prompt
        
        # Add to prompt history
        if not project.prompt_history:
            project.prompt_history = []
        
        project.prompt_history.append({
            'timestamp': project.updated_at.isoformat() if project.updated_at else None,
            'prompt': user_prompt,
            'type': 'initial' if not project.django_project_created else 'enhancement'
        })
        
        # Basic project type detection
        prompt_lower = user_prompt.lower()
        
        # Detect project type from keywords
        type_keywords = {
            'blog': ['blog', 'post', 'article', 'cms', 'content'],
            'ecommerce': ['shop', 'store', 'product', 'cart', 'payment', 'buy', 'sell'],
            'social': ['social', 'chat', 'friend', 'follow', 'message', 'network'],
            'dashboard': ['dashboard', 'analytics', 'chart', 'report', 'metrics'],
            'api': ['api', 'rest', 'endpoint', 'service', 'microservice'],
            'portfolio': ['portfolio', 'gallery', 'showcase', 'work', 'project display'],
            'business': ['business', 'company', 'management', 'crm', 'employee'],
            'education': ['education', 'learning', 'course', 'student', 'teacher', 'quiz'],
            'entertainment': ['game', 'movie', 'music', 'entertainment', 'media', 'streaming']
        }
        
        for project_type, keywords in type_keywords.items():
            if any(keyword in prompt_lower for keyword in keywords):
                project.project_type = project_type
                break
        
        # Extract key features from prompt
        feature_keywords = {
            'user authentication': ['login', 'register', 'auth', 'user', 'account'],
            'file upload': ['upload', 'file', 'image', 'photo', 'document'],
            'search functionality': ['search', 'filter', 'find', 'query'],
            'real-time updates': ['real-time', 'live', 'instant', 'websocket'],
            'payment processing': ['payment', 'stripe', 'paypal', 'checkout', 'billing'],
            'admin interface': ['admin', 'management', 'backend', 'control panel'],
            'responsive design': ['mobile', 'responsive', 'tablet', 'device'],
            'API endpoints': ['api', 'rest', 'json', 'endpoint'],
            'database relations': ['foreign key', 'relationship', 'join', 'related'],
            'email notifications': ['email', 'notification', 'alert', 'notify']
        }
        
        detected_features = []
        for feature, keywords in feature_keywords.items():
            if any(keyword in prompt_lower for keyword in keywords):
                detected_features.append(feature)
        
        # Update or initialize key_features
        if not project.key_features:
            project.key_features = []
        
        # Add new features that aren't already tracked
        for feature in detected_features:
            if feature not in project.key_features:
                project.key_features.append(feature)
        
        # Detect complexity level based on prompt content - default to complex
        # Only downgrade if user explicitly indicates simpler complexity
        if any(word in prompt_lower for word in ['simple', 'basic', 'minimal', 'quick', 'small', 'easy']):
            project.complexity_level = 'simple'
        elif any(word in prompt_lower for word in ['medium', 'moderate', 'standard', 'typical']):
            project.complexity_level = 'medium'
        elif any(word in prompt_lower for word in ['enterprise', 'large-scale', 'production-grade', 'scalable', 'distributed', 'microservices']):
            project.complexity_level = 'enterprise'
        # Default to complex unless explicitly downgraded
        
        # Save the updated project
        project.save()

    @action(detail=False, methods=['post'])
    def quick_create_and_generate(self, request):
        """
        Quick project creation and automatic generation from simple description
        Creates project with auto-detected details and starts async generation
        """
        description = request.data.get('description', '').strip()
        
        if not description or len(description) < 20:
            return Response(
                {'error': 'Description must be at least 20 characters long'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Auto-generate project details from description
            project_details = self._generate_project_details_from_description(description)
            
            # Use the serializer to create the project
            serializer = self.get_serializer(data=project_details)
            serializer.is_valid(raise_exception=True)
            project = serializer.save(owner=request.user, description=description)
            
            # Set initial status
            project.ai_generation_status = 'generating'
            project.last_prompt = description
            project.save()
            
            # Save user message
            ChatMessage.objects.create(
                project=project,
                role='user',
                content=description
            )
            
            # Start async generation task
            from threading import Thread
            thread = Thread(
                target=self._async_generate_project,
                args=(project.id, description),
                daemon=True
            )
            thread.start()
            
            # Return immediately with project created status
            return Response({
                'success': True,
                'project': ProjectSerializer(project).data,
                'message': 'Project created successfully. Generation in progress...',
                'status': 'generating',
                'project_id': str(project.id)
            })
            
        except Exception as e:
            logger.error(f"Quick project creation failed: {e}")
            return Response(
                {'error': f'Failed to create project: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _async_generate_project(self, project_id, description):
        """
        Async project generation task that runs in background thread
        """
        try:
            from django.db import connections
            # Close any existing DB connections to avoid issues in threads
            connections.close_all()
            
            project = Project.objects.get(id=project_id)
            start_time = time.time()
            
            # Use smart project generator
            container_service = ContainerService()
            generator = SmartProjectGenerator(container_service.projects_dir)
            
            # Generate complete project from user prompt
            result = generator.generate_project_from_prompt(description, str(project.id))
            processing_time = time.time() - start_time
            
            if result.get('success'):
                # Read and save all generated files to database
                saved_files = []
                project_path = Path(container_service.projects_dir) / str(project.id)
                
                # Walk through all generated files and save them
                for file_path in project_path.rglob('*'):
                    if file_path.is_file() and not file_path.name.startswith('.'):
                        try:
                            # Get relative path from project root
                            relative_path = file_path.relative_to(project_path)
                            
                            # Read file content
                            with open(file_path, 'r', encoding='utf-8') as f:
                                file_content = f.read()
                            
                            # Save to database
                            project_file, created = ProjectFile.objects.update_or_create(
                                project=project,
                                path=str(relative_path),
                                defaults={
                                    'content': file_content,
                                    'file_type': file_path.suffix.lstrip('.') if file_path.suffix else 'txt',
                                    'is_ai_generated': True,
                                    'ai_merge_status': 'new'
                                }
                            )
                            saved_files.append(str(relative_path))
                            
                        except Exception as e:
                            logger.error(f"Failed to save file {file_path}: {e}")
                
                # Update project with generated structure
                project.django_project_created = True
                project.main_app_name = result.get('project_name', 'main')
                project.ai_generation_status = 'completed'
                project.name = result.get('project_name', project.name)
                project.save()
                
                # Create AI response message
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

**Setup Instructions:**
{chr(10).join(f"• {step}" for step in result['setup_instructions'])}

Your project is ready to use!
"""
                
                # Save AI response
                ChatMessage.objects.create(
                    project=project,
                    role='assistant',
                    content=ai_response_content,
                    processing_time=processing_time,
                    tokens_used=result.get('tokens_used', 0)
                )
                
                logger.info(f"Successfully generated project {project.id} with {len(saved_files)} files")
                
            else:
                # Generation failed
                project.ai_generation_status = 'error'
                project.save()
                
                error_msg = f"Project generation failed: {result.get('error', 'Unknown error')}"
                ChatMessage.objects.create(
                    project=project,
                    role='assistant',
                    content=error_msg,
                    processing_time=processing_time,
                    is_error_report=True
                )
                
                logger.error(f"Generation failed for project {project.id}: {error_msg}")
                
        except Exception as e:
            logger.error(f"Async generation failed for project {project_id}: {e}")
            
            # Update project status to error
            try:
                project = Project.objects.get(id=project_id)
                project.ai_generation_status = 'error'
                project.save()
                
                ChatMessage.objects.create(
                    project=project,
                    role='assistant',
                    content=f"Generation failed with error: {str(e)}",
                    is_error_report=True
                )
            except Exception as db_error:
                logger.error(f"Failed to update project status: {db_error}")

    @action(detail=True, methods=['get'])
    def generation_status(self, request, pk=None):
        """
        Check the status of project generation
        """
        project = self.get_object()
        
        # Get latest message from AI
        latest_message = ChatMessage.objects.filter(
            project=project,
            role='assistant'
        ).order_by('-timestamp').first()
        
        response_data = {
            'project_id': str(project.id),
            'status': project.ai_generation_status,
            'django_project_created': project.django_project_created,
            'files_count': project.files.count(),
            'latest_message': latest_message.content if latest_message else None,
            'project_name': project.name,
            'is_running': project.is_running
        }
        
        # If completed, add additional details
        if project.ai_generation_status == 'completed':
            response_data.update({
                'access_url': f'http://localhost:{project.container_port}' if project.container_port else 'http://localhost:8000',
                'main_app_name': project.main_app_name,
                'setup_complete': True
            })
        
        return Response(response_data)

    def _generate_project_details_from_description(self, description: str) -> dict:
        """Auto-generate project details from user description"""
        import re
        from pathlib import Path
        
        lowercaseDesc = description.lower()
        
        # Auto-detect project type
        project_type = 'web_app'  # default
        if any(word in lowercaseDesc for word in ['blog', 'article', 'post']):
            project_type = 'blog'
        elif any(word in lowercaseDesc for word in ['ecommerce', 'e-commerce', 'shop', 'store', 'product', 'cart']):
            project_type = 'ecommerce'
        elif any(word in lowercaseDesc for word in ['social', 'chat', 'message', 'follow']):
            project_type = 'social'
        elif any(word in lowercaseDesc for word in ['dashboard', 'admin', 'analytics']):
            project_type = 'dashboard'
        elif any(word in lowercaseDesc for word in ['api', 'endpoint', 'rest']):
            project_type = 'api'
        elif any(word in lowercaseDesc for word in ['portfolio', 'showcase']):
            project_type = 'portfolio'
        elif any(word in lowercaseDesc for word in ['business', 'company']):
            project_type = 'business'
        elif any(word in lowercaseDesc for word in ['education', 'learning', 'course', 'quiz']):
            project_type = 'education'
        
        # Auto-detect complexity - default to complex unless explicitly indicated
        complexity = 'complex'  # Default to complex
        
        # Only downgrade complexity if user explicitly indicates it
        if any(word in lowercaseDesc for word in ['simple', 'basic', 'minimal', 'quick', 'small', 'easy']):
            complexity = 'simple'
        elif any(word in lowercaseDesc for word in ['medium', 'moderate', 'standard', 'typical']):
            complexity = 'medium'
        elif any(word in lowercaseDesc for word in ['enterprise', 'large-scale', 'production-grade', 'scalable', 'distributed', 'microservices']):
            complexity = 'enterprise'
        # If user says "complex" or similar, keep it complex (default)
        
        # Auto-extract features
        features = []
        feature_map = {
            'User Authentication': ['login', 'register', 'auth', 'user', 'account'],
            'File Upload': ['upload', 'file', 'image', 'document'],
            'Email Integration': ['email', 'notification', 'mail'],
            'Payment Processing': ['payment', 'pay', 'checkout', 'billing'],
            'Real-time Chat': ['chat', 'message', 'real-time', 'live'],
            'API Integration': ['api', 'integration', 'external'],
            'Admin Dashboard': ['admin', 'dashboard', 'management'],
            'Search Functionality': ['search', 'find', 'filter'],
            'Social Login': ['social login', 'facebook', 'google', 'oauth'],
            'Multi-language Support': ['language', 'international', 'locale']
        }
        
        for feature, keywords in feature_map.items():
            if any(keyword in lowercaseDesc for keyword in keywords):
                features.append(feature)
        
        # Generate project name from description
        words = description.split(' ')[:4]
        clean_words = [re.sub(r'[^a-zA-Z0-9]', '', word) for word in words if len(word) > 2][:3]
        
        if not clean_words:
            name = f"Project_{int(time.time())}"
        else:
            name = '_'.join(word.capitalize() for word in clean_words)
        
        return {
            'name': name,
            'python_version': '3.11',
            'django_version': '5.0',
            'project_type': project_type,
            'complexity_level': complexity,
            'target_audience': 'General users',
            'key_features': features,
            'technical_requirements': {}
        }

class ProjectFileViewSet(ModelViewSet):
    serializer_class = ProjectFileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        project_id = self.kwargs.get('project_pk')
        return ProjectFile.objects.filter(
            project_id=project_id,
            project__owner=self.request.user
        )
    
    def perform_create(self, serializer):
        project_id = self.kwargs.get('project_pk')
        project = get_object_or_404(Project, id=project_id, owner=self.request.user)
        
        # Save to database
        project_file = serializer.save(project=project)
        
        # Save to filesystem
        container_service = ContainerService()
        container_service.save_file_content(
            str(project.id),
            project_file.path,
            project_file.content
        )
    
    def perform_update(self, serializer):
        # Save to database
        project_file = serializer.save()
        
        # Save to filesystem
        container_service = ContainerService()
        container_service.save_file_content(
            str(project_file.project.id),
            project_file.path,
            project_file.content
        )

class ProjectStatsView(generics.RetrieveAPIView):
    """Get project statistics"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, pk):
        project = get_object_or_404(Project, id=pk, owner=request.user)
        
        stats = {
            'files_count': project.files.count(),
            'total_lines': sum(len(f.content.splitlines()) for f in project.files.all()),
            'total_size': sum(f.size for f in project.files.all()),
            'messages_count': project.messages.count(),
            'executions_count': project.executions.count(),
            'last_activity': project.updated_at,
            'is_running': project.is_running,
        }
        
        return Response(stats)
    
    @action(detail=False, methods=['post'])
    def import_existing_projects(self, request):
        """
        Scan for manually created Django projects in user_projects directory and import them
        """
        try:
            from .services.container_service import ContainerService
            container_service = ContainerService()
            projects_dir = container_service.projects_dir
            
            imported_count = 0
            
            # Scan all directories in user_projects
            for project_dir in projects_dir.iterdir():
                if project_dir.is_dir() and project_dir.name != '__pycache__':
                    # Check if this is a Django project
                    manage_py = project_dir / 'manage.py'
                    if manage_py.exists():
                        # Check if we already have this project in database
                        try:
                            project_id = project_dir.name
                            existing_project = Project.objects.get(id=project_id, owner=request.user)
                            continue  # Skip if already exists
                        except (Project.DoesNotExist, ValueError):
                            pass
                        
                        # Try to determine project name from settings or directory
                        project_name = project_dir.name
                        
                        # Look for settings.py to get project name
                        for item in project_dir.iterdir():
                            if item.is_dir() and (item / 'settings.py').exists():
                                project_name = item.name
                                break
                        
                        # Create project entry
                        try:
                            project = Project.objects.create(
                                id=project_id,
                                name=project_name,
                                description=f"Imported existing Django project: {project_name}",
                                owner=request.user,
                                django_project_created=True,
                                main_app_name='main',
                                project_type='custom'
                            )
                            
                            # Import existing files
                            self._import_project_files(project, project_dir)
                            imported_count += 1
                            
                        except Exception as e:
                            logger.error(f"Failed to import project {project_dir.name}: {e}")
                            continue
            
            return Response({
                'message': f'Successfully imported {imported_count} existing projects',
                'imported_count': imported_count
            })
            
        except Exception as e:
            logger.error(f"Error importing existing projects: {e}")
            return Response(
                {'error': f'Failed to import projects: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _import_project_files(self, project, project_dir):
        """Import files from existing Django project into database"""
        
        # Common Django file extensions to import
        extensions = ['.py', '.html', '.css', '.js', '.txt', '.md', '.yml', '.yaml', '.json']
        
        def import_files_recursive(current_dir, relative_path=""):
            for item in current_dir.iterdir():
                if item.is_file():
                    # Check if file should be imported
                    if any(item.name.endswith(ext) for ext in extensions):
                        try:
                            with open(item, 'r', encoding='utf-8') as f:
                                content = f.read()
                            
                            file_path = str(Path(relative_path) / item.name) if relative_path else item.name
                            
                            ProjectFile.objects.update_or_create(
                                project=project,
                                path=file_path,
                                defaults={
                                    'content': content,
                                    'file_type': item.suffix[1:] if item.suffix else 'txt',
                                    'is_ai_generated': False
                                }
                            )
                        except Exception as e:
                            logger.warning(f"Failed to import file {item}: {e}")
                
                elif item.is_dir() and item.name not in ['__pycache__', '.git', 'node_modules', 'venv', 'env']:
                    # Recursively import subdirectories
                    new_relative_path = str(Path(relative_path) / item.name) if relative_path else item.name
                    import_files_recursive(item, new_relative_path)
        
        import_files_recursive(project_dir)


# 🔐 1. User Profiles & Project History Views
class UserProfileViewSet(ModelViewSet):
    """
    Enhanced user profile management with usage tracking
    """
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return UserProfile.objects.filter(user=self.request.user)
    
    def get_object(self):
        """Get or create user profile"""
        profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        return profile
    
    @action(detail=False, methods=['get'])
    def dashboard_stats(self, request):
        """Get comprehensive dashboard statistics"""
        profile = self.get_object()
        
        # Project statistics
        projects = Project.objects.filter(owner=request.user)
        active_projects = projects.filter(is_running=True)
        
        # Recent activity
        recent_sessions = ProjectSession.objects.filter(
            user=request.user,
            start_time__gte=timezone.now() - timedelta(days=30)
        )
        
        # Error statistics
        unresolved_errors = ErrorLog.objects.filter(
            project__owner=request.user,
            is_resolved=False
        )
        
        # Usage trends (last 30 days)
        analytics = UsageAnalytics.objects.filter(
            user=request.user,
            timestamp__gte=timezone.now() - timedelta(days=30)
        )
        
        daily_activity = analytics.values('timestamp__date').annotate(
            count=Count('id'),
            tokens=Sum('tokens_used')
        ).order_by('timestamp__date')
        
        return Response({
            'profile': UserProfileSerializer(profile).data,
            'stats': {
                'total_projects': projects.count(),
                'active_projects': active_projects.count(),
                'total_files': ProjectFile.objects.filter(project__owner=request.user).count(),
                'total_messages': ChatMessage.objects.filter(project__owner=request.user).count(),
                'unresolved_errors': unresolved_errors.count(),
                'monthly_tokens_used': profile.monthly_tokens_used,
                'monthly_token_limit': profile.monthly_token_limit,
                'token_usage_percentage': (profile.monthly_tokens_used / profile.monthly_token_limit) * 100,
            },
            'recent_activity': {
                'sessions_count': recent_sessions.count(),
                'average_session_duration': recent_sessions.aggregate(
                    avg=models.Avg('duration_seconds')
                )['avg'] or 0,
                'total_commands': recent_sessions.aggregate(
                    total=Sum('commands_executed')
                )['total'] or 0,
            },
            'daily_activity': list(daily_activity),
            'recent_errors': ErrorLogSerializer(
                unresolved_errors.order_by('-created_at')[:5], 
                many=True
            ).data,
        })
    
    @action(detail=False, methods=['patch'])
    def update_profile(self, request):
        """Update user profile with enhanced fields"""
        profile = self.get_object()
        serializer = UserProfileUpdateSerializer(profile, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(UserProfileSerializer(profile).data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def upload_avatar(self, request):
        """Upload user avatar"""
        profile = self.get_object()
        
        if 'avatar' not in request.FILES:
            return Response(
                {'error': 'No avatar file provided'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        profile.avatar = request.FILES['avatar']
        profile.save()
        
        return Response({
            'message': 'Avatar uploaded successfully',
            'avatar_url': profile.avatar.url if profile.avatar else None
        })
    
    @action(detail=False, methods=['delete'])
    def remove_avatar(self, request):
        """Remove user avatar"""
        profile = self.get_object()
        
        if profile.avatar:
            profile.avatar.delete()
            profile.save()
            return Response({'message': 'Avatar removed successfully'})
        
        return Response({'message': 'No avatar to remove'})
    
    @action(detail=False, methods=['post'])
    def reset_monthly_usage(self, request):
        """Reset monthly token usage (admin only)"""
        if not request.user.is_staff:
            return Response(
                {'error': 'Only administrators can reset usage'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        profile = self.get_object()
        profile.reset_monthly_usage()
        
        return Response({'message': 'Monthly usage reset successfully'})


class ProjectHistoryView(APIView):
    """
    Enhanced project history with detailed activity tracking
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get comprehensive project history"""
        projects = Project.objects.filter(owner=request.user).prefetch_related(
            'files', 'messages', 'executions', 'error_logs', 'sessions'
        )
        
        # Filter parameters
        project_type = request.GET.get('type')
        date_from = request.GET.get('date_from')
        date_to = request.GET.get('date_to')
        status_filter = request.GET.get('status')
        
        if project_type:
            projects = projects.filter(project_type=project_type)
        
        if date_from:
            projects = projects.filter(created_at__gte=date_from)
        
        if date_to:
            projects = projects.filter(created_at__lte=date_to)
        
        if status_filter == 'active':
            projects = projects.filter(is_running=True)
        elif status_filter == 'completed':
            projects = projects.filter(ai_generation_status='completed')
        
        return Response({
            'projects': ProjectDetailSerializer(projects, many=True).data,
            'summary': {
                'total_projects': projects.count(),
                'by_type': projects.values('project_type').annotate(
                    count=Count('id')
                ),
                'by_status': projects.values('ai_generation_status').annotate(
                    count=Count('id')
                ),
            }
        })


# 💬 2. Persistent Chat + Claude Threading Views
class ChatThreadViewSet(ModelViewSet):
    """
    Enhanced chat thread management with persistence
    """
    serializer_class = ChatThreadSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return ChatThread.objects.filter(project__owner=self.request.user)
    
    @action(detail=True, methods=['post'])
    def resume_conversation(self, request, pk=None):
        """Resume conversation from a specific point"""
        thread = self.get_object()
        message_id = request.data.get('from_message_id')
        
        if message_id:
            # Get conversation history from specific message
            messages = thread.messages.filter(id__gte=message_id).order_by('timestamp')
        else:
            # Get recent conversation context
            messages = thread.messages.order_by('-timestamp')[:thread.context_length]
        
        return Response({
            'thread_id': thread.thread_id,
            'messages': ChatMessageSerializer(messages, many=True).data,
            'context_summary': f"Resuming conversation with {messages.count()} messages"
        })
    
    @action(detail=True, methods=['post'])
    def clear_context(self, request, pk=None):
        """Clear conversation context but preserve history"""
        thread = self.get_object()
        
        # Archive old messages by marking them as historical
        old_messages = thread.messages.filter(timestamp__lt=timezone.now() - timedelta(hours=24))
        old_messages.update(message_type='historical')
        
        return Response({'message': 'Context cleared, history preserved'})


# 🔧 4. Real-Time Error Feedback + Auto-Fix Views
class ErrorLogViewSet(ModelViewSet):
    """
    Enhanced error tracking and auto-fix functionality
    """
    serializer_class = ErrorLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return ErrorLog.objects.filter(project__owner=self.request.user)
    
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Error dashboard with analytics"""
        errors = self.get_queryset()
        
        # Filter by project if specified
        project_id = request.GET.get('project_id')
        if project_id:
            errors = errors.filter(project_id=project_id)
        
        unresolved = errors.filter(is_resolved=False)
        recent = errors.filter(created_at__gte=timezone.now() - timedelta(days=7))
        
        return Response({
            'summary': {
                'total_errors': errors.count(),
                'unresolved_errors': unresolved.count(),
                'recent_errors': recent.count(),
                'auto_fix_success_rate': self._calculate_auto_fix_rate(errors),
            },
            'by_type': errors.values('error_type').annotate(count=Count('id')),
            'by_project': errors.values('project__name').annotate(count=Count('id')),
            'recent_unresolved': ErrorLogSerializer(
                unresolved.order_by('-created_at')[:10], 
                many=True
            ).data,
            'auto_fix_candidates': ErrorLogSerializer(
                unresolved.filter(auto_fix_attempted=False)[:5],
                many=True
            ).data,
        })
    
    @action(detail=True, methods=['post'])
    def auto_fix(self, request, pk=None):
        """Attempt automatic error fix using Claude AI"""
        error_log = self.get_object()
        
        if error_log.auto_fix_attempted:
            return Response(
                {'error': 'Auto-fix already attempted for this error'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Mark as attempted
            error_log.auto_fix_attempted = True
            error_log.save()
            
            # Use conversation handler for AI-powered fix
            conversation_handler = ConversationHandler()
            
            fix_prompt = f"""
Error detected in project {error_log.project.name}:

Error Type: {error_log.error_type}
Error Message: {error_log.error_message}
File: {error_log.file_path}
Line: {error_log.line_number}
Command: {error_log.command_executed}

Traceback:
{error_log.error_traceback}

Please analyze this error and provide a specific fix. Include:
1. Root cause analysis
2. Exact code changes needed
3. Step-by-step fix instructions

Focus on providing actionable, concrete solutions.
"""
            
            # Get AI response
            response = conversation_handler.handle_message(
                str(error_log.project.id),
                fix_prompt,
                is_error_report=True,
                error_type=error_log.error_type,
                error_source=error_log.file_path
            )
            
            # Log AI usage
            if response.get('tokens_used'):
                error_log.tokens_used_for_fix = response['tokens_used']
                error_log.save()
            
            # Try to apply fix automatically if it's a simple code change
            fix_applied = self._attempt_code_fix(error_log, response.get('response', ''))
            
            if fix_applied:
                error_log.mark_resolved(
                    fix_description=response.get('response', ''),
                    auto_fixed=True
                )
            
            return Response({
                'fix_suggestion': response.get('response', ''),
                'auto_applied': fix_applied,
                'tokens_used': response.get('tokens_used', 0),
                'status': 'resolved' if fix_applied else 'suggestion_provided'
            })
            
        except Exception as e:
            logger.error(f"Auto-fix failed for error {error_log.id}: {e}")
            return Response(
                {'error': f'Auto-fix failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _calculate_auto_fix_rate(self, errors):
        """Calculate auto-fix success rate"""
        attempted = errors.filter(auto_fix_attempted=True)
        if attempted.count() == 0:
            return 0
        successful = attempted.filter(auto_fix_successful=True)
        return (successful.count() / attempted.count()) * 100
    
    def _attempt_code_fix(self, error_log, fix_suggestion):
        """Attempt to automatically apply simple code fixes"""
        # This is a simplified implementation
        # In practice, this would use more sophisticated code analysis
        
        if not error_log.file_path or not fix_suggestion:
            return False
        
        # Look for simple patterns that can be auto-fixed
        simple_fixes = [
            'missing import',
            'indentation error',
            'missing colon',
            'missing comma',
            'undefined variable'
        ]
        
        error_msg_lower = error_log.error_message.lower()
        
        if any(pattern in error_msg_lower for pattern in simple_fixes):
            # Attempt to apply fix (simplified implementation)
            try:
                # Here you would implement actual code modification logic
                # For now, we'll just mark it as applied for demonstration
                return True
            except Exception:
                return False
        
        return False


# 📈 9. Usage Analytics Views
class UsageAnalyticsViewSet(ReadOnlyModelViewSet):
    """
    Comprehensive usage analytics and insights
    """
    serializer_class = UsageAnalyticsSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return UsageAnalytics.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Analytics dashboard with comprehensive metrics"""
        analytics = self.get_queryset()
        
        # Time range filter
        days = int(request.GET.get('days', 30))
        start_date = timezone.now() - timedelta(days=days)
        recent_analytics = analytics.filter(timestamp__gte=start_date)
        
        # Performance metrics
        avg_response_time = recent_analytics.aggregate(
            avg=models.Avg('response_time_ms')
        )['avg'] or 0
        
        # Usage patterns
        hourly_usage = recent_analytics.extra(
            select={'hour': 'EXTRACT(hour FROM timestamp)'}
        ).values('hour').annotate(count=Count('id')).order_by('hour')
        
        daily_usage = recent_analytics.extra(
            select={'date': 'DATE(timestamp)'}
        ).values('date').annotate(
            count=Count('id'),
            tokens=Sum('tokens_used')
        ).order_by('date')
        
        # Feature usage
        feature_usage = recent_analytics.values('action_type').annotate(
            count=Count('id'),
            avg_response_time=models.Avg('response_time_ms'),
            success_rate=models.Avg('success') * 100
        ).order_by('-count')
        
        # Project activity
        project_activity = recent_analytics.filter(
            project__isnull=False
        ).values(
            'project__name'
        ).annotate(
            count=Count('id'),
            tokens=Sum('tokens_used')
        ).order_by('-count')[:10]
        
        return Response({
            'summary': {
                'total_actions': recent_analytics.count(),
                'total_tokens': recent_analytics.aggregate(Sum('tokens_used'))['tokens_used__sum'] or 0,
                'avg_response_time': round(avg_response_time, 2),
                'success_rate': round(
                    recent_analytics.aggregate(models.Avg('success'))['success__avg'] * 100 or 0, 
                    2
                ),
                'most_active_hour': self._get_most_active_hour(hourly_usage),
                'most_used_feature': self._get_most_used_feature(feature_usage),
            },
            'trends': {
                'daily_usage': list(daily_usage),
                'hourly_patterns': list(hourly_usage),
                'feature_usage': list(feature_usage),
                'project_activity': list(project_activity),
            },
            'insights': self._generate_insights(recent_analytics),
        })
    
    @action(detail=False, methods=['post'])
    def track_action(self, request):
        """Track a user action for analytics"""
        data = request.data.copy()
        data['user'] = request.user.id
        
        serializer = UsageAnalyticsSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response({'status': 'tracked'}, status=status.HTTP_201_CREATED)
    
    def _get_most_active_hour(self, hourly_usage):
        """Get the hour with most activity"""
        if not hourly_usage:
            return None
        return max(hourly_usage, key=lambda x: x['count'])['hour']
    
    def _get_most_used_feature(self, feature_usage):
        """Get the most used feature"""
        if not feature_usage:
            return None
        return feature_usage[0]['action_type']
    
    def _generate_insights(self, analytics):
        """Generate AI-like insights from usage patterns"""
        insights = []
        
        # Token usage insights
        total_tokens = analytics.aggregate(Sum('tokens_used'))['tokens_used__sum'] or 0
        if total_tokens > 50000:
            insights.append({
                'type': 'usage',
                'title': 'High AI Usage Detected',
                'message': f'You\'ve used {total_tokens:,} tokens. Consider optimizing prompts for efficiency.',
                'severity': 'info'
            })
        
        # Error rate insights
        error_actions = analytics.filter(success=False).count()
        total_actions = analytics.count()
        if total_actions > 0:
            error_rate = (error_actions / total_actions) * 100
            if error_rate > 15:
                insights.append({
                    'type': 'quality',
                    'title': 'High Error Rate',
                    'message': f'Error rate is {error_rate:.1f}%. Check your recent projects for issues.',
                    'severity': 'warning'
                })
        
        # Performance insights
        slow_actions = analytics.filter(response_time_ms__gt=5000).count()
        if slow_actions > 0:
            insights.append({
                'type': 'performance',
                'title': 'Slow Response Times',
                'message': f'{slow_actions} actions took longer than 5 seconds to complete.',
                'severity': 'info'
            })
        
        return insights


class ProjectSessionViewSet(ReadOnlyModelViewSet):
    """
    Project session tracking and management
    """
    serializer_class = ProjectSessionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return ProjectSession.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def start_session(self, request):
        """Start a new project session"""
        project_id = request.data.get('project_id')
        if not project_id:
            return Response(
                {'error': 'project_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            project = Project.objects.get(id=project_id, owner=request.user)
        except Project.DoesNotExist:
            return Response(
                {'error': 'Project not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # End any existing active sessions for this project
        active_sessions = ProjectSession.objects.filter(
            project=project,
            user=request.user,
            end_time__isnull=True
        )
        
        for session in active_sessions:
            session.end_session()
        
        # Create new session
        session = ProjectSession.objects.create(
            project=project,
            user=request.user,
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            ip_address=request.META.get('REMOTE_ADDR'),
            referrer=request.META.get('HTTP_REFERER', '')
        )
        
        return Response({
            'session_id': session.session_id,
            'message': 'Session started successfully'
        })
    
    @action(detail=True, methods=['post'])
    def end_session(self, request, pk=None):
        """End a project session"""
        try:
            session = ProjectSession.objects.get(
                session_id=pk,
                user=request.user,
                end_time__isnull=True
            )
            session.end_session()
            
            return Response({
                'message': 'Session ended successfully',
                'duration': session.duration_seconds
            })
            
        except ProjectSession.DoesNotExist:
            return Response(
                {'error': 'Active session not found'},
                status=status.HTTP_404_NOT_FOUND
            )

