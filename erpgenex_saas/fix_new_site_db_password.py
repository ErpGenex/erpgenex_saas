import frappe
import json
import os

def fix_new_site_db_password():
    """Fix database password for the new site"""
    try:
        # Get database password from SaaS Settings
        saas_settings = frappe.get_single("SaaS Settings")
        db_password = saas_settings.database_password
        
        print(f"Database password from SaaS Settings: {db_password}")
        
        # Get tenant
        tenant = frappe.get_last_doc("SaaS Tenant")
        
        # Handle port-based site names
        if ":" in tenant.site_name:
            folder_name = tenant.site_name.split(":")[0]
            port = tenant.site_name.split(":")[1]
            folder_name = f"{folder_name}_port_{port}"
        else:
            folder_name = tenant.site_name
        
        bench_path = "/home/frappeuser/frappe-bench"
        site_path = os.path.join(bench_path, "sites", folder_name)
        config_path = os.path.join(site_path, "site_config.json")
        
        print(f"Site config path: {config_path}")
        
        # Read current config
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        print(f"Current DB password in config: {config.get('db_password', 'Not set')}")
        
        # Update with correct password
        config['db_password'] = db_password
        
        # Write back
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"Updated DB password in config to: {db_password}")
        
        # Also update the site URL to use correct port
        tenant.site_url = f"http://192.168.1.2:{tenant.port_number}"
        tenant.save(ignore_permissions=True)
        
        print(f"Updated site URL to: {tenant.site_url}")
        
        return True
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
