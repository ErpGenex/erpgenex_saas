import frappe

def check_provisioning_status():
    """Check the status of the provisioning request"""
    try:
        # Get the latest provisioning request
        request = frappe.get_last_doc("Provisioning Request")
        
        print(f"Provisioning Request: {request.name}")
        print(f"Status: {request.status}")
        print(f"Last Message: {request.last_message}")
        print(f"\nExecution Log:\n{request.execution_log}")
        
        # Get tenant details
        tenant = frappe.get_doc("SaaS Tenant", request.tenant)
        print(f"\nTenant Details:")
        print(f"Name: {tenant.tenant_name}")
        print(f"Site Name: {tenant.site_name}")
        print(f"Status: {tenant.status}")
        print(f"Port: {tenant.port_number}")
        print(f"Site URL: {tenant.site_url}")
        print(f"Admin Username: {tenant.admin_username}")
        print(f"Has Admin Password: {bool(tenant.admin_password)}")
        
        return request.status
        
    except Exception as e:
        print(f"Error checking provisioning status: {str(e)}")
        import traceback
        traceback.print_exc()
        return None
