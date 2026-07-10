import frappe

def update_saas_settings():
    """Update SaaS Settings with MariaDB root password"""
    try:
        saas_settings = frappe.get_single("SaaS Settings")
        
        # Set MariaDB root password (same as database password for now)
        saas_settings.mariadb_root_password = saas_settings.database_password
        saas_settings.save(ignore_permissions=True)
        
        print("SaaS Settings updated:")
        print(f"Database Password: {saas_settings.database_password}")
        print(f"MariaDB Root Password: {saas_settings.mariadb_root_password}")
        
        return True
        
    except Exception as e:
        print(f"Error updating SaaS Settings: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
