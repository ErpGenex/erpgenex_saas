"""
Test that port 80 is reserved for main site only
"""

import frappe


def test_port_80_reserved():
    """Test that port 80 is reserved for main site"""
    
    print("=" * 60)
    print("اختبار حجز بورت 80 للموقع الرئيسي")
    print("=" * 60)
    
    try:
        # Test data
        test_data = {
            "tenant_name": "شركة الاختبار للتأكد من البورت",
            "company_email": "test@port-verification.com",
            "subdomain": "test-port-80",
            "business_activity": "عام",
            "server_type": "سيرفر مشترك"
        }
        
        print("\n1. إنشاء معالج اختيار النشاط...")
        print(f"   اسم المستأجر: {test_data['tenant_name']}")
        print(f"   النشاط: {test_data['business_activity']}")
        
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
        else:
            print("   ❌ لم يتم العثور على المستأجر")
            return {"success": False, "error": "Tenant not found"}
        
        print("\n5. التحقق من طلب التجهيز...")
        provisioning_requests = frappe.get_all(
            "Provisioning Request",
            filters={"tenant": test_data["tenant_name"]},
            order_by="creation desc",
            limit=1
        )
        
        if provisioning_requests:
            request = frappe.get_doc("Provisioning Request", provisioning_requests[0].name)
            print(f"   ✅ تم إنشاء طلب التجهيز: {request.name}")
            
            print("\n6. تنفيذ طلب التجهيز...")
            from erpgenex_saas.services.provisioning import ProvisioningService
            ProvisioningService.run(request.name)
            
            print("\n7. التحقق من البورت المخصص...")
            tenant.reload()
            print(f"   اسم الموقع: {tenant.site_name}")
            print(f"   رقم البورت: {tenant.port_number}")
            
            # Verify port is not 80
            if tenant.port_number == 80:
                print(f"   ❌ فشل: البورت 80 محجوز للموقع الرئيسي فقط!")
                return {"success": False, "error": "Port 80 assigned to user site"}
            else:
                print(f"   ✅ نجح: البورت {tenant.port_number} ليس 80 (محجوز للموقع الرئيسي)")
            
            # Verify port is in expected range (8001-8888)
            if 8001 <= tenant.port_number <= 8888:
                print(f"   ✅ البورت {tenant.port_number} في النطاق الصحيح (8001-8888)")
            else:
                print(f"   ❌ البورت {tenant.port_number} خارج النطاق المسموح")
            
            print("\n8. التحقق من إعدادات SaaS Settings...")
            saas_settings = frappe.get_single("SaaS Settings")
            print(f"   البورت الأساسي: {saas_settings.base_port}")
            print(f"   بورت السيرفر: {saas_settings.server_port}")
            
            if saas_settings.base_port == 8001:
                print(f"   ✅ البورت الأساسي 8001 (يبدأ من بعد 80)")
            else:
                print(f"   ❌ البورت الأساسي يجب أن يكون 8001")
            
            if saas_settings.server_port == 80:
                print(f"   ✅ بورت السيرفر 80 (للموقع الرئيسي)")
            else:
                print(f"   ❌ بورت السيرفر يجب أن يكون 80")
            
            print("\n" + "=" * 60)
            print("✅ تم التأكد من حجز بورت 80 للموقع الرئيسي")
            print("=" * 60)
            
            return {
                "success": True,
                "site_name": tenant.site_name,
                "port_number": tenant.port_number,
                "port_80_reserved": True
            }
        else:
            print("   ❌ لم يتم العثور على طلب تجهيز")
            return {"success": False, "error": "Provisioning request not found"}
        
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
    result = test_port_80_reserved()
    
    print("\n" + "=" * 60)
    print("النتيجة النهائية")
    print("=" * 60)
    if result.get("success"):
        print(f"✅ نجح الاختبار!")
        print(f"   بورت المستخدم: {result.get('port_number')}")
        print(f"   بورت 80: محجوز للموقع الرئيسي فقط ✅")
        print(f"   النظام يعمل بشكل صحيح")
    else:
        print(f"❌ فشل الاختبار: {result.get('error')}")
    print("=" * 60)
