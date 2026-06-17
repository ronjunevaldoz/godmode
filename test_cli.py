#!/usr/bin/env python3
"""
Test script for GodMode CLI functionality
"""

import subprocess
import sys

def test_cli():
    """Test the CLI tool functionality"""
    
    # Test installation
    print("Testing CLI installation...")
    try:
        result = subprocess.run([sys.executable, "godmode_cli.py", "install-skills"], 
                              capture_output=True, text=True, cwd="/Users/ronvaldoz/Documents/godmode")
        print("Installation output:")
        print(result.stdout)
        if result.stderr:
            print("Errors:", result.stderr)
    except Exception as e:
        print(f"Error running installation: {e}")
    
    # Test skills listing
    print("\nTesting skills listing...")
    try:
        result = subprocess.run([sys.executable, "godmode_cli.py", "skills"], 
                              capture_output=True, text=True, cwd="/Users/ronvaldoz/Documents/godmode")
        print("Skills listing output:")
        print(result.stdout)
        if result.stderr:
            print("Errors:", result.stderr)
    except Exception as e:
        print(f"Error running skills listing: {e}")

if __name__ == "__main__":
    test_cli()