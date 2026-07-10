import frappe
import subprocess
import os
import sys

def debug_create_site_full():
    """Debug create_site with full error handling and logging"""
    try:
        # Get the latest tenant
        tenant = frappe.get_last_doc("SaaS Tenant")
        
        print(f"Tenant: {tenant.name}")
        print(f"Site Name: {tenant.site_name}")
        
        # Import the service
        from erpgenex_saas.services.provisioning import ProvisioningService
        
        # Add detailed logging
        import logging
        logger = logging.getLogger("erpgenex_saas")
        logger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG)
        logger.addHandler(handler)
        
        print(f"\nCalling create_site with full logging...")
        result = ProvisioningService.create_site(tenant.site_name, tenant.name)
        
        print(f"\nResult: {result}")
        
        return result
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None
