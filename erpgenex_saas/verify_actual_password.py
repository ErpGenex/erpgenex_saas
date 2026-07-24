import frappe

def verify_actual_password():
    """Verify actual password values in database"""
    try:
        # Get the actual value from database
        result = frappe.db.get_value("SaaS Settings", "SaaS Settings", ["database_password", "mariadb_root_password"], as_dict=True)
        
        print("Actual Password Values from Database:")
        print("=" * 60)
        print(f"Database Password: {result['database_password']}")
        print(f"MariaDB Root Password: {result['mariadb_root_password']}")
        print("=" * 60)
        
        # Verify
        if result['database_password'] == frappe.get_single("SaaS Settings").database_password:
            print("✅ Database Password is correct")
        else:
            print(f"❌ Database Password is incorrect: {result['database_password']}")
            
        if result['mariadb_root_password'] == frappe.get_single("SaaS Settings").mariadb_root_password:
            print("✅ MariaDB Root Password is correct")
        else:
            print(f"❌ MariaDB Root Password is incorrect: {result['mariadb_root_password']}")
        
        return result
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None
