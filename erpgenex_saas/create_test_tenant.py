import frappe

def create_test_tenant():
    """Create a test tenant with a different name"""
    try:
        # Generate a unique name
        import random
        import string
        suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        company_name = f"Test Company {suffix}"
        
        print(f"Creating tenant: {company_name}")
        
        # Create tenant
        tenant = frappe.get_doc({
            "doctype": "SaaS Tenant",
            "tenant_name": company_name,
            "company_email": f"test{suffix}@erpgenex.com",
            "subdomain": f"test-{suffix}",
            "status": "Draft"
        })
        
        tenant.insert()
        
        # Create provisioning request
        request = frappe.get_doc({
            "doctype": "Provisioning Request",
            "tenant": tenant.name,
            "request_type": "Initial Provisioning",
            "requested_by": "Administrator",
            "status": "Queued"
        })
        
        request.insert()
        
        print(f"Tenant created: {tenant.name}")
        print(f"Provisioning Request created: {request.name}")
        
        return tenant.name, request.name
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None, None
