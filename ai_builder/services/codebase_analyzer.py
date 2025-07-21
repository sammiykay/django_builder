"""
Codebase Analyzer for Django AI Builder
Provides deep understanding of project structure and code context like Bolt.new
"""

import os
import json
import logging
import zipfile
import tempfile
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from datetime import datetime
import ast
import re
from collections import defaultdict

logger = logging.getLogger(__name__)


class CodebaseAnalyzer:
    """
    Advanced codebase analysis system that understands project structure,
    dependencies, and relationships between files - similar to Bolt.new
    """
    
    def __init__(self, project_path: Path):
        self.project_path = Path(project_path)
        self.analysis_cache = {}
        self.file_dependencies = defaultdict(set)
        self.model_relationships = {}
        self.view_patterns = {}
        self.url_mappings = {}
        
    def analyze_full_codebase(self) -> Dict[str, Any]:
        """
        Perform comprehensive codebase analysis
        Returns complete project understanding for Claude
        """
        try:
            analysis = {
                'project_metadata': self._get_project_metadata(),
                'file_structure': self._get_detailed_file_structure(),
                'code_analysis': self._analyze_code_patterns(),
                'dependency_graph': self._build_dependency_graph(),
                'django_structure': self._analyze_django_structure(),
                'database_schema': self._analyze_database_schema(),
                'api_endpoints': self._analyze_api_endpoints(),
                'frontend_assets': self._analyze_frontend_assets(),
                'test_coverage': self._analyze_test_structure(),
                'code_quality': self._analyze_code_quality(),
                'recent_activity': self._get_recent_activity(),
                'context_summary': self._generate_context_summary()
            }
            
            # Cache the analysis
            self.analysis_cache = analysis
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error in full codebase analysis: {e}")
            return {
                'error': f"Failed to analyze codebase: {str(e)}",
                'timestamp': datetime.now().isoformat()
            }
    
    def _get_project_metadata(self) -> Dict:
        """Get basic project metadata"""
        metadata = {
            'project_name': self.project_path.name,
            'project_path': str(self.project_path),
            'analysis_timestamp': datetime.now().isoformat(),
            'total_files': 0,
            'total_lines': 0,
            'languages': {},
            'frameworks': []
        }
        
        # Count files and lines
        for file_path in self.project_path.rglob('*'):
            if file_path.is_file() and not self._should_ignore_file(file_path):
                metadata['total_files'] += 1
                
                # Count lines and detect language
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = len(f.readlines())
                        metadata['total_lines'] += lines
                        
                        # Track language statistics
                        ext = file_path.suffix.lower()
                        if ext:
                            metadata['languages'][ext] = metadata['languages'].get(ext, 0) + 1
                            
                except Exception as e:
                    logger.warning(f"Could not read file {file_path}: {e}")
        
        # Detect frameworks
        metadata['frameworks'] = self._detect_frameworks()
        
        return metadata
    
    def _get_detailed_file_structure(self) -> Dict:
        """Get detailed file structure with content summaries"""
        structure = {
            'directories': {},
            'files': {},
            'important_files': {}
        }
        
        try:
            for root, dirs, files in os.walk(self.project_path):
                # Skip ignored directories
                dirs[:] = [d for d in dirs if not self._should_ignore_directory(d)]
                
                root_path = Path(root)
                rel_path = root_path.relative_to(self.project_path)
                
                # Directory info
                structure['directories'][str(rel_path)] = {
                    'subdirectories': dirs,
                    'files': files,
                    'file_count': len(files),
                    'purpose': self._infer_directory_purpose(rel_path, files)
                }
                
                # File details
                for file_name in files:
                    file_path = root_path / file_name
                    if not self._should_ignore_file(file_path):
                        rel_file_path = file_path.relative_to(self.project_path)
                        
                        file_info = {
                            'size': file_path.stat().st_size,
                            'extension': file_path.suffix.lower(),
                            'type': self._classify_file_type(file_path),
                            'importance': self._calculate_file_importance(file_path),
                            'summary': self._get_file_summary(file_path)
                        }
                        
                        structure['files'][str(rel_file_path)] = file_info
                        
                        # Track important files
                        if file_info['importance'] >= 0.7:
                            structure['important_files'][str(rel_file_path)] = file_info
        
        except Exception as e:
            logger.error(f"Error getting file structure: {e}")
            structure['error'] = str(e)
        
        return structure
    
    def _analyze_code_patterns(self) -> Dict:
        """Analyze code patterns and conventions"""
        patterns = {
            'imports': defaultdict(int),
            'classes': [],
            'functions': [],
            'constants': [],
            'decorators': defaultdict(int),
            'coding_style': {},
            'common_patterns': []
        }
        
        try:
            for py_file in self.project_path.rglob('*.py'):
                if self._should_ignore_file(py_file):
                    continue
                    
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    # Parse AST
                    tree = ast.parse(content)
                    
                    # Analyze patterns
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                patterns['imports'][alias.name] += 1
                        
                        elif isinstance(node, ast.ImportFrom):
                            if node.module:
                                patterns['imports'][node.module] += 1
                        
                        elif isinstance(node, ast.ClassDef):
                            patterns['classes'].append({
                                'name': node.name,
                                'file': str(py_file.relative_to(self.project_path)),
                                'bases': [base.id for base in node.bases if isinstance(base, ast.Name)],
                                'methods': [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                            })
                        
                        elif isinstance(node, ast.FunctionDef):
                            patterns['functions'].append({
                                'name': node.name,
                                'file': str(py_file.relative_to(self.project_path)),
                                'args': [arg.arg for arg in node.args.args],
                                'decorators': [d.id for d in node.decorator_list if isinstance(d, ast.Name)]
                            })
                        
                        elif isinstance(node, ast.Assign):
                            for target in node.targets:
                                if isinstance(target, ast.Name) and target.id.isupper():
                                    patterns['constants'].append({
                                        'name': target.id,
                                        'file': str(py_file.relative_to(self.project_path))
                                    })
                    
                    # Analyze coding style
                    style_info = self._analyze_coding_style(content)
                    patterns['coding_style'][str(py_file.relative_to(self.project_path))] = style_info
                    
                except Exception as e:
                    logger.warning(f"Could not analyze Python file {py_file}: {e}")
        
        except Exception as e:
            logger.error(f"Error analyzing code patterns: {e}")
            patterns['error'] = str(e)
        
        return patterns
    
    def _build_dependency_graph(self) -> Dict:
        """Build dependency graph between files"""
        graph = {
            'nodes': {},
            'edges': [],
            'clusters': {},
            'circular_dependencies': []
        }
        
        try:
            # Build import graph
            for py_file in self.project_path.rglob('*.py'):
                if self._should_ignore_file(py_file):
                    continue
                
                rel_path = str(py_file.relative_to(self.project_path))
                graph['nodes'][rel_path] = {
                    'type': 'python_file',
                    'imports': [],
                    'imported_by': []
                }
                
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    tree = ast.parse(content)
                    
                    for node in ast.walk(tree):
                        if isinstance(node, ast.ImportFrom):
                            if node.module and node.module.startswith('.'):
                                # Relative import
                                imported_file = self._resolve_relative_import(py_file, node.module)
                                if imported_file:
                                    graph['nodes'][rel_path]['imports'].append(imported_file)
                                    graph['edges'].append({'from': rel_path, 'to': imported_file})
                
                except Exception as e:
                    logger.warning(f"Could not build dependency graph for {py_file}: {e}")
            
            # Detect circular dependencies
            graph['circular_dependencies'] = self._detect_circular_dependencies(graph)
            
            # Cluster related files
            graph['clusters'] = self._cluster_related_files(graph)
        
        except Exception as e:
            logger.error(f"Error building dependency graph: {e}")
            graph['error'] = str(e)
        
        return graph
    
    def _analyze_django_structure(self) -> Dict:
        """Analyze Django-specific structure"""
        django_info = {
            'settings': {},
            'urls': {},
            'models': {},
            'views': {},
            'forms': {},
            'templates': {},
            'static_files': {},
            'apps': [],
            'middleware': [],
            'installed_apps': []
        }
        
        try:
            # Find Django project structure
            manage_py_files = list(self.project_path.rglob('manage.py'))
            if not manage_py_files:
                return {'error': 'Not a Django project - no manage.py found'}
            
            # Analyze settings
            settings_files = list(self.project_path.rglob('settings.py'))
            for settings_file in settings_files:
                django_info['settings'][str(settings_file.relative_to(self.project_path))] = self._analyze_settings_file(settings_file)
            
            # Analyze URLs
            url_files = list(self.project_path.rglob('urls.py'))
            for url_file in url_files:
                django_info['urls'][str(url_file.relative_to(self.project_path))] = self._analyze_url_file(url_file)
            
            # Analyze models
            model_files = list(self.project_path.rglob('models.py'))
            for model_file in model_files:
                django_info['models'][str(model_file.relative_to(self.project_path))] = self._analyze_model_file(model_file)
            
            # Analyze views
            view_files = list(self.project_path.rglob('views.py'))
            for view_file in view_files:
                django_info['views'][str(view_file.relative_to(self.project_path))] = self._analyze_view_file(view_file)
            
            # Analyze forms
            form_files = list(self.project_path.rglob('forms.py'))
            for form_file in form_files:
                django_info['forms'][str(form_file.relative_to(self.project_path))] = self._analyze_form_file(form_file)
            
            # Analyze templates
            template_dirs = list(self.project_path.rglob('templates'))
            for template_dir in template_dirs:
                django_info['templates'][str(template_dir.relative_to(self.project_path))] = self._analyze_template_dir(template_dir)
            
            # Analyze static files
            static_dirs = list(self.project_path.rglob('static'))
            for static_dir in static_dirs:
                django_info['static_files'][str(static_dir.relative_to(self.project_path))] = self._analyze_static_dir(static_dir)
            
            # Detect Django apps
            django_info['apps'] = self._detect_django_apps()
        
        except Exception as e:
            logger.error(f"Error analyzing Django structure: {e}")
            django_info['error'] = str(e)
        
        return django_info
    
    def _analyze_database_schema(self) -> Dict:
        """Analyze database schema and relationships"""
        schema = {
            'models': {},
            'relationships': {},
            'migrations': {},
            'database_info': {}
        }
        
        try:
            # Analyze models for schema
            for model_file in self.project_path.rglob('models.py'):
                if self._should_ignore_file(model_file):
                    continue
                
                schema['models'][str(model_file.relative_to(self.project_path))] = self._extract_model_schema(model_file)
            
            # Analyze migrations
            for migration_file in self.project_path.rglob('migrations/*.py'):
                if migration_file.name != '__init__.py':
                    schema['migrations'][str(migration_file.relative_to(self.project_path))] = self._analyze_migration_file(migration_file)
            
            # Build relationship graph
            schema['relationships'] = self._build_model_relationships(schema['models'])
        
        except Exception as e:
            logger.error(f"Error analyzing database schema: {e}")
            schema['error'] = str(e)
        
        return schema
    
    def _analyze_api_endpoints(self) -> Dict:
        """Analyze API endpoints and patterns"""
        api_info = {
            'rest_framework': False,
            'endpoints': [],
            'serializers': {},
            'viewsets': {},
            'permissions': {},
            'authentication': {}
        }
        
        try:
            # Check for DRF
            for settings_file in self.project_path.rglob('settings.py'):
                with open(settings_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'rest_framework' in content.lower():
                        api_info['rest_framework'] = True
                        break
            
            # Analyze serializers
            for serializer_file in self.project_path.rglob('serializers.py'):
                api_info['serializers'][str(serializer_file.relative_to(self.project_path))] = self._analyze_serializer_file(serializer_file)
            
            # Analyze viewsets and API views
            for view_file in self.project_path.rglob('views.py'):
                api_views = self._extract_api_views(view_file)
                if api_views:
                    api_info['viewsets'][str(view_file.relative_to(self.project_path))] = api_views
            
            # Extract endpoints from URL patterns
            api_info['endpoints'] = self._extract_api_endpoints()
        
        except Exception as e:
            logger.error(f"Error analyzing API endpoints: {e}")
            api_info['error'] = str(e)
        
        return api_info
    
    def _analyze_frontend_assets(self) -> Dict:
        """Analyze frontend assets and dependencies"""
        frontend = {
            'static_files': {},
            'templates': {},
            'javascript': {},
            'css': {},
            'frameworks': [],
            'package_json': None
        }
        
        try:
            # Analyze package.json if exists
            package_json = self.project_path / 'package.json'
            if package_json.exists():
                with open(package_json, 'r') as f:
                    frontend['package_json'] = json.load(f)
            
            # Analyze static files
            for static_file in self.project_path.rglob('static/**/*'):
                if static_file.is_file():
                    ext = static_file.suffix.lower()
                    if ext in ['.js', '.css', '.scss', '.less']:
                        frontend['static_files'][str(static_file.relative_to(self.project_path))] = {
                            'size': static_file.stat().st_size,
                            'type': ext,
                            'content_summary': self._get_file_summary(static_file)
                        }
            
            # Detect frontend frameworks
            frontend['frameworks'] = self._detect_frontend_frameworks()
        
        except Exception as e:
            logger.error(f"Error analyzing frontend assets: {e}")
            frontend['error'] = str(e)
        
        return frontend
    
    def _analyze_test_structure(self) -> Dict:
        """Analyze test structure and coverage"""
        test_info = {
            'test_files': {},
            'test_frameworks': [],
            'coverage_estimate': 0,
            'test_patterns': {}
        }
        
        try:
            # Find test files
            test_files = list(self.project_path.rglob('test*.py')) + list(self.project_path.rglob('*test*.py'))
            
            for test_file in test_files:
                if self._should_ignore_file(test_file):
                    continue
                
                test_info['test_files'][str(test_file.relative_to(self.project_path))] = self._analyze_test_file(test_file)
            
            # Detect test frameworks
            test_info['test_frameworks'] = self._detect_test_frameworks()
            
            # Estimate coverage
            test_info['coverage_estimate'] = self._estimate_test_coverage()
        
        except Exception as e:
            logger.error(f"Error analyzing test structure: {e}")
            test_info['error'] = str(e)
        
        return test_info
    
    def _analyze_code_quality(self) -> Dict:
        """Analyze code quality metrics"""
        quality = {
            'complexity': {},
            'duplicates': [],
            'conventions': {},
            'security_issues': [],
            'performance_issues': []
        }
        
        try:
            # Basic complexity analysis
            for py_file in self.project_path.rglob('*.py'):
                if self._should_ignore_file(py_file):
                    continue
                
                quality['complexity'][str(py_file.relative_to(self.project_path))] = self._calculate_complexity(py_file)
            
            # Check for common issues
            quality['security_issues'] = self._check_security_issues()
            quality['performance_issues'] = self._check_performance_issues()
        
        except Exception as e:
            logger.error(f"Error analyzing code quality: {e}")
            quality['error'] = str(e)
        
        return quality
    
    def _get_recent_activity(self) -> Dict:
        """Get recent file activity"""
        activity = {
            'recent_modifications': [],
            'recent_additions': [],
            'activity_patterns': {}
        }
        
        try:
            from datetime import datetime, timedelta
            
            # Get files modified in last 24 hours
            recent_time = datetime.now() - timedelta(hours=24)
            
            for file_path in self.project_path.rglob('*'):
                if file_path.is_file() and not self._should_ignore_file(file_path):
                    try:
                        stat = file_path.stat()
                        mod_time = datetime.fromtimestamp(stat.st_mtime)
                        
                        if mod_time > recent_time:
                            activity['recent_modifications'].append({
                                'file': str(file_path.relative_to(self.project_path)),
                                'modified': mod_time.isoformat(),
                                'size': stat.st_size
                            })
                    except Exception as e:
                        logger.warning(f"Could not get stats for {file_path}: {e}")
        
        except Exception as e:
            logger.error(f"Error getting recent activity: {e}")
            activity['error'] = str(e)
        
        return activity
    
    def _generate_context_summary(self) -> Dict:
        """Generate high-level context summary for Claude"""
        summary = {
            'project_type': 'django_web_application',
            'complexity_level': 'medium',
            'main_features': [],
            'architecture_patterns': [],
            'key_technologies': [],
            'development_stage': 'development',
            'recommended_actions': []
        }
        
        try:
            # Determine project type and complexity
            if self.analysis_cache.get('project_metadata', {}).get('total_files', 0) > 50:
                summary['complexity_level'] = 'high'
            elif self.analysis_cache.get('project_metadata', {}).get('total_files', 0) < 20:
                summary['complexity_level'] = 'low'
            
            # Extract main features
            django_structure = self.analysis_cache.get('django_structure', {})
            if django_structure.get('models'):
                summary['main_features'].append('database_models')
            if django_structure.get('views'):
                summary['main_features'].append('web_views')
            if self.analysis_cache.get('api_endpoints', {}).get('rest_framework'):
                summary['main_features'].append('rest_api')
            
            # Detect architecture patterns
            if 'rest_framework' in summary['main_features']:
                summary['architecture_patterns'].append('rest_api')
            if len(django_structure.get('apps', [])) > 3:
                summary['architecture_patterns'].append('multi_app_architecture')
            
            # Key technologies
            frameworks = self.analysis_cache.get('project_metadata', {}).get('frameworks', [])
            summary['key_technologies'] = frameworks
        
        except Exception as e:
            logger.error(f"Error generating context summary: {e}")
            summary['error'] = str(e)
        
        return summary
    
    # Helper methods
    def _should_ignore_file(self, file_path: Path) -> bool:
        """Check if file should be ignored"""
        ignore_patterns = [
            '*.pyc', '*.pyo', '*.pyd', '__pycache__',
            '.git', '.gitignore', '.env', '*.log',
            'node_modules', 'venv', 'env', '.venv',
            '*.sqlite3', '*.db', '*.backup'
        ]
        
        file_str = str(file_path)
        return any(pattern.replace('*', '') in file_str for pattern in ignore_patterns)
    
    def _should_ignore_directory(self, dir_name: str) -> bool:
        """Check if directory should be ignored"""
        ignore_dirs = [
            '__pycache__', '.git', 'node_modules', 'venv', 'env', '.venv',
            '.pytest_cache', '.coverage', 'htmlcov', 'dist', 'build'
        ]
        return dir_name in ignore_dirs
    
    def _infer_directory_purpose(self, rel_path: Path, files: List[str]) -> str:
        """Infer the purpose of a directory"""
        path_str = str(rel_path).lower()
        
        if 'test' in path_str:
            return 'tests'
        elif 'static' in path_str:
            return 'static_files'
        elif 'template' in path_str:
            return 'templates'
        elif 'migration' in path_str:
            return 'database_migrations'
        elif any(f.endswith('models.py') for f in files):
            return 'django_app'
        elif any(f.endswith('.css') or f.endswith('.js') for f in files):
            return 'frontend_assets'
        else:
            return 'general'
    
    def _classify_file_type(self, file_path: Path) -> str:
        """Classify file type"""
        ext = file_path.suffix.lower()
        name = file_path.name.lower()
        
        if ext == '.py':
            if name in ['models.py', 'views.py', 'urls.py', 'settings.py', 'forms.py', 'admin.py']:
                return f'django_{name.replace(".py", "")}'
            elif 'test' in name:
                return 'test_file'
            else:
                return 'python_file'
        elif ext in ['.html', '.htm']:
            return 'template'
        elif ext in ['.css', '.scss', '.less']:
            return 'stylesheet'
        elif ext in ['.js', '.ts']:
            return 'javascript'
        elif ext in ['.json']:
            return 'config'
        elif ext in ['.md', '.rst', '.txt']:
            return 'documentation'
        else:
            return 'other'
    
    def _calculate_file_importance(self, file_path: Path) -> float:
        """Calculate file importance score (0-1)"""
        name = file_path.name.lower()
        
        # Django core files
        if name in ['settings.py', 'urls.py', 'models.py', 'views.py']:
            return 1.0
        elif name in ['forms.py', 'admin.py', 'serializers.py']:
            return 0.9
        elif name in ['manage.py', 'wsgi.py', 'asgi.py']:
            return 0.8
        elif name.startswith('test_'):
            return 0.6
        elif file_path.suffix == '.py':
            return 0.7
        elif file_path.suffix in ['.html', '.css', '.js']:
            return 0.5
        else:
            return 0.3
    
    def _get_file_summary(self, file_path: Path) -> str:
        """Get a brief summary of file content"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            if len(content) == 0:
                return "Empty file"
            
            # For Python files, extract key information
            if file_path.suffix == '.py':
                lines = content.split('\n')
                classes = [line.strip() for line in lines if line.strip().startswith('class ')]
                functions = [line.strip() for line in lines if line.strip().startswith('def ')]
                imports = [line.strip() for line in lines if line.strip().startswith('import ') or line.strip().startswith('from ')]
                
                summary_parts = []
                if classes:
                    summary_parts.append(f"{len(classes)} classes")
                if functions:
                    summary_parts.append(f"{len(functions)} functions")
                if imports:
                    summary_parts.append(f"{len(imports)} imports")
                
                return f"Python file with {', '.join(summary_parts)}" if summary_parts else "Python file"
            
            # For other files, just return basic info
            lines = len(content.split('\n'))
            return f"{file_path.suffix} file with {lines} lines"
            
        except Exception as e:
            return f"Could not read file: {str(e)}"
    
    def get_context_for_claude(self, max_size: int = 50000) -> str:
        """
        Get formatted context for Claude with size limit
        """
        if not self.analysis_cache:
            self.analyze_full_codebase()
        
        # Create condensed context
        context = {
            'project_summary': self.analysis_cache.get('context_summary', {}),
            'key_files': {},
            'django_structure': self.analysis_cache.get('django_structure', {}),
            'recent_activity': self.analysis_cache.get('recent_activity', {}),
            'code_patterns': self.analysis_cache.get('code_analysis', {})
        }
        
        # Include important files content
        file_structure = self.analysis_cache.get('file_structure', {})
        important_files = file_structure.get('important_files', {})
        
        current_size = 0
        for file_path, file_info in important_files.items():
            if current_size > max_size:
                break
                
            try:
                full_path = self.project_path / file_path
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                if len(content) < 5000:  # Only include smaller files
                    context['key_files'][file_path] = content
                    current_size += len(content)
                    
            except Exception as e:
                logger.warning(f"Could not include file {file_path}: {e}")
        
        return json.dumps(context, indent=2)
    
    # Placeholder implementations for complex analysis methods
    def _detect_frameworks(self) -> List[str]:
        """Detect frameworks used in the project"""
        frameworks = ['Django']  # Always Django for this project
        
        # Check for additional frameworks
        req_files = list(self.project_path.rglob('requirements*.txt'))
        for req_file in req_files:
            try:
                with open(req_file, 'r') as f:
                    content = f.read().lower()
                    if 'djangorestframework' in content:
                        frameworks.append('Django REST Framework')
                    if 'celery' in content:
                        frameworks.append('Celery')
                    if 'redis' in content:
                        frameworks.append('Redis')
            except Exception:
                pass
        
        return frameworks
    
    def _analyze_coding_style(self, content: str) -> Dict:
        """Analyze coding style patterns"""
        return {
            'indentation': 'spaces' if '    ' in content else 'tabs',
            'line_length': max(len(line) for line in content.split('\n')) if content else 0,
            'docstring_style': 'google' if '"""' in content else 'unknown'
        }
    
    def _resolve_relative_import(self, file_path: Path, module: str) -> Optional[str]:
        """Resolve relative import to actual file path"""
        # Simplified implementation
        return None
    
    def _detect_circular_dependencies(self, graph: Dict) -> List[Dict]:
        """Detect circular dependencies in the graph"""
        # Simplified implementation
        return []
    
    def _cluster_related_files(self, graph: Dict) -> Dict:
        """Cluster related files together"""
        # Simplified implementation
        return {}
    
    def _analyze_settings_file(self, settings_file: Path) -> Dict:
        """Analyze Django settings file"""
        try:
            with open(settings_file, 'r') as f:
                content = f.read()
            
            return {
                'installed_apps': re.findall(r"'([^']+)'", content),
                'middleware': re.findall(r"'([^']+)'", content),
                'database': 'postgresql' if 'postgresql' in content.lower() else 'sqlite' if 'sqlite' in content.lower() else 'unknown'
            }
        except Exception:
            return {'error': 'Could not analyze settings file'}
    
    def _analyze_url_file(self, url_file: Path) -> Dict:
        """Analyze URL patterns file"""
        try:
            with open(url_file, 'r') as f:
                content = f.read()
            
            patterns = re.findall(r"path\s*\(\s*['\"]([^'\"]*)['\"]", content)
            return {'patterns': patterns}
        except Exception:
            return {'error': 'Could not analyze URL file'}
    
    def _analyze_model_file(self, model_file: Path) -> Dict:
        """Analyze Django models file"""
        try:
            with open(model_file, 'r') as f:
                content = f.read()
            
            models = re.findall(r'class\s+(\w+)\s*\([^)]*Model[^)]*\):', content)
            return {'models': models}
        except Exception:
            return {'error': 'Could not analyze model file'}
    
    def _analyze_view_file(self, view_file: Path) -> Dict:
        """Analyze Django views file"""
        try:
            with open(view_file, 'r') as f:
                content = f.read()
            
            views = re.findall(r'def\s+(\w+)\s*\([^)]*request[^)]*\):', content)
            class_views = re.findall(r'class\s+(\w+)\s*\([^)]*View[^)]*\):', content)
            
            return {'function_views': views, 'class_views': class_views}
        except Exception:
            return {'error': 'Could not analyze view file'}
    
    def _analyze_form_file(self, form_file: Path) -> Dict:
        """Analyze Django forms file"""
        try:
            with open(form_file, 'r') as f:
                content = f.read()
            
            forms = re.findall(r'class\s+(\w+)\s*\([^)]*Form[^)]*\):', content)
            return {'forms': forms}
        except Exception:
            return {'error': 'Could not analyze form file'}
    
    def _analyze_template_dir(self, template_dir: Path) -> Dict:
        """Analyze template directory"""
        templates = []
        try:
            for template_file in template_dir.rglob('*.html'):
                templates.append(str(template_file.relative_to(template_dir)))
            return {'templates': templates}
        except Exception:
            return {'error': 'Could not analyze template directory'}
    
    def _analyze_static_dir(self, static_dir: Path) -> Dict:
        """Analyze static files directory"""
        static_files = {'css': [], 'js': [], 'images': [], 'other': []}
        
        try:
            for static_file in static_dir.rglob('*'):
                if static_file.is_file():
                    ext = static_file.suffix.lower()
                    rel_path = str(static_file.relative_to(static_dir))
                    
                    if ext in ['.css', '.scss', '.less']:
                        static_files['css'].append(rel_path)
                    elif ext in ['.js', '.ts']:
                        static_files['js'].append(rel_path)
                    elif ext in ['.png', '.jpg', '.jpeg', '.gif', '.svg']:
                        static_files['images'].append(rel_path)
                    else:
                        static_files['other'].append(rel_path)
            
            return static_files
        except Exception:
            return {'error': 'Could not analyze static directory'}
    
    def _detect_django_apps(self) -> List[str]:
        """Detect Django apps in the project"""
        apps = []
        
        try:
            for app_file in self.project_path.rglob('apps.py'):
                app_dir = app_file.parent
                apps.append(app_dir.name)
        except Exception:
            pass
        
        return apps
    
    def _extract_model_schema(self, model_file: Path) -> Dict:
        """Extract model schema information"""
        # Simplified implementation
        return {}
    
    def _analyze_migration_file(self, migration_file: Path) -> Dict:
        """Analyze Django migration file"""
        # Simplified implementation
        return {}
    
    def _build_model_relationships(self, models: Dict) -> Dict:
        """Build model relationship graph"""
        # Simplified implementation
        return {}
    
    def _analyze_serializer_file(self, serializer_file: Path) -> Dict:
        """Analyze DRF serializers file"""
        # Simplified implementation
        return {}
    
    def _extract_api_views(self, view_file: Path) -> Dict:
        """Extract API views from views file"""
        # Simplified implementation
        return {}
    
    def _extract_api_endpoints(self) -> List[Dict]:
        """Extract API endpoints from URL patterns"""
        # Simplified implementation
        return []
    
    def _detect_frontend_frameworks(self) -> List[str]:
        """Detect frontend frameworks"""
        # Simplified implementation
        return []
    
    def _analyze_test_file(self, test_file: Path) -> Dict:
        """Analyze test file"""
        # Simplified implementation
        return {}
    
    def _detect_test_frameworks(self) -> List[str]:
        """Detect test frameworks"""
        # Simplified implementation
        return []
    
    def _estimate_test_coverage(self) -> float:
        """Estimate test coverage percentage"""
        # Simplified implementation
        return 0.5
    
    def _calculate_complexity(self, py_file: Path) -> Dict:
        """Calculate code complexity metrics"""
        # Simplified implementation
        return {}
    
    def _check_security_issues(self) -> List[Dict]:
        """Check for common security issues"""
        # Simplified implementation
        return []
    
    def _check_performance_issues(self) -> List[Dict]:
        """Check for performance issues"""
        # Simplified implementation
        return []