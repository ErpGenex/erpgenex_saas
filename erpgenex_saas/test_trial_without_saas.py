"""
Test creating new trial account without erpgenex_saas app
erpgenex_saas should only be available on main site, not on user sites
"""

import frappe
import json


def test_trial_account_without_saas_app():
    """Test creating trial account without erpgenex_saas app"""
    
    print("=" * 60)
    print("اختبار إنشاء حساب تجريبي بدون تطبيق erpgenex_saas")
    print("=" * 60)
    
    try:
        # Test data
        test_data = {
            "tenant_name": "شركة التقدم الصناعية",
            "company_email": "progress@industrial-company.com",
            "subdomain": "progress-industrial",
            "business_activity": "مقاولات",
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
        
        print("\n3. التطبيقات المحددة:")
        apps = json.loads(wizard.selected_apps)
        print(f"   عدد التطبيقات: {len(apps)}")
        for app in apps:
            if isinstance(app, dict):
                print(f"   - {app.get('name', app.get('app', str(app)))}")
            else:
                print(f"   - {app}")
        
        # Check if erpgenex_saas is in the list
        has_saas_app = any(
            (app if isinstance(app, str) else app.get('app', '')) == 'erpgenex_saas'
            for app in apps
        )
        
        if has_saas_app:
            print("\n   ❌ خطأ: erpgenex_saas موجود في قائمة التطبيقات!")
            return {"success": False, "error": "erpgenex_saas should not be in apps list"}
        else:
            print("\n   ✅ صحيح: erpgenex_saas غير موجود في قائمة التطبيقات")
        
        print("\n4. إرسال المعالج لبدء التجهيز...")
        wizard.submit()
        print(f"   تم الإرسال بنجاح")
        
        print("\n5. التحقق من المستأجر...")
        if frappe.db.exists("SaaS Tenant", test_data["tenant_name"]):
            tenant = frappe.get_doc("SaaS Tenant", test_data["tenant_name"])
            print(f"   ✅ تم إنشاء المستأجر: {tenant.name}")
            print(f"   حالة المستأجر: {tenant.status}")
            print(f"   اسم الموقع: {tenant.site_name}")
        else:
            print("   ❌ لم يتم العثور على المستأجر")
        
        print("\n6. التحقق من طلب التجهيز...")
        provisioning_requests = frappe.get_all(
            "Provisioning Request",
            filters={"tenant": test_data["tenant_name"]},
            order_by="creation desc",
            limit=1
        )
        
        if provisioning_requests:
            request = frappe.get_doc("Provisioning Request", provisioning_requests[0].name)
            print(f"   ✅ تم إنشاء طلب التجهيز: {request.name}")
            print(f"   حالة الطلب: {request.status}")
            
            # Check execution log for apps
            if request.execution_log:
                try:
                    log_data = json.loads(request.execution_log)
                    apps_in_log = log_data.get('apps_to_install', [])
                    print(f"\n7. التطبيقات في سجل التنفيذ:")
                    for app in apps_in_log:
                        if isinstance(app, dict):
                            print(f"   - {app.get('name', app.get('app', str(app)))}")
                        else:
                            print(f"   - {app}")
                    
                    # Check if erpgenex_saas is in execution log
                    has_saas_in_log = any(
                        (app if isinstance(app, str) else app.get('app', '')) == 'erpgenex_saas'
                        for app in apps_in_log
                    )
                    
                    if has_saas_in_log:
                        print("\n   ❌ خطأ: erpgenex_saas موجود في سجل التنفيذ!")
                    else:
                        print("\n   ✅ صحيح: erpgenex_saas غير موجود في سجل التنفيذ")
                except json.JSONDecodeError:
                    print("   سجل التنفيذ ليس بصيغة JSON")
            
            print("\n8. تنفيذ طلب التجهيز...")
            from erpgenex_saas.services.provisioning import ProvisioningService
            ProvisioningService.run(request.name)
            
            print("\n9. التحقق من حالة المستأجر بعد التجهيز...")
            tenant.reload()
            print(f"   حالة المستأجر: {tenant.status}")
            print(f"   اسم الموقع: {tenant.site_name}")
            
            # Check if site exists in sites folder
            import os
            site_path = f"/home/frappeuser/frappe-bench/sites/{tenant.site_name}"
            if os.path.exists(site_path):
                print(f"   ✅ الموقع موجود في مجلد sites: {site_path}")
                
                # Check installed apps in site
                apps_txt_path = os.path.join(site_path, "apps.txt")
                if os.path.exists(apps_txt_path):
                    with open(apps_txt_path, 'r') as f:
                        installed_apps = f.read()
                    print(f"\n10. التطبيقات المثبتة في الموقع:")
                    print(f"   {installed_apps}")
                    
                    if 'erpgenex_saas' in installed_apps:
                        print("\n   ❌ خطأ: erpgenex_saas مثبت في الموقع!")
                    else:
                        print("\n   ✅ صحيح: erpgenex_saas غير مثبت في الموقع")
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
    result = test_trial_account_without_saas_app()
    
    print("\n" + "=" * 60)
    print("ملخص نتيجة الاختبار")
    print("=" * 60)
    if result.get("success"):
        print(f"✅ نجح الاختبار!")
        print(f"اسم الموقع: {result.get('site_name')}")
        print(f"الحالة: {result.get('status')}")
        print(f"✅ erpgenex_saas غير مثبت للمستخدمين الجدد")
    else:
        print(f"❌ فشل الاختبار: {result.get('error')}")
    print("=" * 60)
