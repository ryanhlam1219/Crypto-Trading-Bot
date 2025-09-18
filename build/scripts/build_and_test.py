#!/usr/bin/env python3
"""
Comprehensive Build and Test Script for Crypto Trading Bot

This script performs a complete build cycle:
1. Discovers source directories dynamically
2. Updates configuration files
3. Runs all unit tests with strict failure handling
4. Generates comprehensive coverage reports
5. Validates coverage thresholds
6. Provides detailed build summary

Usage:
    python build_and_test.py [pytest_args...]

Examples:
    python build_and_test.py                    # Full build with all tests
    python build_and_test.py -k test_binance    # Build with specific test filter
    python build_and_test.py --verbose          # Verbose output
    python build_and_test.py --quick            # Skip coverage threshold checks
"""

import subprocess
import sys
import os
import json
from pathlib import Path
from datetime import datetime
import argparse


class BuildTestRunner:
    """Comprehensive build and test runner"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.start_time = datetime.now()
        self.results = {
            'discovery': False,
            'tests_passed': False,
            'coverage_generated': False,
            'coverage_threshold_met': False,
            'build_successful': False
        }
        
    def print_header(self):
        """Print build header"""
        print("=" * 80)
        print("🚀 CRYPTO TRADING BOT - COMPREHENSIVE BUILD & TEST")
        print("=" * 80)
        print(f"⏰ Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📁 Project: {self.project_root}")
        print()
        
    def print_step(self, step_num: int, title: str, description: str):
        """Print step header"""
        print(f"📋 STEP {step_num}: {title}")
        print(f"   {description}")
        print("-" * 60)
        
    def run_command(self, cmd: str, description: str, critical: bool = True) -> bool:
        """Run command and handle results"""
        print(f"🔄 {description}...")
        
        result = subprocess.run(
            cmd, 
            shell=True, 
            capture_output=True, 
            text=True,
            cwd=self.project_root
        )
        
        if result.returncode == 0:
            print(f"✅ {description} - SUCCESS")
            if result.stdout.strip():
                print(f"📤 Output: {result.stdout.strip()}")
            return True
        else:
            status = "CRITICAL FAILURE" if critical else "WARNING"
            print(f"❌ {description} - {status}")
            if result.stderr.strip():
                print(f"📥 Error: {result.stderr.strip()}")
            if result.stdout.strip():
                print(f"📤 Output: {result.stdout.strip()}")
            
            if critical:
                print(f"\n💥 BUILD FAILED at: {description}")
                return False
            return True
    
    def step_1_discovery(self) -> bool:
        """Step 1: Dynamic source discovery and configuration update"""
        self.print_step(1, "DYNAMIC DISCOVERY", "Discovering source directories and updating configuration")
        
        success = self.run_command(
            "python generate_coverage_reports.py",
            "Dynamic source discovery",
            critical=True
        )
        
        self.results['discovery'] = success
        return success
    
    def step_2_run_tests(self, pytest_args: str = "", coverage_threshold: int = 90) -> bool:
        """Step 2: Run all unit tests with coverage"""
        self.print_step(2, "UNIT TESTING", "Running all unit tests with coverage tracking")
        
        # Build comprehensive pytest command
        base_cmd = (
            "python -m pytest Tests/ "
            "--cov-report=term-missing "
            "--cov-report=html:htmlcov "
            "--cov-report=xml:coverage.xml "
            "--cov-report=json:coverage.json "
            f"--cov-fail-under={coverage_threshold} "
            "--html=reports/test_report.html "
            "--self-contained-html "
            "-v "
            "--tb=short "
            "--strict-markers"
        )
        
        if pytest_args:
            base_cmd += f" {pytest_args}"
            
        success = self.run_command(
            base_cmd,
            "Unit tests with coverage",
            critical=True
        )
        
        self.results['tests_passed'] = success
        return success
    
    def step_3_generate_reports(self) -> bool:
        """Step 3: Generate dynamic coverage reports"""
        self.print_step(3, "REPORT GENERATION", "Generating comprehensive coverage reports")
        
        success = self.run_command(
            "python generate_coverage_reports.py",
            "Dynamic coverage report generation",
            critical=False
        )
        
        self.results['coverage_generated'] = success
        return success
    
    def step_4_validate_coverage(self, threshold: int = 90) -> bool:
        """Step 4: Validate coverage thresholds"""
        self.print_step(4, "COVERAGE VALIDATION", f"Validating coverage meets {threshold}% threshold")
        
        try:
            coverage_file = self.project_root / "coverage.json"
            if not coverage_file.exists():
                print("⚠️  Coverage JSON file not found - skipping validation")
                return True
                
            with open(coverage_file, 'r') as f:
                coverage_data = json.load(f)
            
            total_coverage = coverage_data.get('totals', {}).get('percent_covered', 0)
            
            print(f"📊 Total Coverage: {total_coverage:.2f}%")
            
            if total_coverage >= threshold:
                print(f"✅ Coverage threshold met: {total_coverage:.2f}% >= {threshold}%")
                self.results['coverage_threshold_met'] = True
                return True
            else:
                print(f"❌ Coverage threshold not met: {total_coverage:.2f}% < {threshold}%")
                self.results['coverage_threshold_met'] = False
                return False
                
        except Exception as e:
            print(f"⚠️  Could not validate coverage: {e}")
            return True
    
    def print_summary(self):
        """Print build summary"""
        end_time = datetime.now()
        duration = end_time - self.start_time
        
        print("\n" + "=" * 80)
        print("📋 BUILD SUMMARY")
        print("=" * 80)
        
        # Results
        status_icon = "✅" if self.results['build_successful'] else "❌"
        overall_status = "SUCCESS" if self.results['build_successful'] else "FAILED"
        
        print(f"{status_icon} Overall Status: {overall_status}")
        print(f"⏱️  Duration: {duration.total_seconds():.2f} seconds")
        print(f"🕐 Completed: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Step Results
        print("📝 Step Results:")
        steps = [
            ("Discovery & Configuration", self.results['discovery']),
            ("Unit Tests", self.results['tests_passed']),
            ("Report Generation", self.results['coverage_generated']),
            ("Coverage Validation", self.results['coverage_threshold_met'])
        ]
        
        for step_name, success in steps:
            icon = "✅" if success else "❌"
            print(f"   {icon} {step_name}")
        
        print()
        
        # Generated Artifacts
        if any(self.results.values()):
            print("📁 Generated Artifacts:")
            artifacts = [
                ("coverage.html", "Dynamic coverage homepage"),
                ("htmlcov/", "Detailed coverage reports"),
                ("reports/test_report.html", "Test execution report"),
                ("coverage.json", "Machine-readable coverage data"),
                ("coverage.xml", "XML coverage report")
            ]
            
            for artifact, description in artifacts:
                artifact_path = self.project_root / artifact
                if artifact_path.exists():
                    print(f"   📄 {artifact} - {description}")
        
        print("\n" + "=" * 80)
        
        if self.results['build_successful']:
            print("🎉 BUILD COMPLETED SUCCESSFULLY!")
            print("💡 All tests passed and coverage reports generated.")
        else:
            print("💥 BUILD FAILED!")
            print("🔧 Please review the errors above and fix issues before proceeding.")
        
        print("=" * 80)
    
    def run_full_build(self, pytest_args: str = "", coverage_threshold: int = 90, skip_coverage_check: bool = False) -> bool:
        """Run the complete build process"""
        self.print_header()
        
        try:
            # Step 1: Discovery
            if not self.step_1_discovery():
                return False
            
            # Step 2: Tests
            if not self.step_2_run_tests(pytest_args, coverage_threshold):
                return False
            
            # Step 3: Reports
            self.step_3_generate_reports()  # Non-critical
            
            # Step 4: Coverage validation
            if not skip_coverage_check:
                if not self.step_4_validate_coverage(coverage_threshold):
                    return False
            
            self.results['build_successful'] = True
            return True
            
        except KeyboardInterrupt:
            print("\n⏹️  Build interrupted by user")
            return False
        except Exception as e:
            print(f"\n💥 Unexpected error during build: {e}")
            return False
        finally:
            self.print_summary()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Comprehensive build and test script for Crypto Trading Bot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python build_and_test.py                    # Full build
  python build_and_test.py -k test_binance    # Run specific tests
  python build_and_test.py --quick            # Skip coverage checks
  python build_and_test.py --threshold 85     # Custom coverage threshold
        """
    )
    
    parser.add_argument(
        '--threshold', 
        type=int, 
        default=90,
        help='Coverage percentage threshold (default: 90)'
    )
    
    parser.add_argument(
        '--quick', 
        action='store_true',
        help='Skip coverage threshold validation for faster builds'
    )
    
    # Parse known args to allow pytest arguments to pass through
    args, pytest_args = parser.parse_known_args()
    
    # Convert pytest args back to string
    pytest_args_str = " ".join(pytest_args) if pytest_args else ""
    
    # Initialize and run build (go up to project root)
    project_root = Path(__file__).parent.parent.parent
    builder = BuildTestRunner(str(project_root))
    
    success = builder.run_full_build(
        pytest_args=pytest_args_str,
        coverage_threshold=args.threshold,
        skip_coverage_check=args.quick
    )
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()