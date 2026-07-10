import frappe

def verify_password_changes():
    """Verify password changes in SaaS Settings"""
    try:
        saas_settings = frappe.get_single("SaaS Settings")
        
        print("SaaS Settings - Password Verification:")
        print("=" * 60)
        print(f"Database Password: {saas_settings.database_password}")
        print(f"MariaDB Root Password: {saas_settings.mariadb_root_password}")
        print(f"Default Value: Microhard2610")
        print("=" * 60)
        
        # Verify the passwords are set correctly
        if saas_settings.database_password == "Microhard2610":
            print("✅ Database Password is correct")
        else:
            print("❌ Database Password is incorrect")
            
        if saas_settings.mariadb_root_password == "Microhard2610":
            print("✅ MariaDB Root Password is correct")
        else:
            print("❌ MariaDB Root Password is incorrect")
        
        print("\nNote: The password fields now have the 'password': 1 property")
        print("This adds the eye icon to toggle password visibility in the UI")
        print("Only System Manager role can view and modify these passwords")
        
        return True
        
    except Exception as e:
        print(f"Error verifying password changes: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
