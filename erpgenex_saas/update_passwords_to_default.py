import os
import secrets

import frappe

def update_passwords_to_default():
    """Update passwords to a generated shared value."""
    try:
        saas_settings = frappe.get_single("SaaS Settings")
        
        password = os.environ.get("ERPGENEX_SAAS_DB_PASSWORD") or os.environ.get("ERPGENEX_SAAS_MARIADB_ROOT_PASSWORD") or secrets.token_urlsafe(16)
        saas_settings.database_password = password
        saas_settings.mariadb_root_password = password
        saas_settings.save(ignore_permissions=True)
        
        print("Passwords updated:")
        print(f"Database Password: {saas_settings.database_password}")
        print(f"MariaDB Root Password: {saas_settings.mariadb_root_password}")
        
        return True
        
    except Exception as e:
        print(f"Error updating passwords: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
