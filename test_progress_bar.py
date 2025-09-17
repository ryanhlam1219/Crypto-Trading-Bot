#!/usr/bin/env python3
"""
Simple test script to verify progress bar functionality
"""

import time
from tqdm import tqdm

def test_progress_bar():
    """Test that the progress bar displays correctly"""
    print("Testing progress bar functionality...")
    
    # Test basic progress bar
    with tqdm(total=100, desc="Data fetching", unit="candles") as pbar:
        for i in range(100):
            time.sleep(0.01)  # Simulate work
            pbar.update(1)
            if i % 10 == 0:
                pbar.set_postfix(Price=f"${42000 + i * 10:.2f}")
    
    print("Progress bar test completed successfully!")

if __name__ == "__main__":
    test_progress_bar()
