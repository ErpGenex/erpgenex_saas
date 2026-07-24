import frappe
from erpgenex_saas.runtime_config import get_site_url

def fix_site_url():
    """Fix site URL to use correct port"""
    try:
        tenant = frappe.get_last_doc("SaaS Tenant")
        
        print(f"Current Site URL: {tenant.site_url}")
        print(f"Port Number: {tenant.port_number}")
        
        # Fix the site URL to use the correct port
        tenant.site_url = get_site_url(tenant.port_number)
        tenant.save(ignore_permissions=True)
        
        print(f"Updated Site URL: {tenant.site_url}")
        
        return tenant.site_url
        
    except Exception as e:
        print(f"Error fixing site URL: {str(e)}")
        import traceback
        traceback.print_exc()
        return None
