#!/usr/bin/env python
"""
Django ASGI Server with WebSocket Support
Run this script to start Django with WebSocket functionality enabled
"""
import os
import sys
import subprocess

def main():
    print("🚀 Starting Django with WebSocket support...")
    print("🔗 WebSocket endpoints: ws://localhost:8000/ws/")
    print("📡 API endpoints: http://localhost:8000/api/")
    print("🌐 Admin: http://localhost:8000/admin/")
    print("\nMake sure to run migrations first:")
    print("  python manage.py migrate")
    print("\nPress Ctrl+C to stop the server\n")
    
    # Set Django settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
    
    try:
        # Run daphne (ASGI server)
        cmd = [
            sys.executable, '-m', 'daphne',
            '-b', '0.0.0.0',
            '-p', '8000',
            'core.asgi:application'
        ]
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n👋 Server stopped.")
    except FileNotFoundError:
        print("❌ Daphne not found. Installing...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'daphne'])
        print("✅ Daphne installed. Please run the script again.")

if __name__ == '__main__':
    main()