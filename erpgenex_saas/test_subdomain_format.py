"""
Test script to create a trial account with education activity using subdomain format (user.erpgenex.local)
"""

import frappe
import json


def update_saas_settings_for_subdomain():
    """Update SaaS Settings to use subdomain-based distribution"""
    print("=" * 60)
    print("تحديث إعدادات SaaS Settings لاستخدام توزيع النطاق الفرعي")
    print("=" * 60)
    
    try:
        saas_settings = frappe.get_single("SaaS Settings")
        saas_settings.site_distribution_method = "Subdomain"
        saas_settings.platform_domain = "erpgenex.local"
        saas_settings.save(ignore_permissions=True)
        
        print(f"✅ تم تحديث الإعدادات بنجاح:")
        print(f"   طريقة التوزيع: {saas_settings.site_distribution_method}")
        print(f"   نطاق المنصة: {saas_settings.platform_domain}")
        
        return True
        
    except Exception as e:
        print(f"❌ فشل تحديث الإعدادات: {str(e)}")
        print(f"التتبع: {frappe.get_traceback()}")
        return False


def test_education_subdomain():
    """Test creating a trial account with education activity using subdomain format"""
    
    print("\n" + "=" * 60)
    print("بدء اختبار إنشاء حساب تجريبي تعليمي بصيغة النطاق الفرعي")
    print("=" * 60)
    
    try:
        # First update settings
        if not update_saas_settings_for_subdomain():
            return {"success": False, "error": "Failed to update settings"
	}
        
        # Test data
        test_data = {
            "tenant_name": "مدرسة الأمل التعليمية",
            "company_email": "amal@education-school.com",
            "subdomain": "amal-school",
            "business_activity": "تعليمي",
            "server_type": "سيرفر مشترك"
        }
        
        print("\n1. إنشاء معالج اختيار النشاط...")
        print(f"   اسم المستأجر: {test_data['tenant_name']}")
        print(f"   النشاط: {test_data['business_activity']}")
        print(f"   النطاق الفرعي: {test_data['subdomain']}")
        print(f"   نوع السيرفر: {test_data['server_type']}")
        
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
        
        print("\n3. التطبيقات المحددة:")
        apps = json.loads(wizard.selected_apps)
        for app in apps:
            if isinstance(app, dict):
                print(f"   - {app.get('name', app.get('app', str(app)))}")
            else:
                print(f"   - {app}")
        
        print("\n4. إرسال المعالج لبدء التجهيز...")
        wizard.submit()
        print(f"   تم الإرسال بنجاح")
        print(f"   الحالة: {wizard.status}")
        print(f"   حالة التجهيز: {wizard.provisioning_status}")
        
        print("\n5. التحقق من المستأجر...")
        if frappe.db.exists("SaaS Tenant", test_data["tenant_name"]):
            tenant = frappe.get_doc("SaaS Tenant", test_data["tenant_name"])
            print(f"   ✅ تم إنشاء المستأجر: {tenant.name}")
            print(f"   حالة المستأجر: {tenant.status}")
            print(f"   اسم الموقع: {tenant.site_name}")
            print(f"   النطاق المتوقع: amal-school.erpgenex.local")
        else:
            print("   ❌ لم يتم العثور على المستأجر")
        
        print("\n6. التحقق من طلب التجهيز...")
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
            print(f"   نوع الطلب: {request.request_type}")
            
            # Parse execution log to see activity info
            if request.execution_log:
                try:
                    log_data = json.loads(request.execution_log)
                    print(f"\n7. تفاصيل التجهيز:")
                    print(f"   النشاط التجاري: {log_data.get('business_activity', 'N/A')}")
                    print(f"   طريقة التوزيع: {log_data.get('site_distribution_method', 'N/A')}")
                    apps_to_install = log_data.get('apps_to_install', [])
                    print(f"   عدد التطبيقات: {len(apps_to_install)}")
                except json.JSONDecodeError:
                    print("   سجل التنفيذ ليس بصيغة JSON")
        else:
            print("   ❌ لم يتم العثور على طلب تجهيز")
        
        print("\n" + "=" * 60)
        print("✅ تم اكتمال الاختبار بنجاح!")
        print("=" * 60)
        
        # Get tenant info for final summary
        tenant_info = {}
        if frappe.db.exists("SaaS Tenant", test_data["tenant_name"]):
            tenant = frappe.get_doc("SaaS Tenant", test_data["tenant_name"])
            tenant_info = {
                "site_name": tenant.site_name,
                "status": tenant.status
            }
        
        return {
            "success": True,
            "wizard_name": wizard.name,
            "tenant_name": test_data["tenant_name"],
            "status": wizard.status,
            "site_name": tenant_info.get("site_name"),
            "tenant_status": tenant_info.get("status")
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


# Run the test
if __name__ == "__main__":
    result = test_education_subdomain()
    
    print("\n" + "=" * 60)
    print("ملخص نتيجة الاختبار")
    print("=" * 60)
    if result.get("success"):
        print(f"✅ نجح الاختبار!")
        print(f"اسم المعالج: {result.get('wizard_name')}")
        print(f"اسم المستأجر: {result.get('tenant_name')}")
        print(f"الحالة: {result.get('status')}")
        print(f"اسم الموقع: {result.get('site_name')}")
        print(f"حالة المستأجر: {result.get('tenant_status')}")
    else:
        print(f"❌ فشل الاختبار: {result.get('error')}")
    print("=" * 60)
