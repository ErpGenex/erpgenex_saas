import os
import secrets

import frappe

def set_passwords_directly():
    """Set passwords directly using db.set_value"""
    try:
        # Set passwords using db.set_value
        password = os.environ.get("ERPGENEX_SAAS_DB_PASSWORD") or os.environ.get("ERPGENEX_SAAS_MARIADB_ROOT_PASSWORD") or secrets.token_urlsafe(16)
        frappe.db.set_value("SaaS Settings", "SaaS Settings", "database_password", password)
        frappe.db.set_value("SaaS Settings", "SaaS Settings", "mariadb_root_password", password)
        frappe.db.commit()
        
        print("Passwords set using db.set_value")
        
        # Get the actual values using SQL to avoid masking
        result = frappe.db.sql("SELECT database_password, mariadb_root_password FROM `tabSaaS Settings`", as_dict=True)
        
        if result:
            print(f"Database Password: {result[0]['database_password']}")
            print(f"MariaDB Root Password: {result[0]['mariadb_root_password']}")
        
        return True
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
