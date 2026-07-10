import frappe

def fix_site_url():
    """Fix site URL to use correct port"""
    try:
        tenant = frappe.get_last_doc("SaaS Tenant")
        
        print(f"Current Site URL: {tenant.site_url}")
        print(f"Port Number: {tenant.port_number}")
        
        # Fix the site URL to use the correct port
        tenant.site_url = f"http://192.168.1.2:{tenant.port_number}"
        tenant.save(ignore_permissions=True)
        
        print(f"Updated Site URL: {tenant.site_url}")
        
        return tenant.site_url
        
    except Exception as e:
        print(f"Error fixing site URL: {str(e)}")
        import traceback
        traceback.print_exc()
        return None
