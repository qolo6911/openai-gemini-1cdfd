#!/usr/bin/env python3
"""Basic tests for XAUUSD Trading System"""

import sys
import os

def test_imports():
    """Test that all required modules can be imported"""
    print("Testing imports...")
    
    try:
        import PyQt5.QtWidgets
        print("✓ PyQt5 imported successfully")
    except ImportError as e:
        print(f"✗ PyQt5 import failed: {e}")
        return False
    
    try:
        import matplotlib.pyplot
        print("✓ matplotlib imported successfully")
    except ImportError as e:
        print(f"✗ matplotlib import failed: {e}")
        return False
    
    try:
        import pandas
        print("✓ pandas imported successfully")
    except ImportError as e:
        print(f"✗ pandas import failed: {e}")
        return False
    
    try:
        import numpy
        print("✓ numpy imported successfully")
    except ImportError as e:
        print(f"✗ numpy import failed: {e}")
        return False
    
    try:
        import torch
        print("✓ PyTorch imported successfully")
        if torch.cuda.is_available():
            print(f"  ✓ CUDA available: {torch.cuda.get_device_name(0)}")
        else:
            print("  ⚠ CUDA not available (will use CPU)")
    except ImportError as e:
        print(f"✗ PyTorch import failed: {e}")
        return False
    
    return True


def test_core_modules():
    """Test that core modules can be imported"""
    print("\nTesting core modules...")
    
    try:
        from core.data.mt5_connector import MT5DataConnector
        print("✓ MT5DataConnector imported")
    except ImportError as e:
        print(f"✗ MT5DataConnector import failed: {e}")
        return False
    
    try:
        from core.features.indicators import calculate_ema, calculate_atr
        print("✓ Indicators module imported")
    except ImportError as e:
        print(f"✗ Indicators import failed: {e}")
        return False
    
    try:
        from core.models.tcn import TCN
        print("✓ TCN model imported")
    except ImportError as e:
        print(f"✗ TCN import failed: {e}")
        return False
    
    try:
        from utils.config_manager import load_config, save_config
        print("✓ Config manager imported")
    except ImportError as e:
        print(f"✗ Config manager import failed: {e}")
        return False
    
    return True


def test_gui_modules():
    """Test that GUI modules can be imported"""
    print("\nTesting GUI modules...")
    
    try:
        from gui.config_widget import ConfigWidget
        print("✓ ConfigWidget imported")
    except ImportError as e:
        print(f"✗ ConfigWidget import failed: {e}")
        return False
    
    try:
        from gui.training_widget import TrainingWidget
        print("✓ TrainingWidget imported")
    except ImportError as e:
        print(f"✗ TrainingWidget import failed: {e}")
        return False
    
    try:
        from gui.main_window import MainWindow
        print("✓ MainWindow imported")
    except ImportError as e:
        print(f"✗ MainWindow import failed: {e}")
        return False
    
    return True


def test_data_connector():
    """Test MT5DataConnector functionality"""
    print("\nTesting MT5DataConnector...")
    
    try:
        from core.data.mt5_connector import MT5DataConnector
        
        connector = MT5DataConnector()
        df = connector.fetch_data('M15', 100)
        
        if len(df) > 0:
            print(f"✓ Data fetched successfully: {len(df)} rows")
            print(f"  Columns: {', '.join(df.columns)}")
        else:
            print("✗ No data fetched")
            return False
        
    except Exception as e:
        print(f"✗ Data connector test failed: {e}")
        return False
    
    return True


def main():
    print("=" * 60)
    print("XAUUSD Trading System - Basic Tests")
    print("=" * 60)
    
    tests = [
        ("Imports", test_imports),
        ("Core Modules", test_core_modules),
        ("GUI Modules", test_gui_modules),
        ("Data Connector", test_data_connector),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 60)
    print("Test Summary:")
    print("=" * 60)
    
    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{test_name}: {status}")
    
    all_passed = all(result for _, result in results)
    
    print("=" * 60)
    if all_passed:
        print("✓ All tests passed!")
        return 0
    else:
        print("✗ Some tests failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
