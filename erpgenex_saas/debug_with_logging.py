import frappe
import logging

# Set up detailed logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("erpgenex_saas")
logger.setLevel(logging.DEBUG)

def debug_with_logging():
    """Debug with detailed logging"""
    try:
        # Get the latest tenant
        tenant = frappe.get_last_doc("SaaS Tenant")
        
        print(f"Tenant: {tenant.name}")
        print(f"Site Name: {tenant.site_name}")
        
        # Enable detailed logging for erpgenex_saas
        frappe.logger("erpgenex_saas").setLevel(logging.DEBUG)
        
        # Call create_site
        from erpgenex_saas.services.provisioning import ProvisioningService
        
        print(f"\nCalling create_site with detailed logging...")
        result = ProvisioningService.create_site(tenant.site_name, tenant.name)
        
        print(f"Result: {result}")
        
        return result
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None
