import frappe

def debug_create_site():
    """Debug create_site function directly"""
    try:
        # Get the latest tenant
        tenant = frappe.get_last_doc("SaaS Tenant")
        
        print(f"Tenant: {tenant.name}")
        print(f"Site Name: {tenant.site_name}")
        
        # Call create_site with detailed error handling
        from erpgenex_saas.services.provisioning import ProvisioningService
        
        print(f"\nCalling create_site...")
        result = ProvisioningService.create_site(tenant.site_name, tenant.name)
        
        print(f"Result: {result}")
        
        return result
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None
