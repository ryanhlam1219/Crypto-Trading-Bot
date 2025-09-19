#!/usr/bin/env python3
"""
Dynamic Coverage Runner for Crypto Trading Bot

This script:
1. Runs the dynamic coverage discovery
2. Executes pytest with updated configuration
3. Regenerates the dynamic HTML reports

Usage: python run_dynamic_coverage.py [pytest-args]
"""

import sys
import subprocess
import os
from pathlib import Path

def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"Running {description}...")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    # Check if it's just a coverage warning (not a real failure)
    if result.returncode != 0:
        # If it's just coverage warnings, treat as success
        if "CoverageWarning" in result.stderr and "No contexts were measured" in result.stderr:
            print(f"{description} completed (with coverage warnings)")
            return True
        else:
            print(f"{description} failed!")
            print("STDERR:", result.stderr)
            return False
    
    print(f"{description} completed")
    return True

def main():
    """Main execution function"""
    project_root = Path(__file__).parent.parent.parent  # Go up to project root
    os.chdir(project_root)
    
    # Find the correct Python interpreter
    import sys
    python_exe = sys.executable  # Use the same Python interpreter that's running this script
    
    print("Dynamic Coverage Analysis for Crypto Trading Bot")
    print("=" * 60)
    
    # Step 1: Generate dynamic configuration
    print("Step 1: Discovering source files and updating configuration...")
    if not run_command(f"{python_exe} build/core/generate_coverage_reports.py", "Dynamic discovery"):
        return 1
    
    # Step 2: Run tests with coverage
    print("\nStep 2: Running tests with coverage...")
    
    # Build pytest command - explicitly add coverage for all main modules
    pytest_args = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else ""
    pytest_cmd = f"{python_exe} -m pytest Tests/ --cov=Exchanges --cov=Strategies --cov=Utils {pytest_args} -v"
    
    if not run_command(pytest_cmd, "Running tests with coverage"):
        print("Tests completed with failures, but continuing with report generation...")
    
    # Step 3: Regenerate dynamic reports
    print("\nStep 3: Regenerating dynamic coverage reports...")
    if not run_command(f"{python_exe} build/core/generate_coverage_reports.py", "Regenerating reports"):
        return 1
    
    print("\n" + "=" * 60)
    print("Dynamic coverage analysis complete!")
    print("\nGenerated Reports:")
    print("   coverage.html - Dynamic homepage with directory navigation")
    print("   htmlcov/ - Detailed file-by-file coverage reports")
    print("   coverage.json - Machine-readable coverage data")
    print("\nNext time you add new directories or files, just run this script again!")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())