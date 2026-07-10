"""
Execute provisioning request to complete site creation
"""

import frappe


def execute_provisioning_request(request_name):
    """Execute a provisioning request to complete site creation"""
    print("=" * 60)
    print(f"تنفيذ طلب التجهيز: {request_name}")
    print("=" * 60)
    
    try:
        from erpgenex_saas.services.provisioning import ProvisioningService
        ProvisioningService.run(request_name)
        
        print(f"✅ تم تنفيذ طلب التجهيز بنجاح")
        
        # Check tenant status
        request = frappe.get_doc("Provisioning Request", request_name)
        tenant = frappe.get_doc("SaaS Tenant", request.tenant)
        
        print(f"\nحالة المستأجر: {tenant.status}")
        print(f"اسم الموقع: {tenant.site_name}")
        print(f"رقم البورت: {tenant.port_number}")
        
        return True
        
    except Exception as e:
        print(f"❌ فشل تنفيذ طلب التجهيز: {str(e)}")
        print(f"التتبع: {frappe.get_traceback()}")
        return False


if __name__ == "__main__":
    # Execute the provisioning request from the test
    execute_provisioning_request("m9s0lib1ma")
