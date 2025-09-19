#!/usr/bin/env python3
"""
Daily Build Workflow for Crypto Trading Bot

This script provides different build modes for different development scenarios:

Usage:
    python build.py                    # Quick syntax check
    python build.py --compile          # Full compile validation  
    python build.py --test             # Run working tests
    python build.py --coverage         # Generate coverage reports
    python build.py --all              # Complete build cycle

Examples:
    python build.py                    # Before committing code
    python build.py --compile          # Before deploying  
    python build.py --test             # After making changes
    python build.py --coverage         # To check test coverage
"""

import sys
import subprocess
from pathlib import Path
from datetime import datetime

# Get the correct Python executable
PYTHON_EXE = sys.executable


def print_banner(title: str):
    """Print a nice banner"""
    print("=" * 60)
    print(f"🚀 {title}")
    print("=" * 60)


def run_command(cmd: str, description: str) -> bool:
    """Run a command and return success status"""
    print(f"📋 {description}...")
    
    result = subprocess.run(cmd, shell=True, cwd=Path(__file__).parent)
    
    if result.returncode == 0:
        print(f"✅ {description} completed successfully")
        return True
    else:
        print(f"❌ {description} failed")
        return False


def syntax_check():
    """Quick syntax validation"""
    print_banner("QUICK SYNTAX CHECK")
    success = run_command(f"{PYTHON_EXE} build/scripts/quick_compile.py --syntax-only", "Syntax validation")
    
    if success:
        print("\n🎉 CODE SYNTAX IS VALID!")
        print("✅ Safe to commit and continue development")
    else:
        print("\n💥 SYNTAX ERRORS FOUND!")
        print("❌ Please fix syntax errors before proceeding")
    
    return success


def compile_check():
    """Full compilation validation"""
    print_banner("COMPILATION VALIDATION")
    success = run_command(f"{PYTHON_EXE} build/scripts/quick_compile.py", "Code compilation")
    
    if success:
        print("\n🎉 CODE COMPILES SUCCESSFULLY!")
        print("✅ Ready for testing and deployment")
    else:
        print("\n⚠️ COMPILATION ISSUES DETECTED")
        print("🔧 Check import and dependency issues")
    
    return success


def test_run():
    """Run available tests"""
    print_banner("TEST EXECUTION")
    success = run_command(f"{PYTHON_EXE} build/scripts/quick_compile.py --full", "Test execution")
    
    if success:
        print("\n🎉 TESTS COMPLETED!")
        print("✅ Core functionality verified")
    else:
        print("\n⚠️ SOME TESTS FAILED")
        print("🔧 Review test results and fix issues")
    
    return success


def coverage_generation():
    """Generate coverage reports"""
    print_banner("COVERAGE ANALYSIS")
    success = run_command(f"{PYTHON_EXE} build/core/run_dynamic_coverage.py", "Coverage generation")
    
    if success:
        print("\n🎉 COVERAGE REPORTS GENERATED!")
        print("📊 Check coverage.html for detailed results")
    else:
        print("\n⚠️ COVERAGE GENERATION ISSUES")
        print("🔧 Check test execution and coverage configuration")
    
    return success


def complete_build():
    """Complete build cycle"""
    print_banner("COMPLETE BUILD CYCLE")
    
    results = []
    
    # Step 1: Syntax check
    print("\n📋 Step 1: Syntax Validation")
    results.append(("Syntax Check", run_command(f"{PYTHON_EXE} build/scripts/quick_compile.py --syntax-only", "Syntax validation")))
    
    # Step 2: Compilation
    print("\n📋 Step 2: Compilation Validation")
    results.append(("Compilation", run_command(f"{PYTHON_EXE} build/scripts/quick_compile.py", "Code compilation")))
    
    # Step 3: Dynamic coverage (includes tests)
    print("\n📋 Step 3: Tests and Coverage")
    results.append(("Tests & Coverage", run_command(f"{PYTHON_EXE} build/core/run_dynamic_coverage.py", "Tests and coverage")))
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 COMPLETE BUILD SUMMARY")
    print("=" * 60)
    
    for step_name, success in results:
        icon = "✅" if success else "❌"
        print(f"{icon} {step_name}")
    
    overall_success = all(success for _, success in results)
    
    if overall_success:
        print("\n🎉 COMPLETE BUILD SUCCESSFUL!")
        print("✅ All steps completed successfully")
        print("🚀 Ready for production deployment!")
    else:
        print("\n⚠️ BUILD COMPLETED WITH ISSUES")
        print("🔧 Review failed steps and address issues")
        print("💡 Code may still be usable for development")
    
    return overall_success


def main():
    """Main entry point"""
    start_time = datetime.now()
    
    if len(sys.argv) == 1:
        # Default: quick syntax check
        success = syntax_check()
    elif "--compile" in sys.argv:
        success = compile_check()
    elif "--test" in sys.argv:
        success = test_run()
    elif "--coverage" in sys.argv:
        success = coverage_generation()
    elif "--all" in sys.argv:
        success = complete_build()
    else:
        print("Usage: python build.py [--compile|--test|--coverage|--all]")
        print("Default: quick syntax check")
        sys.exit(1)
    
    # Print timing
    end_time = datetime.now()
    duration = end_time - start_time
    print(f"\n⏱️ Completed in {duration.total_seconds():.2f} seconds")
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()