import os
import re
import logging
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class DjangoIntegrator:
    """
    Service to properly integrate AI-generated Django code with existing Django project structure.
    This ensures apps are registered, URLs are included, and settings are updated.
    """
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.main_project_dir = self._find_main_project_dir()
        
    def _find_main_project_dir(self) -> Optional[Path]:
        """Find the main Django project directory (contains settings.py)"""
        for item in self.project_path.iterdir():
            if item.is_dir() and (item / 'settings.py').exists():
                return item
        return None
    
    def integrate_ai_generated_code(self, ai_files: List[Dict]) -> Dict:
        """
        Integrate AI-generated files with existing Django project structure.
        
        Args:
            ai_files: List of AI-generated files with path and content
            
        Returns:
            dict: Integration results with success status and details
        """
        results = {
            'success': True,
            'apps_registered': [],
            'urls_included': [],
            'settings_updated': [],
            'errors': []
        }
        
        try:
            # 1. Identify Django apps in AI-generated files
            ai_apps = self._identify_django_apps(ai_files)
            logger.info(f"Identified AI-generated apps: {ai_apps}")
            
            # 2. Register apps in INSTALLED_APPS
            for app_name in ai_apps:
                if self._register_app_in_settings(app_name):
                    results['apps_registered'].append(app_name)
                else:
                    results['errors'].append(f"Failed to register app: {app_name}")
            
            # 3. Include app URLs in main project URLs
            for app_name in ai_apps:
                if self._include_app_urls(app_name):
                    results['urls_included'].append(app_name)
                else:
                    results['errors'].append(f"Failed to include URLs for app: {app_name}")
            
            # 4. Update settings for AI-generated requirements
            settings_updates = self._update_settings_for_ai_code(ai_files)
            results['settings_updated'] = settings_updates
            
            if results['errors']:
                results['success'] = False
                
        except Exception as e:
            logger.error(f"Error integrating AI-generated code: {e}")
            results['success'] = False
            results['errors'].append(str(e))
        
        return results
    
    def _identify_django_apps(self, ai_files: List[Dict]) -> List[str]:
        """Identify Django apps from AI-generated files"""
        apps = set()
        
        for file_info in ai_files:
            file_path = file_info['path']
            
            # Check if file is part of a Django app (has models.py, views.py, etc.)
            if '/' in file_path:
                potential_app = file_path.split('/')[0]
                
                # Check if it's a valid Django app directory
                app_indicators = ['models.py', 'views.py', 'urls.py', 'admin.py', 'apps.py']
                
                for indicator in app_indicators:
                    if file_path.endswith(indicator) or f'{potential_app}/{indicator}' in [f['path'] for f in ai_files]:
                        apps.add(potential_app)
                        break
        
        return list(apps)
    
    def _register_app_in_settings(self, app_name: str) -> bool:
        """Register Django app in INSTALLED_APPS"""
        if not self.main_project_dir:
            return False
        
        settings_path = self.main_project_dir / 'settings.py'
        
        try:
            with open(settings_path, 'r') as f:
                content = f.read()
            
            # Check if app is already registered
            if f"'{app_name}'" in content or f'"{app_name}"' in content:
                logger.info(f"App {app_name} already registered in settings")
                return True
            
            # Find INSTALLED_APPS and add the app
            pattern = r'(INSTALLED_APPS\s*=\s*\[)(.*?)(\])'
            match = re.search(pattern, content, re.DOTALL)
            
            if match:
                before = match.group(1)
                apps_content = match.group(2)
                after = match.group(3)
                
                # Add the new app
                new_app_entry = f"    '{app_name}',\n"
                new_apps_content = apps_content.rstrip() + '\n' + new_app_entry
                
                new_content = content.replace(
                    match.group(0),
                    before + new_apps_content + after
                )
                
                with open(settings_path, 'w') as f:
                    f.write(new_content)
                
                logger.info(f"Successfully registered app {app_name} in settings")
                return True
            
        except Exception as e:
            logger.error(f"Error registering app {app_name}: {e}")
        
        return False
    
    def _include_app_urls(self, app_name: str) -> bool:
        """Include app URLs in main project URLs"""
        if not self.main_project_dir:
            return False
        
        urls_path = self.main_project_dir / 'urls.py'
        
        try:
            with open(urls_path, 'r') as f:
                content = f.read()
            
            # Check if app URLs are already included
            if f"'{app_name}.urls'" in content or f'"{app_name}.urls"' in content:
                logger.info(f"URLs for {app_name} already included")
                return True
            
            # Check if the app has a urls.py file
            app_urls_path = self.project_path / app_name / 'urls.py'
            if not app_urls_path.exists():
                logger.info(f"No urls.py found for app {app_name}, skipping URL inclusion")
                return True
            
            # Add include import if not present
            if 'include' not in content or 'from django.urls import include' not in content:
                # Find the import section and add include
                import_pattern = r'from django\.urls import ([^\n]+)'
                match = re.search(import_pattern, content)
                if match:
                    imports = match.group(1).strip()
                    if 'include' not in imports:
                        # Add include to existing import
                        if imports.endswith(','):
                            new_imports = imports + ' include'
                        else:
                            new_imports = imports + ', include'
                        
                        old_import_line = match.group(0)
                        new_import_line = f'from django.urls import {new_imports}'
                        content = content.replace(old_import_line, new_import_line)
                        logger.info(f"Updated import line: {new_import_line}")
                else:
                    # Add include import as new line if no django.urls import found
                    lines = content.split('\n')
                    admin_import_idx = -1
                    for i, line in enumerate(lines):
                        if 'from django.contrib import admin' in line:
                            admin_import_idx = i
                            break
                    
                    if admin_import_idx >= 0:
                        lines.insert(admin_import_idx + 1, 'from django.urls import path, include')
                        content = '\n'.join(lines)
                        logger.info("Added new django.urls import line")
            
            # Find urlpatterns and add the app URL
            pattern = r'(urlpatterns\s*=\s*\[)(.*?)(\])'
            match = re.search(pattern, content, re.DOTALL)
            
            if match:
                before = match.group(1)
                urls_content = match.group(2)
                after = match.group(3)
                
                # Add the new URL pattern - use empty path for main app
                if app_name == 'main':
                    new_url_entry = f"    path('', include('{app_name}.urls')),\n"
                else:
                    new_url_entry = f"    path('{app_name}/', include('{app_name}.urls')),\n"
                new_urls_content = urls_content.rstrip() + '\n' + new_url_entry
                
                new_content = content.replace(
                    match.group(0),
                    before + new_urls_content + after
                )
                
                with open(urls_path, 'w') as f:
                    f.write(new_content)
                
                logger.info(f"Successfully included URLs for app {app_name}")
                return True
            
        except Exception as e:
            logger.error(f"Error including URLs for app {app_name}: {e}")
        
        return False
    
    def _update_settings_for_ai_code(self, ai_files: List[Dict]) -> List[str]:
        """Update Django settings based on AI-generated code requirements"""
        updates = []
        
        if not self.main_project_dir:
            return updates
        
        settings_path = self.main_project_dir / 'settings.py'
        
        try:
            with open(settings_path, 'r') as f:
                content = f.read()
            
            # Check if AI code uses Django REST Framework
            needs_drf = any(
                'rest_framework' in file_info['content'] or 
                'serializers' in file_info['content']
                for file_info in ai_files
            )
            
            if needs_drf and 'rest_framework' not in content:
                # Add REST framework to INSTALLED_APPS
                pattern = r'(INSTALLED_APPS\s*=\s*\[)(.*?)(\])'
                match = re.search(pattern, content, re.DOTALL)
                
                if match:
                    before = match.group(1)
                    apps_content = match.group(2)
                    after = match.group(3)
                    
                    new_app_entry = "    'rest_framework',\n"
                    new_apps_content = apps_content.rstrip() + '\n' + new_app_entry
                    
                    content = content.replace(
                        match.group(0),
                        before + new_apps_content + after
                    )
                    
                    updates.append('rest_framework')
            
            # Update ALLOWED_HOSTS for development
            if 'ALLOWED_HOSTS = []' in content:
                content = content.replace(
                    'ALLOWED_HOSTS = []',
                    "ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']"
                )
                updates.append('ALLOWED_HOSTS')
            
            # Configure iframe settings for preview functionality
            if 'X_FRAME_OPTIONS' not in content:
                # Add iframe settings at the end of the file
                iframe_settings = '''
# Allow iframe embedding for development preview
X_FRAME_OPTIONS = 'ALLOWALL'
SECURE_FRAME_DENY = False
'''
                content += iframe_settings
                updates.append('iframe_settings')
            
            # Comment out XFrameOptionsMiddleware to allow iframe embedding
            if 'django.middleware.clickjacking.XFrameOptionsMiddleware' in content:
                content = content.replace(
                    "'django.middleware.clickjacking.XFrameOptionsMiddleware',",
                    "# 'django.middleware.clickjacking.XFrameOptionsMiddleware',  # Commented out to allow iframe embedding"
                )
                updates.append('XFrameOptionsMiddleware')
            
            # Write updated settings
            with open(settings_path, 'w') as f:
                f.write(content)
            
        except Exception as e:
            logger.error(f"Error updating settings: {e}")
        
        return updates
    
    def create_missing_app_files(self, app_name: str) -> bool:
        """Create missing Django app files like __init__.py, apps.py"""
        app_path = self.project_path / app_name
        
        if not app_path.exists():
            return False
        
        try:
            # Create __init__.py if missing
            init_file = app_path / '__init__.py'
            if not init_file.exists():
                init_file.touch()
            
            # Create apps.py if missing
            apps_file = app_path / 'apps.py'
            if not apps_file.exists():
                apps_content = f'''from django.apps import AppConfig


class {app_name.capitalize()}Config(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = '{app_name}'
'''
                with open(apps_file, 'w') as f:
                    f.write(apps_content)
            
            # Create migrations directory if missing
            migrations_dir = app_path / 'migrations'
            if not migrations_dir.exists():
                migrations_dir.mkdir()
                (migrations_dir / '__init__.py').touch()
            
            return True
            
        except Exception as e:
            logger.error(f"Error creating missing app files for {app_name}: {e}")
            return False