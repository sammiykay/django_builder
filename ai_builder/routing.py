"""
WebSocket routing for Django AI Builder
"""

from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/projects/(?P<project_id>[^/]+)/generate/$', consumers.ProjectGenerationConsumer.as_asgi()),
    re_path(r'ws/projects/(?P<project_id>[^/]+)/files/$', consumers.ProjectFileWatcher.as_asgi()),
    re_path(r'ws/projects/(?P<project_id>[^/]+)/logs/$', consumers.ProjectLogsConsumer.as_asgi()),
    re_path(r'ws/projects/(?P<project_id>[^/]+)/container/$', consumers.ContainerLogsConsumer.as_asgi()),
    re_path(r'ws/projects/(?P<project_id>[^/]+)/ai_streaming/$', consumers.AIStreamingConsumer.as_asgi()),
]