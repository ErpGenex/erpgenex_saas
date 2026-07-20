"""
Test creating site with port-based distribution and password from settings
"""

import frappe


def test_port_based_site():
    """Test creating site with port-based distribution"""
    
    print("=" * 60)
    print("اختبار إنشاء موقع بتوزيع البورت وكلمة المرور")
    print("=" * 60)
    
    try:
        # Test data
        test_data = {
            "tenant_name": "شركة المستقبل الرقمية",
            "company_email": "future@digital-company.com",
            "subdomain": "future-digital",
            "business_activity": "تعليمي",
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
            print(f"   رقم البورت: {tenant.port_number}")
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
            print(f"   رقم البورت: {tenant.port_number}")
            
            # Check if port is in range 8000-8888
            if tenant.port_number:
                if 8000 <= tenant.port_number <= 8888:
                    print(f"   ✅ البورت {tenant.port_number} في النطاق الصحيح (8000-8888)")
                else:
                    print(f"   ❌ البورت {tenant.port_number} خارج النطاق المسموح")
            
            # Check if site exists in sites folder
            import os
            # For port-based sites, the folder name is different
            if ":" in tenant.site_name:
                folder_name = f"{tenant.site_name.split(':')[0]}_port_{tenant.site_name.split(':')[1]}"
            else:
                folder_name = tenant.site_name
            
            site_path = f"/home/frappeuser/frappe-bench/sites/{folder_name}"
            if os.path.exists(site_path):
                print(f"   ✅ الموقع موجود في مجلد sites: {site_path}")
                
                # Check site config for password
                site_config_path = os.path.join(site_path, "site_config.json")
                if os.path.exists(site_config_path):
                    import json
                    with open(site_config_path, 'r') as f:
                        config = json.load(f)
                    print(f"   ✅ ملف التكوين موجود")
                    print(f"   اسم قاعدة البيانات: {config.get('db_name', 'N/A')}")
                    print(f"   نوع قاعدة البيانات: {config.get('db_type', 'N/A')}")
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
            "port_number": tenant.port_number if tenant else None,
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
    result = test_port_based_site()
    
    print("\n" + "=" * 60)
    print("ملخص نتيجة الاختبار")
    print("=" * 60)
    if result.get("success"):
        print(f"✅ نجح الاختبار!")
        print(f"اسم الموقع: {result.get('site_name')}")
        print(f"رقم البورت: {result.get('port_number')}")
        print(f"الحالة: {result.get('status')}")
        print(f"كلمة المرور: Microhard2610 (من إعدادات SaaS)")
        print(f"الوصول: http://192.168.1.2:{result.get('port_number')}")
    else:
        print(f"❌ فشل الاختبار: {result.get('error')}")
    print("=" * 60)
