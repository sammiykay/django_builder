"""
Django AI Builder Validation Service

Implements comprehensive safety measures for generated code:
- Jinja2 template safety and validation
- Import and module testing after generation
- Django project checks integration
- Proper generation sequence enforcement
- Static linting integration
- Helpful error reporting instead of crashes
"""

import os
import sys
import ast
import importlib
import subprocess
import tempfile
import traceback
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum
import logging

try:
    import jinja2
    from jinja2 import Environment, FileSystemLoader, meta, TemplateSyntaxError
    from jinja2.sandbox import SandboxedEnvironment
except ImportError:
    jinja2 = None

logger = logging.getLogger(__name__)


class ValidationLevel(Enum):
    """Validation severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationResult:
    """Result of a validation check"""
    level: ValidationLevel
    message: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    suggestion: Optional[str] = None
    code_snippet: Optional[str] = None


class GenerationSequence:
    """Enforces proper Django component generation sequence"""
    
    SEQUENCE_ORDER = [
        'models',
        'serializers', 
        'views',
        'urls',
        'settings',
        'templates',
        'static',
        'migrations'
    ]
    
    DEPENDENCIES = {
        'serializers': ['models'],
        'views': ['models', 'serializers'],
        'urls': ['views'],
        'migrations': ['models'],
        'templates': ['views'],
    }


class SafeTemplateEngine:
    """Jinja2-based safe template engine with validation"""
    
    def __init__(self, template_dir: Optional[str] = None):
        """Initialize safe template engine"""
        if not jinja2:
            raise ImportError("Jinja2 is required for safe template rendering")
            
        # Use sandboxed environment for safety
        self.env = SandboxedEnvironment(
            loader=FileSystemLoader(template_dir) if template_dir else None,
            autoescape=True,
            undefined=jinja2.StrictUndefined  # Fail on undefined variables
        )
        
        # Register safe filters
        self.env.filters.update({
            'safe_name': self._safe_name_filter,
            'snake_case': self._snake_case_filter,
            'camel_case': self._camel_case_filter,
            'pascal_case': self._pascal_case_filter,
        })
    
    def _safe_name_filter(self, value: str) -> str:
        """Convert to safe Python identifier"""
        import re
        # Remove non-alphanumeric chars, convert to snake_case
        safe = re.sub(r'[^a-zA-Z0-9_]', '_', str(value))
        safe = re.sub(r'_+', '_', safe)  # Remove multiple underscores
        safe = safe.strip('_')  # Remove leading/trailing underscores
        
        # Ensure it doesn't start with a number
        if safe and safe[0].isdigit():
            safe = f"item_{safe}"
            
        return safe or 'default'
    
    def _snake_case_filter(self, value: str) -> str:
        """Convert to snake_case"""
        import re
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', str(value))
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
    
    def _camel_case_filter(self, value: str) -> str:
        """Convert to camelCase"""
        components = str(value).split('_')
        return components[0].lower() + ''.join(x.capitalize() for x in components[1:])
    
    def _pascal_case_filter(self, value: str) -> str:
        """Convert to PascalCase"""
        return ''.join(x.capitalize() for x in str(value).split('_'))
    
    def validate_template(self, template_content: str) -> List[ValidationResult]:
        """Validate template syntax and variables"""
        results = []
        
        try:
            # Parse template for syntax errors
            self.env.parse(template_content)
            
            # Extract undefined variables
            ast_nodes = self.env.parse(template_content)
            undefined_vars = meta.find_undeclared_variables(ast_nodes)
            
            if undefined_vars:
                results.append(ValidationResult(
                    level=ValidationLevel.WARNING,
                    message=f"Template contains undefined variables: {', '.join(undefined_vars)}",
                    suggestion="Ensure all variables are provided in template context"
                ))
                
        except TemplateSyntaxError as e:
            results.append(ValidationResult(
                level=ValidationLevel.ERROR,
                message=f"Template syntax error: {e.message}",
                line_number=e.lineno,
                suggestion="Fix template syntax according to Jinja2 documentation"
            ))
        except Exception as e:
            results.append(ValidationResult(
                level=ValidationLevel.ERROR,
                message=f"Template validation error: {str(e)}",
                suggestion="Check template for syntax issues"
            ))
            
        return results
    
    def render_safe(self, template_content: str, context: Dict[str, Any]) -> Tuple[str, List[ValidationResult]]:
        """Safely render template with validation"""
        validation_results = self.validate_template(template_content)
        
        # Filter out only critical errors that prevent rendering
        critical_errors = [r for r in validation_results if r.level == ValidationLevel.CRITICAL]
        if critical_errors:
            return "", validation_results
        
        try:
            template = self.env.from_string(template_content)
            rendered = template.render(**context)
            return rendered, validation_results
        except Exception as e:
            validation_results.append(ValidationResult(
                level=ValidationLevel.ERROR,
                message=f"Template rendering failed: {str(e)}",
                suggestion="Check template syntax and context variables"
            ))
            return "", validation_results


class PythonValidator:
    """Python code validation and import testing"""
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
    
    def validate_syntax(self, file_path: str) -> List[ValidationResult]:
        """Validate Python syntax"""
        results = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Parse AST to check syntax
            ast.parse(content, filename=file_path)
            
            results.append(ValidationResult(
                level=ValidationLevel.INFO,
                message="Python syntax is valid",
                file_path=file_path
            ))
            
        except SyntaxError as e:
            results.append(ValidationResult(
                level=ValidationLevel.ERROR,
                message=f"Syntax error: {e.msg}",
                file_path=file_path,
                line_number=e.lineno,
                suggestion="Fix Python syntax error",
                code_snippet=self._get_code_snippet(file_path, e.lineno) if e.lineno else None
            ))
        except Exception as e:
            results.append(ValidationResult(
                level=ValidationLevel.ERROR,
                message=f"Failed to validate syntax: {str(e)}",
                file_path=file_path
            ))
            
        return results
    
    def test_imports(self, file_path: str) -> List[ValidationResult]:
        """Test if all imports in a file work"""
        results = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse imports from the file
            tree = ast.parse(content)
            imports = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ''
                    for alias in node.names:
                        if alias.name == '*':
                            imports.append(module)
                        else:
                            imports.append(f"{module}.{alias.name}" if module else alias.name)
            
            # Test each import
            for import_name in imports:
                try:
                    # Try to import the module
                    if '.' in import_name:
                        module_path, attr = import_name.rsplit('.', 1)
                        module = importlib.import_module(module_path)
                        if hasattr(module, attr):
                            results.append(ValidationResult(
                                level=ValidationLevel.INFO,
                                message=f"Import '{import_name}' is valid",
                                file_path=file_path
                            ))
                        else:
                            results.append(ValidationResult(
                                level=ValidationLevel.WARNING,
                                message=f"Attribute '{attr}' not found in module '{module_path}'",
                                file_path=file_path,
                                suggestion=f"Check if '{attr}' exists in '{module_path}'"
                            ))
                    else:
                        importlib.import_module(import_name)
                        results.append(ValidationResult(
                            level=ValidationLevel.INFO,
                            message=f"Module '{import_name}' imported successfully",
                            file_path=file_path
                        ))
                        
                except ImportError as e:
                    results.append(ValidationResult(
                        level=ValidationLevel.WARNING,
                        message=f"Import error for '{import_name}': {str(e)}",
                        file_path=file_path,
                        suggestion=f"Install required package or check import path for '{import_name}'"
                    ))
                except Exception as e:
                    results.append(ValidationResult(
                        level=ValidationLevel.WARNING,
                        message=f"Unexpected error testing import '{import_name}': {str(e)}",
                        file_path=file_path
                    ))
                    
        except Exception as e:
            results.append(ValidationResult(
                level=ValidationLevel.ERROR,
                message=f"Failed to test imports: {str(e)}",
                file_path=file_path
            ))
            
        return results
    
    def _get_code_snippet(self, file_path: str, line_number: int, context: int = 3) -> str:
        """Get code snippet around a specific line"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            start = max(0, line_number - context - 1)
            end = min(len(lines), line_number + context)
            
            snippet_lines = []
            for i in range(start, end):
                prefix = ">>> " if i == line_number - 1 else "    "
                snippet_lines.append(f"{prefix}{i+1:3}: {lines[i].rstrip()}")
            
            return '\n'.join(snippet_lines)
        except:
            return ""


class DjangoValidator:
    """Django-specific validation using manage.py check"""
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
    
    def run_django_check(self) -> List[ValidationResult]:
        """Run Django's built-in check command"""
        results = []
        
        # Look for manage.py
        manage_py = self.project_path / "manage.py"
        if not manage_py.exists():
            results.append(ValidationResult(
                level=ValidationLevel.WARNING,
                message="manage.py not found - skipping Django checks",
                suggestion="Ensure Django project is properly structured"
            ))
            return results
        
        try:
            # Run Django check command
            cmd = [sys.executable, str(manage_py), "check", "--deploy"]
            
            # Set environment
            env = os.environ.copy()
            env['PYTHONPATH'] = str(self.project_path.parent)
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(self.project_path),
                env=env,
                timeout=30
            )
            
            if result.returncode == 0:
                results.append(ValidationResult(
                    level=ValidationLevel.INFO,
                    message="Django check passed successfully",
                    suggestion="Project structure is valid"
                ))
            else:
                # Parse Django check output
                error_lines = result.stderr.split('\n') if result.stderr else []
                output_lines = result.stdout.split('\n') if result.stdout else []
                
                for line in error_lines + output_lines:
                    line = line.strip()
                    if not line:
                        continue
                        
                    if 'ERROR' in line or 'CRITICAL' in line:
                        level = ValidationLevel.ERROR
                    elif 'WARNING' in line:
                        level = ValidationLevel.WARNING
                    else:
                        level = ValidationLevel.INFO
                    
                    results.append(ValidationResult(
                        level=level,
                        message=f"Django check: {line}",
                        suggestion="Fix the reported Django issue"
                    ))
                        
        except subprocess.TimeoutExpired:
            results.append(ValidationResult(
                level=ValidationLevel.WARNING,
                message="Django check timed out",
                suggestion="Check for infinite loops or blocking operations"
            ))
        except Exception as e:
            results.append(ValidationResult(
                level=ValidationLevel.WARNING,
                message=f"Failed to run Django check: {str(e)}",
                suggestion="Ensure Django is properly installed and configured"
            ))
            
        return results


class StaticLinter:
    """Static code analysis with flake8 and pylint"""
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
    
    def run_flake8(self, file_path: str) -> List[ValidationResult]:
        """Run flake8 linting"""
        results = []
        
        try:
            cmd = ["flake8", file_path, "--max-line-length=100", "--ignore=E501,W503"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                results.append(ValidationResult(
                    level=ValidationLevel.INFO,
                    message="Flake8 linting passed",
                    file_path=file_path
                ))
            else:
                for line in result.stdout.split('\n'):
                    if line.strip():
                        parts = line.split(':', 3)
                        if len(parts) >= 4:
                            file_name, line_num, col, message = parts
                            results.append(ValidationResult(
                                level=ValidationLevel.WARNING,
                                message=f"Flake8: {message.strip()}",
                                file_path=file_path,
                                line_number=int(line_num) if line_num.isdigit() else None,
                                suggestion="Fix the linting issue"
                            ))
                        
        except FileNotFoundError:
            results.append(ValidationResult(
                level=ValidationLevel.INFO,
                message="Flake8 not installed - skipping lint checks",
                suggestion="Install flake8 for code quality checks: pip install flake8"
            ))
        except Exception as e:
            results.append(ValidationResult(
                level=ValidationLevel.WARNING,
                message=f"Flake8 error: {str(e)}",
                file_path=file_path
            ))
            
        return results
    
    def run_pylint(self, file_path: str) -> List[ValidationResult]:
        """Run pylint analysis"""
        results = []
        
        try:
            cmd = ["pylint", file_path, "--output-format=json", "--disable=C0114,C0115,C0116"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.stdout:
                import json
                try:
                    pylint_results = json.loads(result.stdout)
                    for item in pylint_results:
                        level_map = {
                            'error': ValidationLevel.ERROR,
                            'warning': ValidationLevel.WARNING,
                            'refactor': ValidationLevel.INFO,
                            'convention': ValidationLevel.INFO
                        }
                        
                        level = level_map.get(item.get('type', 'info'), ValidationLevel.INFO)
                        
                        results.append(ValidationResult(
                            level=level,
                            message=f"Pylint: {item.get('message', 'Unknown issue')}",
                            file_path=file_path,
                            line_number=item.get('line'),
                            suggestion="Address the pylint suggestion"
                        ))
                except json.JSONDecodeError:
                    # Fallback to text parsing
                    pass
                    
        except FileNotFoundError:
            results.append(ValidationResult(
                level=ValidationLevel.INFO,
                message="Pylint not installed - skipping advanced analysis",
                suggestion="Install pylint for detailed code analysis: pip install pylint"
            ))
        except Exception as e:
            results.append(ValidationResult(
                level=ValidationLevel.WARNING,
                message=f"Pylint error: {str(e)}",
                file_path=file_path
            ))
            
        return results


class ValidationService:
    """Comprehensive validation service for Django AI Builder"""
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.template_engine = SafeTemplateEngine()
        self.python_validator = PythonValidator(str(project_path))
        self.django_validator = DjangoValidator(str(project_path))
        self.linter = StaticLinter(str(project_path))
        self.sequence_tracker = {}
    
    def validate_generation_sequence(self, component_type: str, dependencies: List[str] = None) -> List[ValidationResult]:
        """Validate proper generation sequence"""
        results = []
        dependencies = dependencies or GenerationSequence.DEPENDENCIES.get(component_type, [])
        
        # Check if dependencies are satisfied
        missing_deps = []
        for dep in dependencies:
            if dep not in self.sequence_tracker:
                missing_deps.append(dep)
        
        if missing_deps:
            results.append(ValidationResult(
                level=ValidationLevel.WARNING,
                message=f"Generating {component_type} before dependencies: {', '.join(missing_deps)}",
                suggestion=f"Consider generating {', '.join(missing_deps)} first for better reliability"
            ))
        
        # Track this component as completed
        self.sequence_tracker[component_type] = True
        
        return results
    
    def validate_file(self, file_path: str, check_imports: bool = True, run_linting: bool = False) -> List[ValidationResult]:
        """Comprehensive file validation"""
        results = []
        
        if not Path(file_path).exists():
            results.append(ValidationResult(
                level=ValidationLevel.ERROR,
                message=f"File does not exist: {file_path}",
                file_path=file_path
            ))
            return results
        
        # Python syntax validation
        if file_path.endswith('.py'):
            results.extend(self.python_validator.validate_syntax(file_path))
            
            # Import testing
            if check_imports:
                results.extend(self.python_validator.test_imports(file_path))
            
            # Static linting
            if run_linting:
                results.extend(self.linter.run_flake8(file_path))
                # results.extend(self.linter.run_pylint(file_path))  # Uncomment for pylint
        
        return results
    
    def validate_template(self, template_content: str, context: Dict[str, Any] = None) -> Tuple[str, List[ValidationResult]]:
        """Validate and render template safely"""
        context = context or {}
        return self.template_engine.render_safe(template_content, context)
    
    def validate_project(self, run_django_check: bool = True) -> List[ValidationResult]:
        """Comprehensive project validation"""
        results = []
        
        # Django checks
        if run_django_check:
            results.extend(self.django_validator.run_django_check())
        
        # Validate all Python files in project
        for py_file in self.project_path.rglob("*.py"):
            if not any(part.startswith('.') for part in py_file.parts):  # Skip hidden dirs
                file_results = self.validate_file(str(py_file), check_imports=True)
                results.extend(file_results)
        
        return results
    
    def format_results(self, results: List[ValidationResult]) -> str:
        """Format validation results for user display"""
        if not results:
            return "✅ All validations passed successfully!"
        
        # Group by level
        by_level = {level: [] for level in ValidationLevel}
        for result in results:
            by_level[result.level].append(result)
        
        output = []
        
        # Show critical/errors first
        for level in [ValidationLevel.CRITICAL, ValidationLevel.ERROR, ValidationLevel.WARNING, ValidationLevel.INFO]:
            items = by_level[level]
            if not items:
                continue
                
            level_icon = {
                ValidationLevel.CRITICAL: "🚨",
                ValidationLevel.ERROR: "❌", 
                ValidationLevel.WARNING: "⚠️",
                ValidationLevel.INFO: "ℹ️"
            }
            
            output.append(f"\n{level_icon[level]} {level.value.upper()} ({len(items)} issues):")
            
            for result in items:
                msg = f"  • {result.message}"
                if result.file_path:
                    msg += f" ({Path(result.file_path).name}"
                    if result.line_number:
                        msg += f":{result.line_number}"
                    msg += ")"
                
                output.append(msg)
                
                if result.suggestion:
                    output.append(f"    💡 {result.suggestion}")
                    
                if result.code_snippet:
                    output.append(f"    📄 Code:")
                    for line in result.code_snippet.split('\n'):
                        output.append(f"       {line}")
        
        return '\n'.join(output)