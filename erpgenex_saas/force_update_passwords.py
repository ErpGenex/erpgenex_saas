import os
import secrets

import frappe

def force_update_passwords():
    """Force update passwords using SQL"""
    try:
        # Update using SQL to bypass any masking
        password = os.environ.get("ERPGENEX_SAAS_DB_PASSWORD") or os.environ.get("ERPGENEX_SAAS_MARIADB_ROOT_PASSWORD") or secrets.token_urlsafe(16)
        frappe.db.sql("UPDATE `tabSaaS Settings` SET database_password = %s", (password,))
        frappe.db.sql("UPDATE `tabSaaS Settings` SET mariadb_root_password = %s", (password,))
        frappe.db.commit()
        
        print("Passwords updated using SQL")
        
        # Verify
        result = frappe.db.get_value("SaaS Settings", "SaaS Settings", ["database_password", "mariadb_root_password"], as_dict=True)
        
        print(f"Database Password: {result['database_password']}")
        print(f"MariaDB Root Password: {result['mariadb_root_password']}")
        
        return True
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
