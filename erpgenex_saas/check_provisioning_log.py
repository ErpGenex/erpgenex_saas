import frappe

def check_provisioning_log():
    """Check the provisioning request execution log"""
    try:
        # Get the latest provisioning request
        request = frappe.get_last_doc("Provisioning Request")
        
        print(f"Provisioning Request: {request.name}")
        print(f"Status: {request.status}")
        print(f"Last Message: {request.last_message}")
        print(f"\nExecution Log:")
        print("=" * 60)
        print(request.execution_log)
        print("=" * 60)
        
        return request
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None
