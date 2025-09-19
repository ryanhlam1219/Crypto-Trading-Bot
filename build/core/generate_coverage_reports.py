#!/usr/bin/env python3
"""
Dynamic Coverage Report Generator for Crypto Trading Bot

This script automatically:
1. Discovers all source directories and files
2. Excludes abstract classes and __init__.py files
3. Updates coverage configuration
4. Generates dynamic HTML reports
5. Creates directory-based navigation

Usage: python generate_coverage_reports.py
"""

import os
import ast
import json
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass
from datetime import datetime


@dataclass
class FileInfo:
    """Information about a source file"""
    path: str
    relative_path: str
    directory: str
    is_abstract: bool
    is_init: bool
    statements: int = 0
    missing: int = 0
    coverage: float = 0.0


@dataclass
class DirectoryInfo:
    """Information about a directory's coverage"""
    name: str
    files: List[FileInfo]
    total_statements: int = 0
    total_missing: int = 0
    coverage_percent: float = 0.0


class AbstractClassDetector:
    """Detects abstract classes and methods in Python files"""
    
    @staticmethod
    def is_abstract_class(file_path: str) -> bool:
        """Check if a Python file contains abstract classes"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse the AST
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    # Check if class inherits from ABC or has abstractmethod decorators
                    for base in node.bases:
                        if isinstance(base, ast.Name) and base.id == 'ABC':
                            return True
                        if isinstance(base, ast.Attribute) and base.attr == 'ABC':
                            return True
                    
                    # Check for abstractmethod decorators
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            for decorator in item.decorator_list:
                                if isinstance(decorator, ast.Name) and 'abstract' in decorator.id:
                                    return True
                                if isinstance(decorator, ast.Attribute) and 'abstract' in decorator.attr:
                                    return True
            
            # Also check for string patterns
            abstract_patterns = [
                r'from\s+abc\s+import\s+.*ABC',
                r'import\s+abc',
                r'@abstractmethod',
                r'class\s+\w+\(.*ABC.*\)',
                r'raise\s+NotImplementedError'
            ]
            
            for pattern in abstract_patterns:
                if re.search(pattern, content):
                    return True
                    
            return False
            
        except Exception as e:
            print(f"Warning: Could not analyze {file_path}: {e}")
            return False


class CoverageReportGenerator:
    """Generates dynamic coverage reports"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.source_dirs = self._discover_source_directories()
        self.exclude_patterns = [
            'Tests/*',
            '*/__pycache__/*',
            '*/migrations/*',
            'setup.py',
            '*/venv/*',
            '*/.venv/*',
            '*/site-packages/*',
            'main.py',
            '*/__init__.py',  # Always exclude __init__.py
            'build/*'  # Always exclude build directory
        ]
        self.detector = AbstractClassDetector()
    
    def _discover_source_directories(self) -> List[str]:
        """Dynamically discover directories containing Python source files"""
        source_dirs = []
        exclude_dirs = {
            'Tests', 'tests', '__pycache__', '.venv', 'venv', 
            '.git', '.pytest_cache', 'htmlcov', 'reports',
            'coverage', '.coverage', '.idea', '.vscode',
            'data', 'logs', 'temp', 'tmp', 'build',  # Exclude build directory
            'Collect-Fees'  # Exclude Collect-Fees (separate project with no tests)
        }
        
        for item in self.project_root.iterdir():
            if (item.is_dir() and 
                item.name not in exclude_dirs and 
                not item.name.startswith('.') and
                self._contains_python_source_files(item)):
                source_dirs.append(item.name)
        
        return sorted(source_dirs)
    
    def _contains_python_source_files(self, directory: Path) -> bool:
        """Check if directory contains Python source files (not just __init__.py)"""
        python_files = list(directory.rglob("*.py"))
        # Must have at least one .py file that's not just __init__.py
        source_files = [f for f in python_files if f.name != "__init__.py"]
        return len(source_files) > 0
    
    def discover_files(self) -> Dict[str, DirectoryInfo]:
        """Discover all source files and categorize them"""
        directories = {}
        
        for source_dir in self.source_dirs:
            dir_path = self.project_root / source_dir
            if not dir_path.exists():
                continue
                
            files = []
            
            # Walk through directory
            for py_file in dir_path.rglob("*.py"):
                relative_path = py_file.relative_to(self.project_root)
                
                # Skip __init__.py files
                if py_file.name == "__init__.py":
                    continue
                
                # Check if it's an abstract class
                is_abstract = self.detector.is_abstract_class(str(py_file))
                
                # Skip abstract classes
                if is_abstract:
                    print(f"Excluding abstract class: {relative_path}")
                    continue
                
                file_info = FileInfo(
                    path=str(py_file),
                    relative_path=str(relative_path),
                    directory=source_dir,
                    is_abstract=is_abstract,
                    is_init=py_file.name == "__init__.py"
                )
                
                files.append(file_info)
            
            if files:
                directories[source_dir] = DirectoryInfo(
                    name=source_dir,
                    files=files
                )
        
        return directories
    
    def load_coverage_data(self) -> Dict:
        """Load coverage data from JSON report"""
        coverage_file = self.project_root / "coverage.json"
        if not coverage_file.exists():
            return {}
        
        with open(coverage_file, 'r') as f:
            return json.load(f)
    
    def update_file_coverage(self, directories: Dict[str, DirectoryInfo], coverage_data: Dict):
        """Update file coverage information from coverage data"""
        files_data = coverage_data.get('files', {})
        
        for dir_info in directories.values():
            for file_info in dir_info.files:
                # Look for the file in coverage data
                coverage_key = None
                for key in files_data.keys():
                    # Normalize paths for comparison
                    normalized_key = key.replace('\\', '/').replace('/', os.sep)
                    normalized_file = file_info.relative_path.replace('\\', '/').replace('/', os.sep)
                    
                    if normalized_key.endswith(normalized_file) or normalized_file.endswith(normalized_key):
                        coverage_key = key
                        break
                
                if coverage_key and coverage_key in files_data:
                    file_data = files_data[coverage_key]
                    summary = file_data.get('summary', {})
                    
                    file_info.statements = summary.get('num_statements', 0)
                    file_info.missing = summary.get('missing_lines', 0)
                    file_info.coverage = summary.get('percent_covered', 0.0)
    
    def calculate_directory_stats(self, directories: Dict[str, DirectoryInfo]):
        """Calculate directory-level statistics"""
        for dir_info in directories.values():
            total_statements = sum(f.statements for f in dir_info.files)
            total_missing = sum(f.missing for f in dir_info.files)
            
            dir_info.total_statements = total_statements
            dir_info.total_missing = total_missing
            
            if total_statements > 0:
                covered = total_statements - total_missing
                dir_info.coverage_percent = (covered / total_statements) * 100
            else:
                dir_info.coverage_percent = 0.0
    
    def update_pyproject_config(self, directories: Dict[str, DirectoryInfo]):
        """Update pyproject.toml with discovered directories and exclusions"""
        # TEMPORARILY DISABLED: This function was causing duplicate coverage entries
        # and overriding manual pyproject.toml configurations
        print("INFO: pyproject.toml update disabled to prevent configuration conflicts")
        print(f"Discovered {len(directories)} source directories: {list(directories.keys())}")
        return
    
    def generate_dynamic_homepage(self, directories: Dict[str, DirectoryInfo]):
        """Generate the dynamic coverage homepage"""
        
        # Calculate overall stats
        total_statements = sum(d.total_statements for d in directories.values())
        total_missing = sum(d.total_missing for d in directories.values())
        overall_coverage = ((total_statements - total_missing) / total_statements * 100) if total_statements > 0 else 0
        
        # Generate directory cards
        directory_cards = []
        directory_modals = []
        
        for dir_name, dir_info in directories.items():
            # Directory card
            card_html = f'''
                <div class="directory-item directory-clickable" onclick="showDirectoryFiles('{dir_name}')">
                    <div class="directory-header">
                        <div class="directory-name">{dir_name}</div>
                        <div class="directory-coverage-percent">{dir_info.coverage_percent:.2f}%</div>
                    </div>
                    <div class="directory-progress">
                        <div class="directory-progress-bar" style="width: {dir_info.coverage_percent:.2f}%;"></div>
                    </div>
                    <div class="directory-stats">
                        <span>{dir_info.total_statements} statements</span>
                        <span class="separator">•</span>
                        <span>{dir_info.total_missing} missing</span>
                        <span class="separator">•</span>
                        <span>{len(dir_info.files)} files</span>
                    </div>
                </div>'''
            directory_cards.append(card_html)
            
            # Modal content
            files_html = []
            for file_info in dir_info.files:
                # Determine coverage color
                if file_info.coverage >= 80:
                    color_class = "#4CAF50"
                elif file_info.coverage >= 50:
                    color_class = "#ff9800"
                else:
                    color_class = "#f44336"
                
                # Try to find the HTML file
                html_file = self.find_html_file(file_info.relative_path)
                
                if html_file:
                    file_link = f'<a href="htmlcov/{html_file}" style="color: #667eea; text-decoration: none;">{file_info.relative_path}</a>'
                else:
                    file_link = file_info.relative_path
                
                file_html = f'''
                    <tr style="border-bottom: 1px solid #e0e0e0;">
                        <td style="padding: 12px;">{file_link}</td>
                        <td style="padding: 12px; text-align: right;">{file_info.statements}</td>
                        <td style="padding: 12px; text-align: right;">{file_info.missing}</td>
                        <td style="padding: 12px; text-align: right;"><span style="background: {color_class}; color: white; padding: 4px 8px; border-radius: 4px;">{file_info.coverage:.2f}%</span></td>
                    </tr>'''
                files_html.append(file_html)
            
            modal_case = f'''
                if (directory === '{dir_name}') {{
                    filesHtml += `{''.join(files_html)}`;
                }}'''
            directory_modals.append(modal_case)
        
        # Generate the complete HTML
        html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
    <title>Crypto Trading Bot - Test Coverage Report</title>
    <link rel="icon" sizes="32x32" href="htmlcov/favicon_32_cb_58284776.png">
    <style>
        /* Custom CSS for coverage report */
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f5f5f5;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: white;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px 0;
            text-align: center;
            margin-bottom: 30px;
        }}
        
        h1 {{
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }}
        
        .subtitle {{
            margin-top: 10px;
            font-size: 1.2em;
            opacity: 0.9;
        }}
        
        .update-info {{
            background: #e3f2fd;
            border: 1px solid #2196f3;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 20px;
            color: #1565c0;
        }}
        
        .overall-coverage {{
            background: white;
            border-radius: 10px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        .coverage-title {{
            font-size: 1.5em;
            margin-bottom: 20px;
            color: #333;
            text-align: center;
        }}
        
        .progress-container {{
            background-color: #e0e0e0;
            border-radius: 25px;
            padding: 3px;
            margin: 20px 0;
            box-shadow: inset 0 2px 5px rgba(0,0,0,0.1);
        }}
        
        .progress-bar {{
            height: 30px;
            border-radius: 22px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            font-size: 14px;
            transition: width 0.5s ease-in-out;
            background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        }}
        
        .progress-text {{
            text-align: center;
            font-size: 2em;
            font-weight: bold;
            color: #4CAF50;
            margin: 10px 0;
        }}
        
        .directory-coverage {{
            background: white;
            border-radius: 10px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        .directory-coverage h3 {{
            margin: 0 0 25px 0;
            color: #333;
            font-size: 1.4em;
            font-weight: 600;
        }}
        
        .directory-list {{
            display: flex;
            flex-direction: column;
            gap: 15px;
        }}
        
        .directory-item {{
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 20px;
            background: #fafafa;
            transition: box-shadow 0.2s, transform 0.2s;
        }}
        
        .directory-clickable {{
            cursor: pointer;
            transition: all 0.3s ease;
        }}
        
        .directory-clickable:hover {{
            background: #f0f7ff !important;
            border-color: #667eea !important;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            transform: translateY(-1px);
        }}
        
        .directory-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
        }}
        
        .directory-name {{
            font-size: 1.2em;
            font-weight: 600;
            color: #333;
        }}
        
        .directory-coverage-percent {{
            font-size: 1.1em;
            font-weight: bold;
            color: #4CAF50;
        }}
        
        .directory-progress {{
            background-color: #e0e0e0;
            border-radius: 15px;
            padding: 2px;
            margin: 10px 0;
            height: 18px;
        }}
        
        .directory-progress-bar {{
            height: 14px;
            border-radius: 13px;
            background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
            transition: width 0.5s ease-in-out;
        }}
        
        .directory-stats {{
            display: flex;
            align-items: center;
            font-size: 0.9em;
            color: #666;
            margin-top: 8px;
        }}
        
        .separator {{
            margin: 0 8px;
            color: #ccc;
        }}
        
        .navigation {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }}
        
        .nav-button {{
            background: white;
            color: #333;
            padding: 25px;
            border: 2px solid #e0e0e0;
            border-radius: 12px;
            text-decoration: none;
            display: block;
            font-weight: bold;
            transition: all 0.3s ease;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }}
        
        .nav-button:hover {{
            transform: translateY(-3px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.15);
            border-color: #667eea;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }}
        
        .button-content {{
            text-align: center;
        }}
        
        .button-title {{
            font-size: 1.2em;
            font-weight: 700;
            margin-bottom: 5px;
        }}
        
        .button-subtitle {{
            font-size: 0.9em;
            opacity: 0.7;
            font-weight: normal;
        }}
        
        .summary-stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }}
        
        .stat-card {{
            background: white;
            border-radius: 10px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        .stat-number {{
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }}
        
        .stat-label {{
            color: #666;
            margin-top: 5px;
        }}
    </style>
</head>
<body>
    <header>
        <div class="container">
            <h1>Crypto Trading Bot</h1>
            <div class="subtitle">Dynamic Test Coverage Report</div>
        </div>
    </header>
    
    <div class="container">
        <div class="update-info">
            <strong>🔄 Auto-Generated Report:</strong> Last updated {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} | 
            Detected {len(directories)} source directories | 
            Excluding abstract classes and __init__.py files
        </div>
        
        <div class="overall-coverage">
            <div class="coverage-title">Overall Test Coverage</div>
            <div class="progress-container">
                <div class="progress-bar" style="width: {overall_coverage:.2f}%;">
                    {overall_coverage:.2f}%
                </div>
            </div>
            <div class="progress-text">{overall_coverage:.2f}%</div>
        </div>
        
        <div class="summary-stats">
            <div class="stat-card">
                <div class="stat-number">{total_statements}</div>
                <div class="stat-label">Total Statements</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{total_missing}</div>
                <div class="stat-label">Missing</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{sum(len(d.files) for d in directories.values())}</div>
                <div class="stat-label">Files Tested</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{len(directories)}</div>
                <div class="stat-label">Directories</div>
            </div>
        </div>
        
        <div class="navigation">
            <a href="htmlcov/index.html" class="nav-button">
                <div class="button-content">
                    <div class="button-title">All Files</div>
                    <div class="button-subtitle">Complete file-by-file analysis</div>
                </div>
            </a>
        </div>
        
        <div class="directory-coverage">
            <h3>Directory Coverage - Click to View Files</h3>
            <div class="directory-list">
                {''.join(directory_cards)}
            </div>
        </div>
        
        <!-- Directory Files Modal -->
        <div id="directoryModal" style="display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 1000;">
            <div style="position: relative; top: 50%; left: 50%; transform: translate(-50%, -50%); background: white; border-radius: 15px; padding: 30px; max-width: 800px; width: 90%; max-height: 80%; overflow-y: auto;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                    <h2 id="modalTitle" style="margin: 0; color: #333;"></h2>
                    <button onclick="closeDirectoryModal()" style="background: none; border: none; font-size: 24px; cursor: pointer; color: #666;">×</button>
                </div>
                <div id="modalContent"></div>
            </div>
        </div>
        
        <div style="text-align: center; margin-top: 40px; color: #666;">
            <p>Generated with coverage.py v7.10.6 | Created at {datetime.now().strftime("%Y-%m-%d %H:%M %Z")}</p>
            <p>🤖 Dynamically generated - automatically excludes abstract classes and __init__.py files</p>
        </div>
    </div>
    
    <script>
        // Directory data
        const directoryData = {{'''
        
        # Add directory data as JavaScript object
        for dir_name, dir_info in directories.items():
            files_data = []
            for file_info in dir_info.files:
                # Determine coverage color
                if file_info.coverage >= 80:
                    color_class = "#4CAF50"
                elif file_info.coverage >= 50:
                    color_class = "#ff9800"
                else:
                    color_class = "#f44336"
                
                # Try to find the HTML file
                html_file = self.find_html_file(file_info.relative_path)
                
                files_data.append({
                    'path': file_info.relative_path,
                    'statements': file_info.statements,
                    'missing': file_info.missing,
                    'coverage': file_info.coverage,
                    'color': color_class,
                    'html_file': html_file
                })
            
            html_content += f'''
            '{dir_name}': {files_data},'''
        
        html_content += f'''
        }};
        
        function showDirectoryFiles(directory) {{
            const modal = document.getElementById('directoryModal');
            const title = document.getElementById('modalTitle');
            const content = document.getElementById('modalContent');
            
            title.textContent = directory + ' Directory Coverage';
            
            let filesHtml = '<table style="width: 100%; border-collapse: collapse;">';
            filesHtml += '<thead><tr style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">';
            filesHtml += '<th style="padding: 12px; text-align: left;">File</th>';
            filesHtml += '<th style="padding: 12px; text-align: right;">Statements</th>';
            filesHtml += '<th style="padding: 12px; text-align: right;">Missing</th>';
            filesHtml += '<th style="padding: 12px; text-align: right;">Coverage</th>';
            filesHtml += '</tr></thead><tbody>';
            
            if (directoryData[directory]) {{
                directoryData[directory].forEach(file => {{
                    let fileLink = file.html_file ? 
                        `<a href="htmlcov/${{file.html_file}}" style="color: #667eea; text-decoration: none;">${{file.path}}</a>` :
                        file.path;
                        
                    filesHtml += `
                        <tr style="border-bottom: 1px solid #e0e0e0;">
                            <td style="padding: 12px;">${{fileLink}}</td>
                            <td style="padding: 12px; text-align: right;">${{file.statements}}</td>
                            <td style="padding: 12px; text-align: right;">${{file.missing}}</td>
                            <td style="padding: 12px; text-align: right;">
                                <span style="background: ${{file.color}}; color: white; padding: 4px 8px; border-radius: 4px;">
                                    ${{file.coverage.toFixed(2)}}%
                                </span>
                            </td>
                        </tr>`;
                }});
            }}
            
            filesHtml += '</tbody></table>';
            
            content.innerHTML = filesHtml;
            modal.style.display = 'block';
        }}
        
        function closeDirectoryModal() {{
            document.getElementById('directoryModal').style.display = 'none';
        }}
        
        // Close modal when clicking outside
        document.getElementById('directoryModal').addEventListener('click', function(e) {{
            if (e.target === this) {{
                closeDirectoryModal();
            }}
        }});
    </script>
</body>
</html>'''
        
        # Write the file
        output_file = self.project_root / "coverage.html"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"Generated dynamic coverage homepage: {output_file}")
    
    def find_html_file(self, relative_path: str) -> str:
        """Find the corresponding HTML file in htmlcov directory"""
        htmlcov_dir = self.project_root / "htmlcov"
        if not htmlcov_dir.exists():
            return ""
        
        # Look for files that might match
        path_parts = relative_path.replace('\\', '/').split('/')
        filename = path_parts[-1].replace('.py', '_py.html')
        
        for html_file in htmlcov_dir.glob("*.html"):
            if filename in html_file.name:
                return html_file.name
        
        return ""
    
    def run(self):
        """Run the complete coverage report generation"""
        print("Starting dynamic coverage report generation...")
        
        # Discover all files and directories
        print("Discovering source files...")
        directories = self.discover_files()
        
        if not directories:
            print("No source directories found!")
            return
        
        print(f"Found {len(directories)} directories with source files")
        for name, info in directories.items():
            print(f"   {name}: {len(info.files)} files")
        
        # Load coverage data
        print("Loading coverage data...")
        coverage_data = self.load_coverage_data()
        
        # Update file coverage information
        if coverage_data:
            print("Updating coverage information...")
            self.update_file_coverage(directories, coverage_data)
            self.calculate_directory_stats(directories)
        else:
            print("No coverage data found - run tests first")
        
        # Update configuration
        print("Updating pyproject.toml configuration...")
        self.update_pyproject_config(directories)
        
        # Generate dynamic reports
        print("Generating dynamic HTML reports...")
        self.generate_dynamic_homepage(directories)
        
        print("Dynamic coverage report generation complete!")
        print("To update: run tests, then run this script again")


if __name__ == "__main__":
    # Go up to project root (build/core -> build -> project_root)
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    generator = CoverageReportGenerator(project_root)
    generator.run()