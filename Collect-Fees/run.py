#!/usr/bin/env python3
"""
Fee Collection Runner

Main entry point for the fee collection system.
Configurable for different exchanges and trading pairs.
"""

import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(__file__))

from fee_collector import FeeCollector

def main():
    """Main entry point"""
    try:
        collector = FeeCollector()
        collector.run_infinite()
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())