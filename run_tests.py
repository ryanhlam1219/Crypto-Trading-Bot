#!/usr/bin/env python
"""
Enhanced test runner script for Crypto Trading Bot with comprehensive coverage reporting.

This script provides convenient commands for running different types of tests,
enforcing 90% coverage requirements, and generating detailed HTML coverage reports.
"""

import subprocess
import sys
import os
import json
import webbrowser
import re
from pathlib import Path
from datetime import datetime
try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False


class Colors:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header(text):
    """Print a formatted header."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*70}")
    print(f"🧪 {text}")
    print(f"{'='*70}{Colors.ENDC}")


def print_success(text):
    """Print success message."""
    print(f"{Colors.OKGREEN}✅ {text}{Colors.ENDC}")


def print_error(text):
    """Print error message."""
    print(f"{Colors.FAIL}❌ {text}{Colors.ENDC}")


def print_warning(text):
    """Print warning message."""
    print(f"{Colors.WARNING}⚠️  {text}{Colors.ENDC}")


def print_info(text):
    """Print info message."""
    print(f"{Colors.OKCYAN}ℹ️  {text}{Colors.ENDC}")


def run_command(command, description, capture_output=True, show_progress=False):
    """Run a command and handle errors with enhanced output and optional progress bar."""
    print_header(description)
    print_info(f"Command: {command}")
    
    try:
        if capture_output:
            if show_progress and TQDM_AVAILABLE:
                # For pytest commands, try to show progress
                if "pytest" in command:
                    return run_pytest_with_progress(command, description)
                else:
                    result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=300)
            else:
                result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=300)
        else:
            result = subprocess.run(command, shell=True, timeout=300)
            return True
        
        if result.stdout:
            print(f"\n{Colors.OKBLUE}Output:{Colors.ENDC}")
            print(result.stdout)
        
        if result.stderr and result.returncode != 0:
            print(f"\n{Colors.FAIL}Errors:{Colors.ENDC}")
            print(result.stderr)
        
        if result.returncode != 0:
            print_error(f"{description} failed with return code {result.returncode}")
            return False
        else:
            print_success(f"{description} completed successfully")
            return True
            
    except subprocess.TimeoutExpired:
        print_error(f"{description} timed out after 5 minutes")
        return False
    except Exception as e:
        print_error(f"{description} failed with exception: {e}")
        return False


def run_pytest_with_progress(command, description):
    """Run pytest with a progress bar showing test execution."""
    # First, discover tests to get total count
    discovery_cmd = command.replace("pytest", "pytest --collect-only -q").replace("-v", "")
    
    try:
        discovery_result = subprocess.run(
            discovery_cmd, shell=True, capture_output=True, text=True, timeout=60
        )
        
        # Count tests from collection output
        if discovery_result.returncode == 0:
            # Parse test count from pytest collection
            lines = discovery_result.stdout.split('\n')
            total_tests = 0
            for line in lines:
                if " tests collected" in line:
                    total_tests = int(re.search(r'(\d+) tests collected', line).group(1))
                    break
        else:
            total_tests = 0
            
    except Exception:
        total_tests = 0
    
    if total_tests == 0:
        print_warning("Could not determine test count, running without progress bar")
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=300)
    else:
        print_info(f"Running {total_tests} tests with progress tracking...")
        
        # Run pytest with real-time output
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        pbar = tqdm(total=total_tests, desc="Tests", unit="test", 
                   bar_format="{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]")
        
        output_lines = []
        passed_count = 0
        failed_count = 0
        
        for line in iter(process.stdout.readline, ''):
            output_lines.append(line)
            
            # Update progress based on pytest output
            if " PASSED " in line or " FAILED " in line or " ERROR " in line or " SKIPPED " in line:
                pbar.update(1)
                if " PASSED " in line:
                    passed_count += 1
                elif " FAILED " in line or " ERROR " in line:
                    failed_count += 1
                    
                # Update description with current stats
                if failed_count > 0:
                    pbar.set_description(f"Tests (✅{passed_count} ❌{failed_count})")
                else:
                    pbar.set_description(f"Tests (✅{passed_count})")
        
        process.wait()
        pbar.close()
        
        result = subprocess.CompletedProcess(
            process.args, process.returncode, 
            stdout=''.join(output_lines), stderr=""
        )
    
    # Process the result same as regular run_command
    if result.stdout:
        print(f"\n{Colors.OKBLUE}Output:{Colors.ENDC}")
        print(result.stdout)
    
    if result.stderr and result.returncode != 0:
        print(f"\n{Colors.FAIL}Errors:{Colors.ENDC}")
        print(result.stderr)
    
    if result.returncode != 0:
        print_error(f"{description} failed with return code {result.returncode}")
        return False
    else:
        print_success(f"{description} completed successfully")
        return True


def ensure_directories():
    """Ensure required directories exist."""
    dirs = ['reports', 'htmlcov']
    for dir_name in dirs:
        Path(dir_name).mkdir(exist_ok=True)
    print_info("Created required directories")


def check_coverage_results():
    """Check coverage results and provide detailed feedback."""
    coverage_file = Path("coverage.json")
    
    if not coverage_file.exists():
        print_warning("Coverage JSON file not found")
        return False
    
    try:
        with open(coverage_file, 'r') as f:
            coverage_data = json.load(f)
        
        total_coverage = coverage_data.get('totals', {}).get('percent_covered', 0)
        
        print_header("Coverage Analysis")
        print(f"{Colors.BOLD}Overall Coverage: {total_coverage:.2f}%{Colors.ENDC}")
        
        if total_coverage >= 90:
            print_success(f"Coverage target met! ({total_coverage:.2f}% >= 90%)")
        else:
            print_error(f"Coverage below target! ({total_coverage:.2f}% < 90%)")
        
        # Detailed file-by-file analysis
        files = coverage_data.get('files', {})
        low_coverage_files = []
        
        print(f"\n{Colors.BOLD}File Coverage Details:{Colors.ENDC}")
        for file_path, file_data in files.items():
            file_coverage = file_data.get('summary', {}).get('percent_covered', 0)
            
            if file_coverage < 90:
                low_coverage_files.append((file_path, file_coverage))
                color = Colors.FAIL
            elif file_coverage < 95:
                color = Colors.WARNING
            else:
                color = Colors.OKGREEN
            
            print(f"  {color}{file_path}: {file_coverage:.2f}%{Colors.ENDC}")
        
        if low_coverage_files:
            print_warning(f"Files below 90% coverage:")
            for file_path, coverage in low_coverage_files:
                missing_lines = files[file_path].get('missing_lines', [])
                print(f"  - {file_path}: {coverage:.2f}%")
                if missing_lines:
                    print(f"    Missing lines: {missing_lines[:10]}{'...' if len(missing_lines) > 10 else ''}")
        
        return total_coverage >= 90
        
    except Exception as e:
        print_error(f"Error reading coverage data: {e}")
        return False


def generate_coverage_badge():
    """Generate a coverage badge based on current coverage."""
    try:
        with open("coverage.json", 'r') as f:
            coverage_data = json.load(f)
        
        total_coverage = coverage_data.get('totals', {}).get('percent_covered', 0)
        
        # Determine badge color based on coverage
        if total_coverage >= 90:
            color = "brightgreen"
        elif total_coverage >= 80:
            color = "yellow"
        elif total_coverage >= 70:
            color = "orange"
        else:
            color = "red"
        
        # Create a simple coverage badge info
        badge_info = {
            "coverage": f"{total_coverage:.1f}%",
            "color": color,
            "timestamp": datetime.now().isoformat()
        }
        
        with open("reports/coverage_badge.json", "w") as f:
            json.dump(badge_info, f, indent=2)
        
        print_info(f"Coverage badge generated: {total_coverage:.1f}% ({color})")
        
    except Exception as e:
        print_warning(f"Could not generate coverage badge: {e}")


def generate_enhanced_coverage_html():
    """Generate an enhanced HTML coverage report with visual progress bars."""
    coverage_file = Path("coverage.json")
    
    if not coverage_file.exists():
        print_warning("No coverage data found. Cannot generate enhanced HTML report.")
        return
    
    try:
        with open(coverage_file, 'r') as f:
            coverage_data = json.load(f)
        
        total_coverage = coverage_data.get('totals', {}).get('percent_covered', 0)
        files = coverage_data.get('files', {})
        
        # Filter out __init__.py files
        filtered_files = {path: data for path, data in files.items() 
                         if not path.endswith('__init__.py')}
        
        # Generate HTML
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Coverage Report - Crypto Trading Bot</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
        }}
        .header p {{
            margin: 10px 0 0 0;
            opacity: 0.9;
        }}
        .overall-stats {{
            padding: 30px;
            background: #fff;
            border-bottom: 1px solid #eee;
        }}
        .stat-card {{
            display: inline-block;
            margin: 10px 20px 10px 0;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
            min-width: 150px;
            text-align: center;
        }}
        .stat-value {{
            font-size: 2em;
            font-weight: bold;
            color: #333;
        }}
        .stat-label {{
            color: #666;
            margin-top: 5px;
        }}
        .progress-bar {{
            width: 100%;
            height: 30px;
            background-color: #e9ecef;
            border-radius: 15px;
            overflow: hidden;
            margin: 10px 0;
            position: relative;
        }}
        .progress-fill {{
            height: 100%;
            border-radius: 15px;
            transition: width 0.5s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
        }}
        .progress-excellent {{ background: linear-gradient(90deg, #28a745, #20c997); }}
        .progress-good {{ background: linear-gradient(90deg, #ffc107, #fd7e14); }}
        .progress-poor {{ background: linear-gradient(90deg, #dc3545, #e83e8c); }}
        .files-table {{
            padding: 30px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #f8f9fa;
            font-weight: 600;
            color: #495057;
        }}
        tr:hover {{
            background-color: #f8f9fa;
        }}
        .file-progress {{
            width: 200px;
            height: 20px;
            background-color: #e9ecef;
            border-radius: 10px;
            overflow: hidden;
            position: relative;
        }}
        .file-progress-fill {{
            height: 100%;
            border-radius: 10px;
            transition: width 0.3s ease;
        }}
        .coverage-text {{
            font-weight: bold;
            text-align: center;
            min-width: 60px;
        }}
        .excellent {{ color: #28a745; }}
        .good {{ color: #ffc107; }}
        .poor {{ color: #dc3545; }}
        .footer {{
            padding: 20px;
            text-align: center;
            background: #f8f9fa;
            color: #666;
            border-top: 1px solid #eee;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧪 Coverage Report</h1>
            <p>Crypto Trading Bot - Test Coverage Analysis</p>
        </div>
        
        <div class="overall-stats">
            <h2>📊 Overall Statistics</h2>
            <div class="stat-card">
                <div class="stat-value">{total_coverage:.1f}%</div>
                <div class="stat-label">Total Coverage</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len(filtered_files)}</div>
                <div class="stat-label">Files Analyzed</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{sum(1 for _, data in filtered_files.items() if data.get('summary', {}).get('percent_covered', 0) >= 90)}</div>
                <div class="stat-label">Files ≥90%</div>
            </div>
            
            <h3>Overall Progress</h3>
            <div class="progress-bar">
                <div class="progress-fill progress-{'excellent' if total_coverage >= 90 else 'good' if total_coverage >= 70 else 'poor'}" 
                     style="width: {total_coverage}%">
                    {total_coverage:.1f}%
                </div>
            </div>
        </div>
        
        <div class="files-table">
            <h2>📁 File Coverage Details</h2>
            <table>
                <thead>
                    <tr>
                        <th>File</th>
                        <th>Coverage</th>
                        <th>Progress</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
"""
        
        # Sort files by coverage percentage
        sorted_files = sorted(
            [(path, data.get('summary', {}).get('percent_covered', 0), data) 
             for path, data in filtered_files.items()],
            key=lambda x: x[1],
            reverse=True
        )
        
        for file_path, coverage, data in sorted_files:
            filename = file_path.replace('\\', '/').split('/')[-1]
            
            # Determine status and color
            if coverage >= 90:
                status = "Excellent"
                status_class = "excellent"
                progress_class = "progress-excellent"
            elif coverage >= 70:
                status = "Good"
                status_class = "good"
                progress_class = "progress-good"
            else:
                status = "Needs Work"
                status_class = "poor"
                progress_class = "progress-poor"
            
            html_content += f"""
                    <tr>
                        <td><strong>{filename}</strong></td>
                        <td class="coverage-text {status_class}">{coverage:.1f}%</td>
                        <td>
                            <div class="file-progress">
                                <div class="file-progress-fill {progress_class}" style="width: {coverage}%"></div>
                            </div>
                        </td>
                        <td class="{status_class}">{status}</td>
                    </tr>
"""
        
        html_content += f"""
                </tbody>
            </table>
        </div>
        
        <div class="footer">
            <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 
               <a href="htmlcov/index.html">View Detailed Coverage Report</a></p>
        </div>
    </div>
    
    <script>
        // Add some interactivity
        document.addEventListener('DOMContentLoaded', function() {{
            const progressBars = document.querySelectorAll('.progress-fill, .file-progress-fill');
            progressBars.forEach(bar => {{
                const width = bar.style.width;
                bar.style.width = '0%';
                setTimeout(() => {{
                    bar.style.width = width;
                }}, 100);
            }});
        }});
    </script>
</body>
</html>
"""
        
        # Write the HTML file
        reports_dir = Path("reports")
        reports_dir.mkdir(exist_ok=True)
        
        with open("reports/coverage_visual.html", "w", encoding='utf-8') as f:
            f.write(html_content)
        
        print_success("Enhanced HTML coverage report generated: reports/coverage_visual.html")
        
    except Exception as e:
        print_error(f"Error generating enhanced HTML report: {e}")


def generate_coverage_badge():
    """Generate a coverage badge for the README."""
    coverage_file = Path("coverage.json")
    
    if coverage_file.exists():
        try:
            with open(coverage_file, 'r') as f:
                coverage_data = json.load(f)
            
            total_coverage = coverage_data.get('totals', {}).get('percent_covered', 0)
            
            # Color based on coverage percentage
            if total_coverage >= 90:
                color = "brightgreen"
            elif total_coverage >= 80:
                color = "yellow"
            elif total_coverage >= 70:
                color = "orange"
            else:
                color = "red"
            
            badge_url = f"https://img.shields.io/badge/coverage-{total_coverage:.1f}%25-{color}"
            print_info(f"Coverage badge: {badge_url}")
            
            return badge_url
            
        except Exception as e:
            print_warning(f"Could not generate coverage badge: {e}")
    
    return None


def generate_combined_coverage_html():
    """Generate a combined HTML coverage report with visual styling and hyperlinks to detailed pages."""
    coverage_file = Path("coverage.json")
    htmlcov_dir = Path("htmlcov")
    
    if not coverage_file.exists():
        print_warning("No coverage data found. Cannot generate enhanced HTML report.")
        return
    
    if not htmlcov_dir.exists():
        print_warning("Standard coverage HTML not found. Run coverage first.")
        return
    
    try:
        with open(coverage_file, 'r') as f:
            coverage_data = json.load(f)
        
        total_coverage = coverage_data.get('totals', {}).get('percent_covered', 0)
        files = coverage_data.get('files', {})
        
        # Filter out __init__.py files
        filtered_files = {path: data for path, data in files.items() 
                         if not path.endswith('__init__.py')}
        
        # Create mapping from file paths to HTML file names
        def get_html_filename(file_path):
            """Convert file path to coverage HTML filename."""
            # This mimics how coverage.py generates HTML filenames
            import hashlib
            # Normalize path separators
            normalized_path = file_path.replace('\\', '/')
            # Create hash-based filename similar to coverage.py
            path_hash = hashlib.md5(normalized_path.encode()).hexdigest()[:16]
            safe_name = normalized_path.replace('/', '_').replace('\\', '_').replace('.', '_')
            return f"z_{path_hash}_{safe_name}_py.html"
        
        # Generate HTML content
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Coverage Report - Crypto Trading Bot</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
        }}
        .header p {{
            margin: 10px 0 0 0;
            opacity: 0.9;
        }}
        .overall-stats {{
            padding: 30px;
            background: #fff;
            border-bottom: 1px solid #eee;
        }}
        .stat-card {{
            display: inline-block;
            margin: 10px 20px 10px 0;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
            min-width: 150px;
            text-align: center;
        }}
        .stat-card h3 {{
            margin: 0 0 10px 0;
            font-size: 2em;
            color: #333;
        }}
        .stat-card p {{
            margin: 0;
            color: #666;
        }}
        .progress-container {{
            margin: 20px 0;
        }}
        .progress-bar {{
            width: 100%;
            height: 30px;
            background-color: #e9ecef;
            border-radius: 15px;
            overflow: hidden;
            position: relative;
        }}
        .progress-fill {{
            height: 100%;
            transition: width 0.8s ease-in-out;
            position: relative;
        }}
        .progress-excellent {{
            background: linear-gradient(45deg, #28a745, #20c997);
        }}
        .progress-good {{
            background: linear-gradient(45deg, #ffc107, #fd7e14);
        }}
        .progress-poor {{
            background: linear-gradient(45deg, #dc3545, #e74c3c);
        }}
        .progress-text {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            color: white;
            font-weight: bold;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
        }}
        .files-section {{
            padding: 30px;
        }}
        .file-item {{
            display: flex;
            align-items: center;
            padding: 15px;
            margin: 10px 0;
            background: #f8f9fa;
            border-radius: 8px;
            transition: all 0.3s ease;
        }}
        .file-item:hover {{
            background: #e9ecef;
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }}
        .file-name {{
            flex: 1;
            font-weight: 600;
            color: #495057;
        }}
        .file-name a {{
            color: #495057;
            text-decoration: none;
            transition: color 0.3s ease;
        }}
        .file-name a:hover {{
            color: #007bff;
            text-decoration: underline;
        }}
        .file-progress {{
            flex: 2;
            margin: 0 20px;
        }}
        .file-percentage {{
            min-width: 80px;
            text-align: right;
            font-weight: bold;
        }}
        .file-status {{
            min-width: 100px;
            text-align: center;
            font-size: 0.9em;
        }}
        .status-excellent {{
            color: #28a745;
            font-weight: bold;
        }}
        .status-good {{
            color: #ffc107;
            font-weight: bold;
        }}
        .status-poor {{
            color: #dc3545;
            font-weight: bold;
        }}
        .file-progress .progress-bar {{
            height: 20px;
        }}
        .navigation {{
            padding: 20px 30px;
            background: #f8f9fa;
            border-top: 1px solid #eee;
        }}
        .nav-links {{
            display: flex;
            gap: 20px;
            justify-content: center;
        }}
        .nav-link {{
            padding: 10px 20px;
            background: #007bff;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            transition: background 0.3s ease;
        }}
        .nav-link:hover {{
            background: #0056b3;
        }}
        .timestamp {{
            text-align: center;
            color: #6c757d;
            font-size: 0.9em;
            margin-top: 10px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧪 Crypto Trading Bot Coverage Report</h1>
            <p>Comprehensive test coverage analysis with detailed insights</p>
        </div>
        
        <div class="overall-stats">
            <div class="stat-card">
                <h3>{total_coverage:.1f}%</h3>
                <p>Total Coverage</p>
            </div>
            <div class="stat-card">
                <h3>{len(filtered_files)}</h3>
                <p>Files Analyzed</p>
            </div>
            <div class="stat-card">
                <h3>{sum(data.get('summary', {}).get('num_statements', 0) for data in filtered_files.values())}</h3>
                <p>Total Statements</p>
            </div>
            
            <div class="progress-container">
                <div class="progress-bar">
                    <div class="progress-fill {'progress-excellent' if total_coverage >= 90 else 'progress-good' if total_coverage >= 70 else 'progress-poor'}" 
                         style="width: {total_coverage}%">
                        <div class="progress-text">{total_coverage:.1f}% Overall Coverage</div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="files-section">
            <h2>📁 File Coverage Details</h2>
"""
        
        # Sort files by coverage percentage (lowest first to highlight problem areas)
        sorted_files = sorted(filtered_files.items(), 
                            key=lambda x: x[1].get('summary', {}).get('percent_covered', 0))
        
        for file_path, file_data in sorted_files:
            coverage = file_data.get('summary', {}).get('percent_covered', 0)
            statements = file_data.get('summary', {}).get('num_statements', 0)
            missing = file_data.get('summary', {}).get('missing_lines', 0)
            
            # Determine status and progress class
            if coverage >= 90:
                status = "Excellent"
                status_class = "status-excellent"
                progress_class = "progress-excellent"
            elif coverage >= 70:
                status = "Good"
                status_class = "status-good"
                progress_class = "progress-good"
            else:
                status = "Needs Work"
                status_class = "status-poor"
                progress_class = "progress-poor"
            
            # Try to find the corresponding HTML file
            html_filename = get_html_filename(file_path)
            html_path = htmlcov_dir / html_filename
            
            # Check if HTML file exists, otherwise look for similar files
            if not html_path.exists():
                # Try to find the file by looking for files containing the base name
                base_name = Path(file_path).stem
                matching_files = [f for f in htmlcov_dir.glob("*.html") 
                                if base_name.replace('_', '') in f.name or 
                                   file_path.replace('\\', '_').replace('/', '_') in f.name]
                if matching_files:
                    html_filename = matching_files[0].name
                else:
                    html_filename = None
            
            # Create the file item HTML
            file_display_name = file_path.replace('\\', '/')
            if html_filename:
                file_link = f'<a href="htmlcov/{html_filename}" target="_blank">{file_display_name}</a>'
            else:
                file_link = file_display_name
            
            html_content += f"""
            <div class="file-item">
                <div class="file-name">{file_link}</div>
                <div class="file-progress">
                    <div class="progress-bar">
                        <div class="progress-fill {progress_class}" style="width: {coverage}%">
                            <div class="progress-text">{coverage:.1f}%</div>
                        </div>
                    </div>
                </div>
                <div class="file-percentage">{coverage:.1f}%</div>
                <div class="file-status {status_class}">{status}</div>
            </div>
"""
        
        # Add footer with navigation
        html_content += f"""
        </div>
        
        <div class="navigation">
            <div class="nav-links">
                <a href="htmlcov/index.html" class="nav-link" target="_blank">📊 Standard Coverage Report</a>
                <a href="htmlcov/function_index.html" class="nav-link" target="_blank">⚙️ Function Coverage</a>
                <a href="htmlcov/class_index.html" class="nav-link" target="_blank">🏗️ Class Coverage</a>
                <a href="reports/test_report.html" class="nav-link" target="_blank">🧪 Test Results</a>
            </div>
            <div class="timestamp">Generated on {datetime.now().strftime('%Y-%m-%d at %H:%M:%S')}</div>
        </div>
    </div>

    <script>
        // Animate progress bars on page load
        document.addEventListener('DOMContentLoaded', function() {{
            const progressBars = document.querySelectorAll('.progress-fill');
            progressBars.forEach(bar => {{
                const width = bar.style.width;
                bar.style.width = '0%';
                setTimeout(() => {{
                    bar.style.width = width;
                }}, 100);
            }});
        }});
    </script>
</body>
</html>
"""
        
        # Write the HTML file
        reports_dir = Path("reports")
        reports_dir.mkdir(exist_ok=True)
        
        with open("reports/coverage_combined.html", "w", encoding='utf-8') as f:
            f.write(html_content)
        
        print_success("Enhanced combined coverage report generated: reports/coverage_combined.html")
        print_info("✨ Features: Visual progress bars, hyperlinks to detailed coverage, and modern UI!")
        
    except Exception as e:
        print_error(f"Error generating combined HTML report: {e}")
        import traceback
        traceback.print_exc()


def open_reports():
    """Open generated reports in browser."""
    reports = [
        ("htmlcov/index.html", "Coverage Report"),
        ("reports/test_report.html", "Test Results Report")
    ]
    
    print_header("Opening Reports")
    
    for report_path, report_name in reports:
        if Path(report_path).exists():
            try:
                abs_path = Path(report_path).absolute()
                webbrowser.open(f"file://{abs_path}")
                print_success(f"Opened {report_name}")
                print_info(f"URL: file://{abs_path}")
            except Exception as e:
                print_warning(f"Could not open {report_name}: {e}")
        else:
            print_warning(f"{report_name} not found at {report_path}")


def open_enhanced_coverage():
    """Open the enhanced visual coverage report."""
    enhanced_path = "reports/coverage_visual.html"
    
    if Path(enhanced_path).exists():
        try:
            abs_path = Path(enhanced_path).absolute()
            webbrowser.open(f"file://{abs_path}")
            print_success("Enhanced coverage report opened in browser")
            print_info(f"URL: file://{abs_path}")
            print_info("✨ Features: Visual progress bars, file statistics, and interactive elements!")
        except Exception as e:
            print_error(f"Could not open enhanced coverage report: {e}")
    else:
        print_error("Enhanced coverage report not found. Run tests first with: python run_tests.py all")


def open_coverage_only():
    """Open only the HTML coverage report."""
    coverage_path = "htmlcov/index.html"
    
    if Path(coverage_path).exists():
        try:
            abs_path = Path(coverage_path).absolute()
            webbrowser.open(f"file://{abs_path}")
            print_success("Coverage report opened in browser")
            print_info(f"URL: file://{abs_path}")
            print_info("💡 Tip: Bookmark this URL for quick access!")
        except Exception as e:
            print_error(f"Could not open coverage report: {e}")
    else:
        print_error("Coverage report not found. Run tests first with: python run_tests.py all")
    """Open only the HTML coverage report."""
    coverage_path = "htmlcov/index.html"
    
    if Path(coverage_path).exists():
        try:
            abs_path = Path(coverage_path).absolute()
            webbrowser.open(f"file://{abs_path}")
            print_success("Coverage report opened in browser")
            print_info(f"URL: file://{abs_path}")
            print_info("💡 Tip: Bookmark this URL for quick access!")
        except Exception as e:
            print_error(f"Could not open coverage report: {e}")
    else:
        print_error("Coverage report not found. Run tests first with: python run_tests.py all")


def show_coverage_summary():
    """Show a quick coverage summary in terminal."""
    coverage_file = Path("coverage.json")
    
    if not coverage_file.exists():
        print_error("No coverage data found. Run tests first with: python run_tests.py all")
        return
    
    try:
        with open(coverage_file, 'r') as f:
            coverage_data = json.load(f)
        
        total_coverage = coverage_data.get('totals', {}).get('percent_covered', 0)
        
        print_header("📊 Coverage Summary")
        
        # Overall coverage with visual indicator
        if total_coverage >= 90:
            coverage_icon = "🟢"
            status = "EXCELLENT"
        elif total_coverage >= 80:
            coverage_icon = "🟡"
            status = "GOOD"
        elif total_coverage >= 70:
            coverage_icon = "🟠"
            status = "NEEDS WORK"
        else:
            coverage_icon = "🔴"
            status = "POOR"
        
        print(f"{coverage_icon} {Colors.BOLD}Overall Coverage: {total_coverage:.1f}% ({status}){Colors.ENDC}")
        
        # File breakdown
        files = coverage_data.get('files', {})
        if files:
            print(f"\n{Colors.BOLD}📁 File Coverage:{Colors.ENDC}")
            
            # Sort files by coverage percentage and filter out __init__.py files
            file_coverage = [(file_path, file_data.get('summary', {}).get('percent_covered', 0)) 
                           for file_path, file_data in files.items()
                           if not file_path.endswith('__init__.py')]
            file_coverage.sort(key=lambda x: x[1])
            
            for file_path, coverage in file_coverage:
                if coverage < 70:
                    color = Colors.FAIL
                    icon = "🔴"
                elif coverage < 90:
                    color = Colors.WARNING
                    icon = "🟡"
                else:
                    color = Colors.OKGREEN
                    icon = "🟢"
                
                # Shorten file path for display
                short_path = file_path.replace('\\', '/').split('/')[-1]
                print(f"  {icon} {color}{short_path}: {coverage:.1f}%{Colors.ENDC}")
        
        print(f"\n💡 {Colors.OKCYAN}Quick Access:{Colors.ENDC}")
        print(f"  • Full HTML report: python run_tests.py coverage-html")
        print(f"  • All reports: python run_tests.py reports")
        
    except Exception as e:
        print_error(f"Error reading coverage data: {e}")


def run_full_test_suite():
    """Run the complete test suite with coverage."""
    print_header("🚀 Running Full Test Suite with Coverage")
    
    ensure_directories()
    
    # Run tests with coverage and progress bar
    success = run_command(
        "python -m pytest Tests/ -v --cov=Strategies --cov=Exchanges --cov=Utils --cov-report=html --cov-report=json --cov-report=xml --cov-report=term-missing --html=reports/test_report.html --self-contained-html",
        "Running all tests with coverage and reports",
        show_progress=True
    )
    
    if success:
        # Analyze coverage results
        coverage_ok = check_coverage_results()
        
        # Generate coverage badge
        generate_coverage_badge()
        
        # Generate enhanced HTML coverage report
        generate_enhanced_coverage_html()
        
        # Generate combined coverage report
        generate_combined_coverage_html()
        
        # Create summary report
        create_test_summary()
        
        # Show quick coverage summary
        show_coverage_summary()
        
        if coverage_ok:
            print_success("All tests passed and coverage requirements met!")
            print_info("💡 Open combined coverage report with: python run_tests.py coverage-combined")
        else:
            print_error("Tests passed but coverage below 90% requirement")
            return False
    
    return success


def create_test_summary():
    """Create a test execution summary."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    summary = f"""
# Test Execution Summary

**Generated:** {timestamp}

## Coverage Reports Available

- **HTML Coverage Report:** `htmlcov/index.html`
- **Test Results Report:** `reports/test_report.html`
- **Coverage Data (JSON):** `coverage.json`
- **Coverage Data (XML):** `coverage.xml`

## Quick Access Commands

```bash
# Run all tests with coverage
python run_tests.py all

# Run specific test suites
python run_tests.py exchanges
python run_tests.py strategies
python run_tests.py integration

# Open coverage reports
python run_tests.py reports
```

## Coverage Requirements

- **Minimum Coverage:** 90%
- **Scope:** All implementation code (Strategies, Exchanges, Utils)
- **Exclusions:** Test files, main.py, cache files
"""
    
    with open("reports/test_summary.md", "w") as f:
        f.write(summary)
    
    print_info("Test summary created: reports/test_summary.md")


def main():
    """Enhanced main test runner with coverage enforcement."""
    
    # Ensure we're in the project root
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    if len(sys.argv) < 2:
        print_header("Crypto Trading Bot - Test Runner")
        print("Usage: python run_tests.py <command>\n")
        print(f"{Colors.BOLD}Available commands:{Colors.ENDC}")
        print("  all           - Run all tests with coverage (90% minimum)")
        print("  unit          - Run only unit tests")
        print("  compliance    - Run only compliance tests")
        print("  exchanges     - Run only exchange implementation tests")
        print("  strategies    - Run only strategy implementation tests")
        print("  integration   - Run only integration tests")
        print("  utils         - Run only utils tests")
        print("  coverage      - Generate coverage report only")
        print("  coverage-html - Open HTML coverage report in browser")
        print("  coverage-combined - Open enhanced combined coverage report with hyperlinks")
        print("  coverage-summary - Show quick coverage summary in terminal")
        print("  reports       - Open all HTML reports in browser")
        print("  install       - Install test dependencies")
        print("  clean         - Clean generated reports")
        print("  full          - Run complete test suite with all reports")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "install":
        success = run_command(
            "pip install pytest pytest-cov coverage pytest-html pytest-mock responses tqdm",
            "Installing test dependencies"
        )
        if success:
            print_success("Test dependencies installed successfully!")
            print_info("You can now run tests with: python run_tests.py all")
    
    elif command == "all" or command == "full":
        success = run_full_test_suite()
        if success:
            print_info("Opening coverage reports...")
            open_reports()
    
    elif command == "unit":
        success = run_command(
            "python -m pytest Tests/unit/ -v --cov=Strategies --cov=Exchanges --cov=Utils --cov-report=term-missing",
            "Running unit tests with coverage",
            show_progress=True
        )
    
    elif command == "compliance":
        success = run_command(
            "python -m pytest Tests/unit/compliance/ -v",
            "Running compliance tests",
            show_progress=True
        )
    
    elif command == "exchanges":
        success = run_command(
            "python -m pytest Tests/unit/exchanges/ -v --cov=Exchanges --cov-report=term-missing",
            "Running exchange implementation tests",
            show_progress=True
        )
    
    elif command == "strategies":
        success = run_command(
            "python -m pytest Tests/unit/strategies/ -v --cov=Strategies --cov-report=term-missing",
            "Running strategy implementation tests",
            show_progress=True
        )
    
    elif command == "integration":
        success = run_command(
            "python -m pytest Tests/integration/ -v --cov=Strategies --cov=Exchanges --cov-report=term-missing",
            "Running integration tests",
            show_progress=True
        )
    
    elif command == "utils":
        success = run_command(
            "python -m pytest Tests/unit/utils/ -v --cov=Utils --cov-report=term-missing",
            "Running utils tests",
            show_progress=True
        )
    
    elif command == "coverage":
        ensure_directories()
        success = run_command(
            "python -m coverage report --show-missing",
            "Generating coverage report"
        )
        if success:
            check_coverage_results()
    
    elif command == "reports":
        open_reports()
        success = True
    
    elif command == "coverage-html":
        open_coverage_only()
        success = True
    
    elif command == "coverage-combined":
        # Generate and open the combined coverage report
        generate_combined_coverage_html()
        combined_path = "reports/coverage_combined.html"
        if Path(combined_path).exists():
            try:
                abs_path = Path(combined_path).absolute()
                webbrowser.open(f"file://{abs_path}")
                print_success("Combined coverage report opened in browser")
                print_info(f"URL: file://{abs_path}")
                print_info("✨ Features: Visual progress bars with clickable file links!")
            except Exception as e:
                print_error(f"Could not open combined coverage report: {e}")
        success = True
    
    elif command == "coverage-summary":
        show_coverage_summary()
        success = True
    
    elif command == "clean":
        import shutil
        dirs_to_clean = ['htmlcov', 'reports', '.pytest_cache', '__pycache__']
        files_to_clean = ['coverage.json', 'coverage.xml', '.coverage']
        
        for dir_name in dirs_to_clean:
            if Path(dir_name).exists():
                shutil.rmtree(dir_name)
                print_info(f"Removed {dir_name}/")
        
        for file_name in files_to_clean:
            if Path(file_name).exists():
                os.remove(file_name)
                print_info(f"Removed {file_name}")
        
        print_success("Cleaned generated reports and cache files")
        success = True
    
    else:
        print_error(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()