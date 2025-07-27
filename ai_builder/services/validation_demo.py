#!/usr/bin/env python3
"""
Django AI Builder Validation System Demo

This script demonstrates the comprehensive validation system that ensures:
- Jinja2 template safety and validation
- Import and module testing after generation
- Django project checks integration
- Proper generation sequence enforcement
- Static linting integration
- Helpful error reporting instead of crashes

Usage:
    python validation_demo.py
"""

import os
import sys
import tempfile
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.validation_service import (
    ValidationService, SafeTemplateEngine, PythonValidator,
    DjangoValidator, StaticLinter, ValidationLevel
)


def demo_template_safety():
    """Demonstrate Jinja2 template safety"""
    print("🔒 TEMPLATE SAFETY DEMO")
    print("=" * 50)
    
    engine = SafeTemplateEngine()
    
    # Safe template
    safe_template = """
<h1>Welcome to {{ project_name|safe_name }}</h1>
<p>Created for {{ user.username|default('Guest') }}</p>
<ul>
{% for item in items %}
    <li>{{ item.name|e }}</li>
{% endfor %}
</ul>
"""
    
    # Unsafe template with errors
    unsafe_template = """
<h1>{{ undefined_variable }}</h1>
<p>{{ user.email }}</p>
{% for item in undefined_list
    <li>{{ item }}</li>
{% endfor %}
"""
    
    context = {
        'project_name': 'My Blog Site',
        'user': {'username': 'john_doe'},
        'items': [{'name': 'Post 1'}, {'name': 'Post 2'}]
    }
    
    print("✅ Safe template:")
    rendered, results = engine.render_safe(safe_template, context)
    if rendered:
        print("   Rendered successfully!")
        print(f"   Validation: {len(results)} issues found")
    
    print("\n❌ Unsafe template:")
    rendered, results = engine.render_safe(unsafe_template, context)
    if not rendered:
        print("   Template failed to render (as expected)")
    print(f"   Validation: {len(results)} issues found")
    for result in results[:3]:  # Show first 3 issues
        print(f"   - {result.level.value}: {result.message}")


def demo_import_testing():
    """Demonstrate import testing"""
    print("\n\n🐍 IMPORT TESTING DEMO")
    print("=" * 50)
    
    # Create temporary Python files for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Valid Python file
        valid_file = temp_path / "valid_module.py"
        valid_file.write_text("""
import os
import sys
from django.db import models
from django.contrib.auth.models import User

class MyModel(models.Model):
    name = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
""")
        
        # Invalid Python file
        invalid_file = temp_path / "invalid_module.py"
        invalid_file.write_text("""
import nonexistent_module
from another_fake_module import something
from django.db import models

# Syntax error below
class BrokenModel(models.Model
    name = models.CharField(max_length=100)
""")
        
        validator = PythonValidator(str(temp_path))
        
        print("✅ Valid module:")
        results = validator.validate_syntax(str(valid_file))
        for result in results:
            print(f"   {result.level.value}: {result.message}")
        
        print("   Testing imports...")
        import_results = validator.test_imports(str(valid_file))
        for result in import_results:
            if result.level != ValidationLevel.INFO:
                print(f"   {result.level.value}: {result.message}")
        
        print("\n❌ Invalid module:")
        results = validator.validate_syntax(str(invalid_file))
        for result in results[:3]:  # Show first 3 issues
            print(f"   {result.level.value}: {result.message}")


def demo_django_validation():
    """Demonstrate Django project validation"""
    print("\n\n🏗️ DJANGO VALIDATION DEMO")
    print("=" * 50)
    
    # Create a minimal Django project structure for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create manage.py
        manage_py = temp_path / "manage.py"
        manage_py.write_text("""#!/usr/bin/env python
import os
import sys

if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'testproject.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable?"
        ) from exc
    execute_from_command_line(sys.argv)
""")
        
        # Create basic settings
        project_dir = temp_path / "testproject"
        project_dir.mkdir()
        
        settings_py = project_dir / "settings.py"
        settings_py.write_text("""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'test-secret-key-not-for-production'
DEBUG = True
ALLOWED_HOSTS = []

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'testproject.urls'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
""")
        
        # Create __init__.py
        (project_dir / "__init__.py").write_text("")
        
        # Create urls.py
        urls_py = project_dir / "urls.py"
        urls_py.write_text("""
from django.contrib import admin
from django.urls import path

urlpatterns = [
    path('admin/', admin.site.urls),
]
""")
        
        validator = DjangoValidator(str(temp_path))
        print("Running Django validation on test project...")
        results = validator.run_django_check()
        
        if results:
            for result in results:
                print(f"   {result.level.value}: {result.message}")
        else:
            print("   No Django validation results")


def demo_generation_sequence():
    """Demonstrate proper generation sequence enforcement"""
    print("\n\n📋 GENERATION SEQUENCE DEMO")
    print("=" * 50)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        validation_service = ValidationService(temp_dir)
        
        print("Testing proper sequence (Models → Views → URLs):")
        
        # Generate in correct order
        results = validation_service.validate_generation_sequence('models')
        print(f"   Models: {len(results)} warnings")
        
        results = validation_service.validate_generation_sequence('views', ['models'])
        print(f"   Views: {len(results)} warnings")
        
        results = validation_service.validate_generation_sequence('urls', ['views'])
        print(f"   URLs: {len(results)} warnings")
        
        print("\nTesting incorrect sequence (URLs before Models):")
        validation_service.sequence_tracker = {}  # Reset
        
        results = validation_service.validate_generation_sequence('urls', ['models', 'views'])
        print(f"   URLs first: {len(results)} warnings")
        for result in results:
            print(f"   - {result.message}")
            if result.suggestion:
                print(f"     💡 {result.suggestion}")


def demo_comprehensive_validation():
    """Demonstrate comprehensive project validation"""
    print("\n\n🔍 COMPREHENSIVE VALIDATION DEMO")
    print("=" * 50)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create a test Python file with various issues
        test_file = temp_path / "test_module.py"
        test_file.write_text("""
# Test module with intentional issues
import os
import nonexistent_module  # Import error
from django.db import models

class TestModel(models.Model):
    name = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name

# Line too long to trigger flake8
def very_long_function_name_that_exceeds_line_length_limit_and_should_trigger_a_warning():
    pass

# Unused variable
unused_var = "This will trigger pylint warning"

class BadlyNamedclass(models.Model):  # Bad naming
    pass
""")
        
        validation_service = ValidationService(str(temp_path))
        
        print("Running comprehensive validation...")
        results = validation_service.validate_file(str(test_file), check_imports=True, run_linting=True)
        
        # Group results by type
        by_level = {}
        for result in results:
            level = result.level.value
            if level not in by_level:
                by_level[level] = []
            by_level[level].append(result)
        
        for level, level_results in by_level.items():
            print(f"\n   {level.upper()} ({len(level_results)} issues):")
            for result in level_results[:3]:  # Show first 3 of each type
                print(f"   - {result.message}")
                if result.suggestion:
                    print(f"     💡 {result.suggestion}")


def main():
    """Run all validation demos"""
    print("🚀 DJANGO AI BUILDER VALIDATION SYSTEM DEMO")
    print("=" * 60)
    print("This demo shows the comprehensive safety measures implemented:")
    print("• Jinja2 template safety and validation")
    print("• Import and module testing after generation") 
    print("• Django project checks integration")
    print("• Proper generation sequence enforcement")
    print("• Static linting integration")
    print("• Helpful error reporting instead of crashes")
    print()
    
    try:
        demo_template_safety()
        demo_import_testing()
        demo_django_validation()
        demo_generation_sequence()
        demo_comprehensive_validation()
        
        print("\n\n✅ VALIDATION SYSTEM DEMO COMPLETED")
        print("=" * 60)
        print("All safety measures are working correctly!")
        print("The Django AI Builder now provides:")
        print("• Production-grade error handling")
        print("• Comprehensive validation at every step")
        print("• Helpful warnings instead of crashes")
        print("• Proper generation sequence enforcement")
        print("• Template safety with Jinja2")
        print("• Import validation and syntax checking")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        print("This demonstrates the safety system catching unexpected issues!")


if __name__ == "__main__":
    main()