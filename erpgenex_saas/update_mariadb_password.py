import frappe

def update_mariadb_password():
    """Update MariaDB root password in SaaS Settings"""
    try:
        saas_settings = frappe.get_single("SaaS Settings")
        
        # Set the correct MariaDB root password
        saas_settings.mariadb_root_password = "Microhard2610"
        saas_settings.save(ignore_permissions=True)
        
        print("✅ MariaDB root password updated to: Microhard2610")
        print(f"Current value: {saas_settings.mariadb_root_password}")
        return True
            
    except Exception as e:
        print(f"Error updating MariaDB root password: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    update_mariadb_password()
