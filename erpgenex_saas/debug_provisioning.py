import frappe

def debug_provisioning():
    """Debug the provisioning process"""
    try:
        # Get the latest tenant
        tenant = frappe.get_last_doc("SaaS Tenant")
        
        print(f"Tenant: {tenant.name}")
        print(f"Site Name: {tenant.site_name}")
        print(f"Status: {tenant.status}")
        print(f"Port: {tenant.port_number}")
        
        # Try to call create_site directly
        from erpgenex_saas.services.provisioning import ProvisioningService
        
        print(f"\nAttempting to create site directly...")
        result = ProvisioningService.create_site(tenant.site_name, tenant.name)
        
        print(f"Result: {result}")
        
        return result
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None
