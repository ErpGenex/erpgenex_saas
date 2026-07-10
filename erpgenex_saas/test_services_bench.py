import frappe

def test_port_manager():
    """Test PortManager functionality"""
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
    
    print("PortManager tests completed successfully!")
    return True

def test_monitoring_service():
    """Test MonitoringService functionality"""
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
    
    print("MonitoringService tests completed successfully!")
    return True

def test_password_manager():
    """Test PasswordManager functionality"""
    print("\nTesting PasswordManager...")
    from erpgenex_saas.services.password_manager import PasswordManager
    
    password_manager = PasswordManager()
    
    # Test generate_password
    print("Testing generate_password...")
    password = password_manager.generate_password(length=12)
    print(f"Generated password: {password}")
    
    # Test validate_password_strength
    print("Testing validate_password_strength...")
    strength = password_manager.validate_password_strength(password)
    print(f"Password strength: {strength}")
    
    # Test get_db_password
    print("Testing get_db_password...")
    db_password = password_manager.get_db_password()
    print(f"DB password retrieved: {db_password[:8]}...")
    
    # Test get_mariadb_root_password
    print("Testing get_mariadb_root_password...")
    mariadb_password = password_manager.get_mariadb_root_password()
    print(f"MariaDB root password retrieved: {mariadb_password[:8]}...")
    
    # Test hash_password
    print("Testing hash_password...")
    hashed = password_manager.hash_password("test123")
    print(f"Hashed password: {hashed[:16]}...")
    
    # Test generate_api_key
    print("Testing generate_api_key...")
    api_key = password_manager.generate_api_key()
    print(f"Generated API key: {api_key[:16]}...")
    
    print("PasswordManager tests completed successfully!")
    return True

def test_progress_tracker():
    """Test ProgressTracker functionality"""
    print("\nTesting ProgressTracker...")
    from erpgenex_saas.services.progress_tracker import ProgressTracker
    
    progress_tracker = ProgressTracker()
    
    # Test get_all_progress
    print("Testing get_all_progress...")
    all_progress = progress_tracker.get_all_progress()
    print(f"All progress: {len(all_progress)} items")
    
    print("ProgressTracker tests completed successfully!")
    return True

def run_all_tests():
    """Run all tests"""
    try:
        test_port_manager()
        test_monitoring_service()
        test_password_manager()
        test_progress_tracker()
        print("\nAll tests passed!")
        return True
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
