import os
import secrets

import frappe

def set_passwords_with_correct_table():
    """Set passwords using correct table name with backticks"""
    try:
        # Set passwords using db.set_value (this should work with the correct DocType)
        password = os.environ.get("ERPGENEX_SAAS_DB_PASSWORD") or os.environ.get("ERPGENEX_SAAS_MARIADB_ROOT_PASSWORD") or secrets.token_urlsafe(16)
        frappe.db.set_value("SaaS Settings", "SaaS Settings", "database_password", password)
        frappe.db.set_value("SaaS Settings", "SaaS Settings", "mariadb_root_password", password)
        frappe.db.commit()
        
        print("Passwords set using db.set_value")
        
        # Get the actual values using SQL with correct table name (note the space)
        result = frappe.db.sql("SELECT database_password, mariadb_root_password FROM `tabSaaS Settings`", as_dict=True)
        
        if result:
            print(f"Database Password: {result[0]['database_password']}")
            print(f"MariaDB Root Password: {result[0]['mariadb_root_password']}")
            
            # Verify
            if result[0]['database_password'] == password:
                print("✅ Database Password is correct")
            else:
                print(f"❌ Database Password is incorrect: {result[0]['database_password']}")
                
            if result[0]['mariadb_root_password'] == password:
                print("✅ MariaDB Root Password is correct")
            else:
                print(f"❌ MariaDB Root Password is incorrect: {result[0]['mariadb_root_password']}")
        
        return True
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
