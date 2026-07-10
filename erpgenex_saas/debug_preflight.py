import frappe

def debug_preflight():
    """Debug pre-flight checks"""
    try:
        from erpgenex_saas.services.provisioning import ProvisioningService
        
        print("Testing pre-flight checks...")
        result = ProvisioningService.pre_flight_checks()
        
        print(f"Pre-flight result: {result}")
        
        return result
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None
