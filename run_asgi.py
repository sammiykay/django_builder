#!/usr/bin/env python
"""
ASGI Development Server Runner for WebSocket Support
Run this instead of `python manage.py runserver` to enable WebSocket functionality
"""
import os
import django
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter
import uvicorn

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

# Get ASGI application
application = get_asgi_application()

if __name__ == "__main__":
    print("🚀 Starting Django ASGI server with WebSocket support...")
    print("🔗 WebSocket endpoints available at ws://localhost:8000/ws/")
    print("📡 REST API available at http://localhost:8000/api/")
    print("🌐 Frontend should connect to http://localhost:8000")
    print("\nPress Ctrl+C to stop the server\n")
    
    uvicorn.run(
        "core.asgi:application",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )