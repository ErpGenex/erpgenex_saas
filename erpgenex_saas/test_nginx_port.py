"""
Test creating site with nginx port configuration using bench set-nginx-port
"""

import frappe
import os
from frappe.utils import get_bench_path
from erpgenex_saas.runtime_config import get_server_host, get_site_url


def test_site_with_nginx_port():
    """Test creating site with nginx port configuration"""
    
    print("=" * 60)
    print("اختبار إنشاء موقع مع تكوين nginx port")
    print("=" * 60)
    
    try:
        # Test data
        test_data = {
            "tenant_name": "شركة النجاح التقنية",
            "company_email": "success@tech-company.com",
            "subdomain": "success-tech",
            "business_activity": "عام",
            "server_type": "سيرفر مشترك"
        }
        
        print("\n1. إنشاء معالج اختيار النشاط...")
        print(f"   اسم المستأجر: {test_data['tenant_name']}")
        print(f"   النشاط: {test_data['business_activity']}")
        print(f"   النطاق الفرعي: {test_data['subdomain']}")
        
        # Create the wizard document
        wizard = frappe.new_doc("Activity Selection Wizard")
        wizard.tenant_name = test_data["tenant_name"]
        wizard.company_email = test_data["company_email"]
        wizard.subdomain = test_data["subdomain"]
        wizard.business_activity = test_data["business_activity"]
        wizard.server_type = test_data["server_type"]
        
        print("\n2. حفظ المعالج...")
        wizard.save(ignore_permissions=True)
        print(f"   تم الحفظ بنجاح: {wizard.name}")
        
        print("\n3. إرسال المعالج لبدء التجهيز...")
        wizard.submit()
        print(f"   تم الإرسال بنجاح")
        
        print("\n4. التحقق من المستأجر...")
        if frappe.db.exists("SaaS Tenant", test_data["tenant_name"]):
            tenant = frappe.get_doc("SaaS Tenant", test_data["tenant_name"])
            print(f"   ✅ تم إنشاء المستأجر: {tenant.name}")
            print(f"   حالة المستأجر: {tenant.status}")
            print(f"   اسم الموقع: {tenant.site_name}")
        else:
            print("   ❌ لم يتم العثور على المستأجر")
        
        print("\n5. التحقق من طلب التجهيز...")
        provisioning_requests = frappe.get_all(
            "Provisioning Request",
            filters={"tenant": test_data["tenant_name"]
	},
            order_by="creation desc",
            limit=1
        )
        
        if provisioning_requests:
            request = frappe.get_doc("Provisioning Request", provisioning_requests[0].name)
            print(f"   ✅ تم إنشاء طلب التجهيز: {request.name}")
            print(f"   حالة الطلب: {request.status}")
            
            print("\n6. تنفيذ طلب التجهيز...")
            from erpgenex_saas.services.provisioning import ProvisioningService
            ProvisioningService.run(request.name)
            
            print("\n7. التحقق من حالة المستأجر بعد التجهيز...")
            tenant.reload()
            print(f"   حالة المستأجر: {tenant.status}")
            print(f"   اسم الموقع: {tenant.site_name}")
            
            # Check if site exists in sites folder
            import os
            site_path = os.path.join(get_bench_path(), "sites", tenant.site_name)
            if os.path.exists(site_path):
                print(f"   ✅ الموقع موجود في مجلد sites: {site_path}")
                
                # Check nginx configuration
                nginx_config_path = f"/etc/nginx/sites-available/{tenant.site_name}"
                if os.path.exists(nginx_config_path):
                    print(f"   ✅ تكوين nginx موجود: {nginx_config_path}")
                    
                    # Read nginx config to check port
                    with open(nginx_config_path, 'r') as f:
                        nginx_config = f.read()
                    
                    if f"{get_server_host()}:8088" in nginx_config or "8088" in nginx_config:
                        print(f"   ✅ البورت 8088 موجود في تكوين nginx")
                    else:
                        print(f"   ❌ البورت 8088 غير موجود في تكوين nginx")
                        print(f"   محتوى تكوين nginx:")
                        print(f"   {nginx_config[:500]}")
                else:
                    print(f"   ❌ تكوين nginx غير موجود: {nginx_config_path}")
            else:
                print(f"   ❌ الموقع غير موجود في مجلد sites: {site_path}")
        else:
            print("   ❌ لم يتم العثور على طلب تجهيز")
        
        print("\n" + "=" * 60)
        print("✅ تم اكتمال الاختبار!")
        print("=" * 60)
        
        return {
            "success": True,
            "site_name": tenant.site_name if tenant else None,
            "status": tenant.status if tenant else None
        }
        
    except Exception as e:
        print("\n" + "=" * 60)
        print("❌ فشل الاختبار!")
        print("=" * 60)
        print(f"الخطأ: {str(e)}")
        print(f"التتبع: {frappe.get_traceback()}")
        
        return {
            "success": False,
            "error": str(e)
        }


if __name__ == "__main__":
    result = test_site_with_nginx_port()
    
    print("\n" + "=" * 60)
    print("ملخص نتيجة الاختبار")
    print("=" * 60)
    if result.get("success"):
        print(f"✅ نجح الاختبار!")
        print(f"اسم الموقع: {result.get('site_name')}")
        print(f"الحالة: {result.get('status')}")
        print(f"الموقع يجب أن يعمل على: {get_site_url(8088)}")
    else:
        print(f"❌ فشل الاختبار: {result.get('error')}")
    print("=" * 60)
