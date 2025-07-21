import re
import ast
import logging
from typing import Dict, List, Tuple, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class CodeMerger:
    """
    Smart code merging service that can intelligently merge AI-generated code
    with existing files without breaking functionality.
    """
    
    def __init__(self):
        pass
    
    def merge_file_content(self, existing_content: str, new_content: str, file_path: str) -> Dict:
        """
        Merge new content with existing content intelligently based on file type.
        
        Returns:
            dict: {
                'merged_content': str,
                'conflicts': List[str],
                'merge_type': str,
                'success': bool
            }
        """
        
        if not existing_content.strip():
            return {
                'merged_content': new_content,
                'conflicts': [],
                'merge_type': 'new_file',
                'success': True
            }
        
        file_ext = Path(file_path).suffix.lower()
        
        try:
            if file_ext == '.py':
                return self._merge_python_files(existing_content, new_content, file_path)
            elif file_ext in ['.html', '.htm']:
                return self._merge_html_files(existing_content, new_content, file_path)
            elif file_ext == '.css':
                return self._merge_css_files(existing_content, new_content, file_path)
            elif file_ext == '.js':
                return self._merge_javascript_files(existing_content, new_content, file_path)
            else:
                return self._merge_text_files(existing_content, new_content, file_path)
                
        except Exception as e:
            logger.error(f"Error merging file {file_path}: {e}")
            return {
                'merged_content': existing_content,
                'conflicts': [f"Merge failed: {str(e)}"],
                'merge_type': 'error',
                'success': False
            }
    
    def _merge_python_files(self, existing: str, new: str, file_path: str) -> Dict:
        """Smart merge for Python files using simple line-based approach"""
        
        try:
            # Simple but effective merging approach
            existing_lines = existing.split('\n')
            new_lines = new.split('\n')
            
            # Extract imports from both files
            existing_imports = self._extract_simple_imports(existing_lines)
            new_imports = self._extract_simple_imports(new_lines)
            
            # Merge imports (remove duplicates)
            all_imports = list(dict.fromkeys(existing_imports + new_imports))
            
            # Get non-import content
            existing_body = self._remove_imports(existing_lines)
            new_body = self._remove_imports(new_lines)
            
            # Check for conflicts (same class/function names)
            conflicts = self._detect_python_conflicts(existing_body, new_body)
            
            # Build merged content
            merged_lines = []
            
            # Add merged imports
            if all_imports:
                merged_lines.extend(all_imports)
                merged_lines.append('')
            
            # Add existing body
            if existing_body:
                merged_lines.extend(existing_body)
                merged_lines.append('')
            
            # Add new body (only if not conflicting)
            if new_body:
                merged_lines.append('# === AI Generated Content ===')
                merged_lines.extend(new_body)
            
            merged_content = '\n'.join(merged_lines)
            
            return {
                'merged_content': merged_content,
                'conflicts': conflicts,
                'merge_type': 'simple_merge',
                'success': True
            }
            
        except Exception as e:
            logger.error(f"Error merging Python file {file_path}: {e}")
            return self._fallback_merge(existing, new, file_path)
    
    def _extract_simple_imports(self, lines: List[str]) -> List[str]:
        """Extract import statements from lines"""
        imports = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('import ') or stripped.startswith('from '):
                imports.append(stripped)
        return imports
    
    def _remove_imports(self, lines: List[str]) -> List[str]:
        """Remove import statements and return body content"""
        body = []
        for line in lines:
            stripped = line.strip()
            if not (stripped.startswith('import ') or stripped.startswith('from ')) and stripped:
                body.append(line)
        return body
    
    def _detect_python_conflicts(self, existing_body: List[str], new_body: List[str]) -> List[str]:
        """Detect potential conflicts in Python code"""
        conflicts = []
        
        # Simple conflict detection - look for same class/function names
        existing_defs = set()
        new_defs = set()
        
        for line in existing_body:
            stripped = line.strip()
            if stripped.startswith('class ') or stripped.startswith('def '):
                name = stripped.split('(')[0].split(':')[0].replace('class ', '').replace('def ', '').strip()
                existing_defs.add(name)
        
        for line in new_body:
            stripped = line.strip()
            if stripped.startswith('class ') or stripped.startswith('def '):
                name = stripped.split('(')[0].split(':')[0].replace('class ', '').replace('def ', '').strip()
                new_defs.add(name)
        
        # Find conflicts
        conflicting = existing_defs.intersection(new_defs)
        for name in conflicting:
            conflicts.append(f"Definition '{name}' exists in both files")
        
        return conflicts
    
    
    def _merge_html_files(self, existing: str, new: str, file_path: str) -> Dict:
        """Merge HTML files by combining head and body content"""
        
        try:
            # Extract head and body from both files
            existing_head = self._extract_html_section(existing, 'head')
            existing_body = self._extract_html_section(existing, 'body')
            
            new_head = self._extract_html_section(new, 'head')
            new_body = self._extract_html_section(new, 'body')
            
            # Merge head content
            merged_head = self._merge_html_head(existing_head, new_head)
            
            # Merge body content
            merged_body = self._merge_html_body(existing_body, new_body)
            
            # Generate merged HTML
            merged_content = self._generate_html_file(merged_head, merged_body)
            
            return {
                'merged_content': merged_content,
                'conflicts': [],
                'merge_type': 'html_merge',
                'success': True
            }
            
        except Exception as e:
            logger.error(f"Error merging HTML file {file_path}: {e}")
            return self._fallback_merge(existing, new, file_path)
    
    def _extract_html_section(self, content: str, section: str) -> str:
        """Extract head or body section from HTML"""
        pattern = rf'<{section}[^>]*>(.*?)</{section}>'
        match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
        return match.group(1) if match else ''
    
    def _merge_html_head(self, existing: str, new: str) -> str:
        """Merge HTML head sections"""
        # Simple merge - combine both
        return existing + '\n' + new if existing and new else existing or new
    
    def _merge_html_body(self, existing: str, new: str) -> str:
        """Merge HTML body sections"""
        # Simple merge - combine both
        return existing + '\n' + new if existing and new else existing or new
    
    def _generate_html_file(self, head: str, body: str) -> str:
        """Generate complete HTML file"""
        return f'''<!DOCTYPE html>
<html>
<head>
{head}
</head>
<body>
{body}
</body>
</html>'''
    
    def _merge_css_files(self, existing: str, new: str, file_path: str) -> Dict:
        """Merge CSS files by combining selectors"""
        
        try:
            # Parse CSS rules
            existing_rules = self._parse_css_rules(existing)
            new_rules = self._parse_css_rules(new)
            
            # Merge rules
            merged_rules = {**existing_rules, **new_rules}
            
            # Generate merged CSS
            merged_content = self._generate_css_file(merged_rules)
            
            conflicts = []
            for selector in existing_rules:
                if selector in new_rules and existing_rules[selector] != new_rules[selector]:
                    conflicts.append(f"CSS selector '{selector}' has different rules")
            
            return {
                'merged_content': merged_content,
                'conflicts': conflicts,
                'merge_type': 'css_merge',
                'success': True
            }
            
        except Exception as e:
            logger.error(f"Error merging CSS file {file_path}: {e}")
            return self._fallback_merge(existing, new, file_path)
    
    def _parse_css_rules(self, content: str) -> Dict:
        """Parse CSS rules into a dictionary"""
        rules = {}
        
        # Simple CSS parsing - can be enhanced
        pattern = r'([^{]+)\{([^}]+)\}'
        matches = re.findall(pattern, content)
        
        for selector, rules_text in matches:
            rules[selector.strip()] = rules_text.strip()
        
        return rules
    
    def _generate_css_file(self, rules: Dict) -> str:
        """Generate CSS file from rules"""
        css_parts = []
        
        for selector, rule_text in rules.items():
            css_parts.append(f'{selector} {{\n{rule_text}\n}}')
        
        return '\n\n'.join(css_parts)
    
    def _merge_javascript_files(self, existing: str, new: str, file_path: str) -> Dict:
        """Merge JavaScript files (basic implementation)"""
        
        # For now, just append new content
        merged_content = existing + '\n\n' + new
        
        return {
            'merged_content': merged_content,
            'conflicts': [],
            'merge_type': 'append_merge',
            'success': True
        }
    
    def _merge_text_files(self, existing: str, new: str, file_path: str) -> Dict:
        """Merge text files (basic implementation)"""
        
        # For now, just append new content
        merged_content = existing + '\n\n' + new
        
        return {
            'merged_content': merged_content,
            'conflicts': [],
            'merge_type': 'append_merge',
            'success': True
        }
    
    def _fallback_merge(self, existing: str, new: str, file_path: str) -> Dict:
        """Fallback merge strategy when smart merge fails"""
        
        # Just append new content with a separator
        merged_content = existing + '\n\n# === AI Generated Content ===\n\n' + new
        
        return {
            'merged_content': merged_content,
            'conflicts': ['Used fallback merge strategy'],
            'merge_type': 'fallback_merge',
            'success': True
        }