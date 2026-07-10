import frappe
import json

def check_saas_settings():
    """Check SaaS Settings for database password"""
    try:
        saas_settings = frappe.get_single("SaaS Settings")
        
        print("SaaS Settings:")
        print(f"Server IP: {saas_settings.server_ip}")
        print(f"Server Port: {saas_settings.server_port}")
        print(f"Platform Domain: {saas_settings.platform_domain}")
        print(f"Database Password: {saas_settings.database_password}")
        print(f"MariaDB Root Password: {saas_settings.mariadb_root_password}")
        print(f"Site Distribution Method: {saas_settings.site_distribution_method}")
        
        # Check main site config for actual MariaDB password
        try:
            with open("/home/frappeuser/frappe-bench/sites/erpgenex.local.site/site_config.json", "r") as f:
                site_config = json.load(f)
                print(f"\nMain Site Config:")
                print(f"DB Name: {site_config.get('db_name')}")
                print(f"DB Password: {site_config.get('db_password')}")
        except Exception as e:
            print(f"Error reading site_config.json: {str(e)}")
        
        # Check if passwords are set
        if not saas_settings.database_password:
            print("\n⚠️ Database password is not set!")
            return False
        else:
            print("\n✅ Database password is set")
            return True
            
    except Exception as e:
        print(f"Error checking SaaS Settings: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
