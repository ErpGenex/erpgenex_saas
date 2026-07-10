"""
Test script to create a trial account with education activity
Run this script to test the Activity Selection Wizard
"""

import frappe
import json


def test_education_activity_trial():
    """Test creating a trial account with education activity"""
    
    print("=" * 60)
    print("بدء اختبار إنشاء حساب تجريبي بنشاط تعليمي")
    print("=" * 60)
    
    try:
        # Test data
        test_data = {
            "tenant_name": "مدرسة التجربة التعليمية",
            "company_email": "test@education-school.com",
            "subdomain": "education-test",
            "business_activity": "تعليمي",
            "server_type": "سيرفر مشترك"
        }
        
        print("\n1. إنشاء معالج اختيار النشاط...")
        print(f"   اسم المستأجر: {test_data['tenant_name']}")
        print(f"   النشاط: {test_data['business_activity']}")
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
            print(f"   تم إنشاء المستأجر: {tenant.name}")
            print(f"   حالة المستأجر: {tenant.status}")
            print(f"   اسم الموقع: {tenant.site_name}")
        else:
            print("   لم يتم العثور على المستأجر")
        
        print("\n6. التحقق من طلب التجهيز...")
        provisioning_requests = frappe.get_all(
            "Provisioning Request",
            filters={"tenant": test_data["tenant_name"]},
            order_by="creation desc",
            limit=1
        )
        
        if provisioning_requests:
            request = frappe.get_doc("Provisioning Request", provisioning_requests[0].name)
            print(f"   تم إنشاء طلب التجهيز: {request.name}")
            print(f"   حالة الطلب: {request.status}")
            print(f"   نوع الطلب: {request.request_type}")
            
            # Parse execution log to see activity info
            if request.execution_log:
                try:
                    log_data = json.loads(request.execution_log)
                    print(f"\n7. تفاصيل التجهيز:")
                    print(f"   النشاط التجاري: {log_data.get('business_activity', 'N/A')}")
                    apps_to_install = log_data.get('apps_to_install', [])
                    print(f"   عدد التطبيقات: {len(apps_to_install)}")
                except json.JSONDecodeError:
                    print("   سجل التنفيذ ليس بصيغة JSON")
        else:
            print("   لم يتم العثور على طلب تجهيز")
        
        print("\n" + "=" * 60)
        print("✅ تم اكتمال الاختبار بنجاح!")
        print("=" * 60)
        
        return {
            "success": True,
            "wizard_name": wizard.name,
            "tenant_name": test_data["tenant_name"],
            "status": wizard.status
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


def test_dedicated_server_education():
    """Test creating a trial account with education activity on dedicated server"""
    
    print("\n" + "=" * 60)
    print("بدء اختبار إنشاء حساب تجريبي بنشاط تعليمي على سيرفر مخصص")
    print("=" * 60)
    
    try:
        # Test data for dedicated server
        test_data = {
            "tenant_name": "مدرسة المستقبل التعليمية",
            "company_email": "future@education-school.com",
            "subdomain": "future-education",
            "business_activity": "تعليمي",
            "server_type": "سيرفر مخصص",
            "server_ip": "192.168.1.100",
            "domain_name": "future-education.com",
            "enable_ssl": True,
            "ssl_certificate": "-----BEGIN CERTIFICATE-----\nTEST CERTIFICATE\n-----END CERTIFICATE-----",
            "ssl_key": "-----BEGIN PRIVATE KEY-----\nTEST PRIVATE KEY\n-----END PRIVATE KEY-----"
        }
        
        print("\n1. إنشاء معالج اختيار النشاط...")
        print(f"   اسم المستأجر: {test_data['tenant_name']}")
        print(f"   النشاط: {test_data['business_activity']}")
        print(f"   نوع السيرفر: {test_data['server_type']}")
        print(f"   عنوان IP: {test_data['server_ip']}")
        print(f"   النطاق: {test_data['domain_name']}")
        print(f"   SSL: {test_data['enable_ssl']}")
        
        # Create the wizard document
        wizard = frappe.new_doc("Activity Selection Wizard")
        wizard.tenant_name = test_data["tenant_name"]
        wizard.company_email = test_data["company_email"]
        wizard.subdomain = test_data["subdomain"]
        wizard.business_activity = test_data["business_activity"]
        wizard.server_type = test_data["server_type"]
        wizard.server_ip = test_data["server_ip"]
        wizard.domain_name = test_data["domain_name"]
        wizard.enable_ssl = test_data["enable_ssl"]
        wizard.ssl_certificate = test_data["ssl_certificate"]
        wizard.ssl_key = test_data["ssl_key"]
        
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
            print(f"   تم إنشاء المستأجر: {tenant.name}")
            print(f"   حالة المستأجر: {tenant.status}")
            print(f"   اسم الموقع: {tenant.site_name}")
            print(f"   النطاق المخصص: {tenant.custom_domain}")
        else:
            print("   لم يتم العثور على المستأجر")
        
        print("\n" + "=" * 60)
        print("✅ تم اكتمال الاختبار بنجاح!")
        print("=" * 60)
        
        return {
            "success": True,
            "wizard_name": wizard.name,
            "tenant_name": test_data["tenant_name"],
            "status": wizard.status
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


# Run the tests
if __name__ == "__main__":
    # Test 1: Shared server with education activity
    result1 = test_education_activity_trial()
    
    # Test 2: Dedicated server with education activity
    result2 = test_dedicated_server_education()
    
    print("\n" + "=" * 60)
    print("ملخص نتائج الاختبار")
    print("=" * 60)
    print(f"الاختبار 1 (سيرفر مشترك): {'✅ نجح' if result1.get('success') else '❌ فشل'}")
    print(f"الاختبار 2 (سيرفر مخصص): {'✅ نجح' if result2.get('success') else '❌ فشل'}")
    print("=" * 60)
