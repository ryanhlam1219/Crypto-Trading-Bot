#!/usr/bin/env python3
"""
Simple Compile Script for Crypto Trading Bot

This is the main script to compile and validate your code.
It focuses on practical compilation validation rather than requiring perfect tests.

Usage:
    python compile.py              # Practical compile with working tests
    python compile.py --syntax     # Just syntax validation
    python compile.py --full       # Full test run (may have failures)
"""

import sys
from pathlib import Path

# Import our practical build runner
from build.scripts.quick_compile import PracticalBuildRunner

def main():
    """Simple compilation entry point"""
    print("🔨 COMPILING CRYPTO TRADING BOT...")
    print()
    
    # Parse simple arguments
    args = sys.argv[1:]
    syntax_only = '--syntax' in args
    full_tests = '--full' in args
    
    # Run build
    project_root = Path(__file__).parent
    builder = PracticalBuildRunner(str(project_root))
    
    success = builder.run_build(
        syntax_only=syntax_only,
        run_full_tests=full_tests
    )
    
    if success:
        print("\n🎉 COMPILATION SUCCESSFUL!")
        print("✅ Code compiles and is ready for use")
        print("🚀 Ready for development!")
    else:
        print("\n💥 COMPILATION FAILED!")
        print("❌ Please fix critical issues and try again")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()