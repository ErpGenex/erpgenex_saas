import frappe

def update_passwords_to_default():
    """Update passwords to Microhard2610"""
    try:
        saas_settings = frappe.get_single("SaaS Settings")
        
        # Update passwords to Microhard2610
        saas_settings.database_password = "Microhard2610"
        saas_settings.mariadb_root_password = "Microhard2610"
        saas_settings.save(ignore_permissions=True)
        
        print("Passwords updated to Microhard2610:")
        print(f"Database Password: {saas_settings.database_password}")
        print(f"MariaDB Root Password: {saas_settings.mariadb_root_password}")
        
        return True
        
    except Exception as e:
        print(f"Error updating passwords: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
