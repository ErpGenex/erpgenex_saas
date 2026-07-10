import frappe

def check_databases():
    """Check for orphaned databases"""
    try:
        # Get all databases
        result = frappe.db.sql("SHOW DATABASES")
        
        print("All databases:")
        for db in result:
            print(f"  - {db[0]}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
