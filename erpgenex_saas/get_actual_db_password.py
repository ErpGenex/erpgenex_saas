import frappe

def get_actual_db_password():
    """Get the actual database password from SaaS Settings"""
    try:
        saas_settings = frappe.get_single("SaaS Settings")
        password = saas_settings.database_password
        
        print(f"Actual DB password: {password}")
        print(f"Length: {len(password)}")
        
        return password
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return None
