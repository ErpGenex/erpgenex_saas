#!/usr/bin/env python
"""Test script for new services"""

import sys
import os

# Add the bench to the path
sys.path.insert(0, '/home/frappeuser/frappe-bench')

import frappe

# Initialize Frappe
frappe.init(site='erpgenex.local.site')
frappe.connect()

try:
    print("Testing PortManager...")
    from erpgenex_saas.services.port_manager import PortManager
    
    port_manager = PortManager()
    
    # Test get_available_port
    print("Testing get_available_port...")
    port = port_manager.get_available_port(start=8001)
    print(f"Available port: {port}")
    
    # Test is_port_available
    print("Testing is_port_available...")
    is_available = port_manager.is_port_available(port)
    print(f"Port {port} is available: {is_available}")
    
    # Test get_used_ports
    print("Testing get_used_ports...")
    used_ports = port_manager.get_used_ports()
    print(f"Used ports: {used_ports}")
    
    # Test get_available_ports_count
    print("Testing get_available_ports_count...")
    available_count = port_manager.get_available_ports_count()
    print(f"Available ports count: {available_count}")
    
    print("\nPortManager tests completed successfully!")
    
    print("\nTesting MonitoringService...")
    from erpgenex_saas.services.monitoring_service import MonitoringService
    
    monitoring = MonitoringService()
    
    # Test collect_metrics
    print("Testing collect_metrics...")
    metrics = monitoring.collect_metrics()
    print(f"System metrics: {metrics}")
    
    # Test check_health
    print("Testing check_health...")
    health = monitoring.check_health()
    print(f"System health: {health}")
    
    print("\nMonitoringService tests completed successfully!")
    
    print("\nAll tests passed!")
    
except Exception as e:
    print(f"Error: {str(e)}")
    import traceback
    traceback.print_exc()
finally:
    frappe.destroy()
