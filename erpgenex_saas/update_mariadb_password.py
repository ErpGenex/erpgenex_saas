import os
import secrets

import frappe

def update_mariadb_password():
    """Update MariaDB root password in SaaS Settings"""
    try:
        saas_settings = frappe.get_single("SaaS Settings")
        
        # Set the MariaDB root password from env or generate a fresh one
        saas_settings.mariadb_root_password = os.environ.get("ERPGENEX_SAAS_MARIADB_ROOT_PASSWORD") or secrets.token_urlsafe(16)
        saas_settings.save(ignore_permissions=True)
        
        print("✅ MariaDB root password updated")
        print(f"Current value: {saas_settings.mariadb_root_password}")
        return True
            
    except Exception as e:
        print(f"Error updating MariaDB root password: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    update_mariadb_password()
