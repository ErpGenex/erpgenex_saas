import frappe

def cleanup_database():
    """Clean up database and user for erpgenex.local_port_8002"""
    try:
        db_name = "erpgenex_local_port_8002"
        db_name_escaped = db_name.replace('-', '_').replace('.', '_')
        
        print(f"Cleaning up database: {db_name_escaped}")
        
        # Drop database
        try:
            frappe.db.sql(f"DROP DATABASE IF EXISTS `{db_name_escaped}`")
            print(f"Dropped database: {db_name_escaped}")
        except Exception as e:
            print(f"Failed to drop database: {str(e)}")
        
        # Drop user
        try:
            frappe.db.sql(f"DROP USER IF EXISTS `{db_name_escaped}`@`%`")
            frappe.db.sql(f"DROP USER IF EXISTS `{db_name_escaped}`@`localhost`")
            print(f"Dropped user: {db_name_escaped}")
        except Exception as e:
            print(f"Failed to drop user: {str(e)}")
        
        # Flush privileges
        try:
            frappe.db.sql("FLUSH PRIVILEGES")
            print("Flushed privileges")
        except Exception as e:
            print(f"Failed to flush privileges: {str(e)}")
        
        print("Cleanup completed")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
