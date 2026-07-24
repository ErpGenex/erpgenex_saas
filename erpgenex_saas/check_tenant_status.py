import frappe
from frappe.utils import get_bench_path

def check_tenant_status():
    """Check the current tenant status"""
    try:
        # Get the latest tenant
        tenant = frappe.get_last_doc("SaaS Tenant")
        
        print("Tenant Status:")
        print(f"Name: {tenant.tenant_name}")
        print(f"Site Name: {tenant.site_name}")
        print(f"Status: {tenant.status}")
        print(f"Port: {tenant.port_number}")
        print(f"Site URL: {tenant.site_url}")
        print(f"Admin Username: {tenant.admin_username}")
        print(f"Admin Password: {tenant.admin_password}")
        
        # Check if site folder exists
        import os
        bench_path = get_bench_path()
        if tenant.site_name:
            # Handle port-based site names
            if ":" in tenant.site_name:
                folder_name = tenant.site_name.split(":")[0]
                port = tenant.site_name.split(":")[1]
                folder_name = f"{folder_name}_port_{port}"
            else:
                folder_name = tenant.site_name
            
            site_path = os.path.join(bench_path, "sites", folder_name)
            print(f"\nSite Path: {site_path}")
            print(f"Site Exists: {os.path.exists(site_path)}")
            
            if os.path.exists(site_path):
                # Check site_config.json
                config_path = os.path.join(site_path, "site_config.json")
                if os.path.exists(config_path):
                    import json
                    with open(config_path, 'r') as f:
                        config = json.load(f)
                    print(f"DB Password in config: {config.get('db_password', 'Not set')}")
        
        return tenant
        
    except Exception as e:
        print(f"Error checking tenant status: {str(e)}")
        import traceback
        traceback.print_exc()
        return None
