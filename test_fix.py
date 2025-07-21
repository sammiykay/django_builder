#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append('/mnt/c/users/sammiykay/desktop/projects/django_ai_builder')

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from ai_builder.services.smart_project_generator import SmartProjectGenerator

def test_fix():
    """Test fixing existing broken projects."""
    
    generator = SmartProjectGenerator('./user_projects')
    
    # Test fixing the e-commerce project we identified
    project_id = 'f6367868-0fda-4a64-8222-d2772a2f53c3'
    print(f"Testing fix for project: {project_id}")
    
    result = generator.fix_incomplete_project(project_id)
    
    if result['success']:
        print(f"✅ Successfully fixed {len(result['fixed_files'])} files")
        for file_info in result['fixed_files']:
            print(f"  - Generated {file_info['file_type']} for {file_info['app_name']}")
    else:
        print(f"❌ Failed to fix project: {result['error']}")
    
    return result

if __name__ == '__main__':
    test_fix()