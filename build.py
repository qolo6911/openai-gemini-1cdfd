#!/usr/bin/env python3
"""Build script for XAUUSD Trading System"""

import os
import sys
import subprocess


def check_dependencies():
    """Check if all required dependencies are installed"""
    print("Checking dependencies...")
    
    try:
        import PyQt5
        print("✓ PyQt5 installed")
    except ImportError:
        print("✗ PyQt5 not found. Installing...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'PyQt5'])
    
    try:
        import matplotlib
        print("✓ matplotlib installed")
    except ImportError:
        print("✗ matplotlib not found. Installing...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'matplotlib'])
    
    try:
        import pandas
        print("✓ pandas installed")
    except ImportError:
        print("✗ pandas not found. Installing...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pandas'])
    
    try:
        import numpy
        print("✓ numpy installed")
    except ImportError:
        print("✗ numpy not found. Installing...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'numpy'])
    
    try:
        import torch
        print("✓ PyTorch installed")
    except ImportError:
        print("✗ PyTorch not found. Installing...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'torch'])
    
    print("\nAll dependencies satisfied!")


def build_exe():
    """Build the executable using PyInstaller"""
    print("\n" + "=" * 60)
    print("Building executable with PyInstaller...")
    print("=" * 60)
    
    try:
        import PyInstaller
    except ImportError:
        print("PyInstaller not found. Installing...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pyinstaller'])
    
    spec_file = 'build_exe.spec'
    
    if not os.path.exists(spec_file):
        print(f"Error: {spec_file} not found!")
        return False
    
    try:
        subprocess.check_call(['pyinstaller', spec_file])
        print("\n✓ Build completed successfully!")
        print(f"Executable location: dist/XAUUSD_Trading_System.exe")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Build failed: {e}")
        return False


def main():
    print("=" * 60)
    print("XAUUSD Trading System - Build Script")
    print("=" * 60)
    
    if '--check-only' in sys.argv:
        check_dependencies()
        return 0
    
    if '--build' in sys.argv:
        check_dependencies()
        if build_exe():
            return 0
        else:
            return 1
    
    print("\nUsage:")
    print("  python build.py --check-only    Check dependencies only")
    print("  python build.py --build         Build the executable")
    print("\nNote: Building the executable may take several minutes")
    print("      and the resulting file will be ~150-250MB")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
