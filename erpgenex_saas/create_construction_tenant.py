import frappe
import json

def create_construction_tenant():
    """Create a construction tenant and provision a site"""
    try:
        # Create SaaS Tenant
        tenant = frappe.get_doc({
            "doctype": "SaaS Tenant",
            "tenant_name": "شركة المقاولات التجريبية",
            "subdomain": "construction-demo",
            "email": "demo@erpgenex.com",
            "company_email": "demo@erpgenex.com",
            "phone": "+966500000000",
            "status": "Draft"
        })
        tenant.insert()
        
        print(f"Tenant created: {tenant.name}")
        
        # Create Provisioning Request
        provisioning_config = {
            "business_activity": "مقاولات",
            "server_type": "سيرفر مشترك",
            "server_config": {
	},
            "apps_to_install": ["omnexa_construction"]
        }
        
        request = frappe.get_doc({
            "doctype": "Provisioning Request",
            "tenant": tenant.name,
            "status": "Queued",
            "execution_log": json.dumps(provisioning_config)
        })
        request.insert()
        
        print(f"Provisioning Request created: {request.name}")
        
        # Enqueue the provisioning request
        from erpgenex_saas.services.provisioning import ProvisioningService
        ProvisioningService.enqueue_request(request.name)
        
        print(f"Provisioning request enqueued for processing")
        print(f"Tenant: {tenant.name}")
        print(f"Request: {request.name}")
        
        return tenant.name, request.name
        
    except Exception as e:
        print(f"Error creating construction tenant: {str(e)}")
        import traceback
        traceback.print_exc()
        return None, None
