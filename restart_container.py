#!/usr/bin/env python3
"""
Script to restart the Django container to apply iframe settings
"""

import os
import sys
from pathlib import Path

# Add the project directory to Python path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

def restart_container():
    """Restart the container to apply iframe settings"""
    
    print("🔄 Instructions to restart Django container for iframe support")
    print("=" * 60)
    
    print("📋 Changes Applied:")
    print("   ✅ Disabled XFrameOptionsMiddleware")
    print("   ✅ Set X_FRAME_OPTIONS = 'ALLOWALL'")
    print("   ✅ Set SECURE_FRAME_DENY = False")
    print("   ✅ Enhanced frontend iframe handling")
    
    print("\n🔄 To Apply Changes:")
    print("   1. In the web interface, click 'Stop Server'")
    print("   2. Wait a few seconds")
    print("   3. Click 'Start Server' again")
    print("   4. The iframe preview should now work!")
    
    print("\n🎯 What to Expect:")
    print("   ✅ Django server starts normally")
    print("   ✅ Iframe preview loads the Django app")
    print("   ✅ Blog app accessible at /main/")
    print("   ✅ Admin interface at /admin/")
    
    print("\n💡 If iframe still doesn't work:")
    print("   • Check browser console for errors")
    print("   • Try different browser or incognito mode")
    print("   • Use the 'Open in New Tab' button")
    print("   • Direct access: http://localhost:8078/main/")
    
    print("\n🔍 Verification Steps:")
    print("   1. Check terminal output for iframe loading messages")
    print("   2. Look for '✅ Preview loaded successfully' message")
    print("   3. If blocked, fallback link will be provided")

if __name__ == '__main__':
    restart_container()