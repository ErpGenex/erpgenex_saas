import frappe
import json
import os

def fix_db_password_from_main_site():
    """Use the main site's database password for the new site"""
    try:
        # Read main site config
        main_config_path = "/home/frappeuser/frappe-bench/sites/erpgenex.local.site/site_config.json"
        with open(main_config_path, 'r') as f:
            main_config = json.load(f)
        
        main_db_password = main_config['db_password']
        print(f"Main site DB password: {main_db_password}")
        
        # Update SaaS Settings
        saas_settings = frappe.get_single("SaaS Settings")
        saas_settings.database_password = main_db_password
        saas_settings.mariadb_root_password = main_db_password
        saas_settings.save(ignore_permissions=True)
        
        print(f"Updated SaaS Settings with main site DB password")
        
        # Get tenant
        tenant = frappe.get_last_doc("SaaS Tenant")
        
        # Handle port-based site names
        if ":" in tenant.site_name:
            folder_name = tenant.site_name.split(":")[0]
            port = tenant.site_name.split(":")[1]
            folder_name = f"{folder_name}_port_{port}"
        else:
            folder_name = tenant.site_name
        
        # Update new site config
        new_config_path = f"/home/frappeuser/frappe-bench/sites/{folder_name}/site_config.json"
        with open(new_config_path, 'r') as f:
            new_config = json.load(f)
        
        new_config['db_password'] = main_db_password
        
        with open(new_config_path, 'w') as f:
            json.dump(new_config, f, indent=2)
        
        print(f"Updated new site config with main site DB password")
        
        return True
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
