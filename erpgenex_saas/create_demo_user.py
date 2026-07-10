import frappe

def create_demo_user():
    """Create a demo user for testing"""
    try:
        # Create demo user
        user = frappe.get_doc({
            "doctype": "User",
            "email": "demo@erpgenex.com",
            "first_name": "Demo",
            "last_name": "User",
            "enabled": 1,
            "send_welcome_email": 0
        })
        user.insert()
        
        # Set password
        user.new_password = "Demo@123456"
        user.save()
        
        print(f"Demo user created: {user.email}")
        print(f"Password: Demo@123456")
        
        return user.name
    except Exception as e:
        print(f"Error creating demo user: {str(e)}")
        return None
