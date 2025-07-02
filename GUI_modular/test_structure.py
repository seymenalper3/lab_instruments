#!/usr/bin/env python3
"""
Test script to verify the modular structure
"""
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all modules can be imported"""
    print("Testing module imports...")
    
    try:
        # Test interface imports
        from interfaces.base_interface import DeviceInterface
        from interfaces.serial_interface import SerialInterface
        from interfaces.ethernet_interface import EthernetInterface
        from interfaces.visa_interface import VISAInterface
        print("✓ Interface modules imported successfully")
        
        # Test model imports
        from models.device_config import DeviceSpec, ConnectionConfig, DEVICE_SPECS, DeviceType
        print("✓ Model modules imported successfully")
        
        # Test controller imports
        from controllers.base_controller import BaseDeviceController
        from controllers.sorensen_controller import SorensenController
        from controllers.keithley_controller import KeithleyController
        from controllers.prodigit_controller import ProdigitController
        print("✓ Controller modules imported successfully")
        
        # Test utility imports
        from utils.data_logger import DataLogger
        print("✓ Utility modules imported successfully")
        
        # Test GUI imports
        from gui.connection_widget import ConnectionWidget
        from gui.device_tab import DeviceTab
        from gui.sorensen_tab import SorensenTab
        from gui.keithley_tab import KeithleyTab
        from gui.prodigit_tab import ProdigitTab
        from gui.monitoring_tab import MonitoringTab
        from gui.main_window import MainWindow
        print("✓ GUI modules imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False

def test_device_specs():
    """Test device specifications"""
    print("\nTesting device specifications...")
    
    from models.device_config import DEVICE_SPECS, DeviceType
    
    # Check that all device specs are defined
    expected_devices = [DeviceType.SORENSEN_SGX, DeviceType.KEITHLEY_2281S, DeviceType.PRODIGIT_34205A]
    
    for device_type in expected_devices:
        if device_type in DEVICE_SPECS:
            spec = DEVICE_SPECS[device_type]
            print(f"✓ {spec.name}: {spec.max_voltage}V, {spec.max_current}A")
            print(f"  Interfaces: {[iface.value for iface in spec.supported_interfaces]}")
            print(f"  Commands: {len(spec.default_commands)} defined")
        else:
            print(f"✗ Missing specification for {device_type}")
            return False
    
    return True

def test_connection_config():
    """Test connection configuration creation"""
    print("\nTesting connection configurations...")
    
    from models.device_config import ConnectionConfig
    
    # Test serial config
    serial_config = ConnectionConfig.create_serial("/dev/ttyUSB0", 9600)
    print(f"✓ Serial config: {serial_config.interface_type.value}")
    
    # Test ethernet config  
    eth_config = ConnectionConfig.create_ethernet("192.168.1.100", 5025)
    print(f"✓ Ethernet config: {eth_config.interface_type.value}")
    
    # Test VISA config
    visa_config = ConnectionConfig.create_visa("USB0::0x05E6::0x2281S::4587429::0::INSTR")
    print(f"✓ VISA config: {visa_config.interface_type.value}")
    
    return True

def test_data_logger():
    """Test data logger functionality"""
    print("\nTesting data logger...")
    
    from utils.data_logger import DataLogger
    
    logger = DataLogger()
    logger.set_sample_interval(0.5)
    
    print(f"✓ Data logger created, interval: {logger.sample_interval}s")
    print(f"✓ Data count: {logger.get_data_count()}")
    
    return True

def main():
    """Run all tests"""
    print("=" * 50)
    print("MODULAR GUI STRUCTURE TEST")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_device_specs,
        test_connection_config,
        test_data_logger
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print("Test failed!")
        except Exception as e:
            print(f"Test error: {e}")
    
    print("\n" + "=" * 50)
    print(f"RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ All tests passed! The modular structure is working correctly.")
        print("\nTo run the GUI application:")
        print("  python main.py")
    else:
        print("✗ Some tests failed. Check the error messages above.")
        
    print("=" * 50)

if __name__ == "__main__":
    main()