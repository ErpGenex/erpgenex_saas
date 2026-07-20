"""
Create a new production-ready site with full functionality test
"""

import frappe
import os


def create_production_site():
    """Create a new production-ready site for testing"""
    
    print("=" * 60)
    print("إنشاء موقع جديد جاهز للعمل")
    print("=" * 60)
    
    try:
        # Test data for production site
        test_data = {
            "tenant_name": "شركة النجاح المتكاملة",
            "company_email": "success@integrated-company.com",
            "subdomain": "success-integrated",
            "business_activity": "مقاولات",
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
        apps = frappe.parse_json(wizard.selected_apps)
        for app in apps:
            if isinstance(app, dict):
                print(f"   - {app.get('name', app.get('app', str(app)))}")
            else:
                print(f"   - {app}")
        
        print("\n4. إرسال المعالج لبدء التجهيز...")
        wizard.submit()
        print(f"   تم الإرسال بنجاح")
        
        print("\n5. التحقق من المستأجر...")
        if frappe.db.exists("SaaS Tenant", test_data["tenant_name"]):
            tenant = frappe.get_doc("SaaS Tenant", test_data["tenant_name"])
            print(f"   ✅ تم إنشاء المستأجر: {tenant.name}")
            print(f"   حالة المستأجر: {tenant.status}")
            print(f"   اسم الموقع: {tenant.site_name}")
            print(f"   رقم البورت: {tenant.port_number}")
        else:
            print("   ❌ لم يتم العثور على المستأجر")
            return {"success": False, "error": "Tenant not found"
	}
        
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
            
            print("\n7. تنفيذ طلب التجهيز...")
            from erpgenex_saas.services.provisioning import ProvisioningService
            ProvisioningService.run(request.name)
            
            print("\n8. التحقق من حالة المستأجر بعد التجهيز...")
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
            if ":" in tenant.site_name:
                folder_name = f"{tenant.site_name.split(':')[0]}_port_{tenant.site_name.split(':')[1]}"
            else:
                folder_name = tenant.site_name
            
            site_path = f"/home/frappeuser/frappe-bench/sites/{folder_name}"
            if os.path.exists(site_path):
                print(f"   ✅ الموقع موجود في مجلد sites: {site_path}")
                
                # Check site config
                site_config_path = os.path.join(site_path, "site_config.json")
                if os.path.exists(site_config_path):
                    import json
                    with open(site_config_path, 'r') as f:
                        config = json.load(f)
                    print(f"   ✅ ملف التكوين موجود")
                    print(f"   اسم قاعدة البيانات: {config.get('db_name', 'N/A')}")
                    print(f"   نوع قاعدة البيانات: {config.get('db_type', 'N/A')}")
                
                # Check if apps are installed
                apps_txt_path = os.path.join(site_path, "apps.txt")
                if os.path.exists(apps_txt_path):
                    with open(apps_txt_path, 'r') as f:
                        installed_apps = f.read()
                    print(f"\n9. التطبيقات المثبتة في الموقع:")
                    print(f"   {installed_apps}")
                    
                    # Check if erpgenex_saas is NOT installed
                    if 'erpgenex_saas' not in installed_apps:
                        print(f"   ✅ erpgenex_saas غير مثبت (صحيح - للموقع الرئيسي فقط)")
                    else:
                        print(f"   ❌ erpgenex_saas مثبت (يجب أن يكون فقط للموقع الرئيسي)")
            else:
                print(f"   ❌ الموقع غير موجود في مجلد sites: {site_path}")
                return {"success": False, "error": "Site folder not found"
	}
            
            print("\n10. التحقق من النطاق...")
            domains = frappe.get_all("SaaS Domain", filters={"tenant": tenant.name
	})
            if domains:
                print(f"   ✅ تم إنشاء {len(domains)} نطاق(ات)")
                for domain in domains:
                    domain_doc = frappe.get_doc("SaaS Domain", domain.name)
                    print(f"   - {domain_doc.domain_name} ({domain_doc.domain_type})")
            
            print("\n" + "=" * 60)
            print("✅ تم إنشاء الموقع بنجاح!")
            print("=" * 60)
            
            print(f"\n📋 ملخص الموقع الجديد:")
            print(f"   اسم المستأجر: {tenant.name}")
            print(f"   اسم الموقع: {tenant.site_name}")
            print(f"   رقم البورت: {tenant.port_number}")
            print(f"   الحالة: {tenant.status}")
            print(f"   النشاط: {test_data['business_activity']}")
            print(f"   المسار الفعلي: {site_path}")
            print(f"   كلمة المرور: Microhard2610 (من إعدادات SaaS)")
            print(f"   الوصول: http://192.168.1.2:{tenant.port_number}")
            
            return {
                "success": True,
                "site_name": tenant.site_name,
                "port_number": tenant.port_number,
                "status": tenant.status,
                "folder_name": folder_name,
                "access_url": f"http://192.168.1.2:{tenant.port_number
	}"
            }
        else:
            print("   ❌ لم يتم العثور على طلب تجهيز")
            return {"success": False, "error": "Provisioning request not found"
	}
        
    except Exception as e:
        print("\n" + "=" * 60)
        print("❌ فشل إنشاء الموقع!")
        print("=" * 60)
        print(f"الخطأ: {str(e)}")
        print(f"التتبع: {frappe.get_traceback()}")
        
        return {
            "success": False,
            "error": str(e)
        }


if __name__ == "__main__":
    result = create_production_site()
    
    print("\n" + "=" * 60)
    print("النتيجة النهائية")
    print("=" * 60)
    if result.get("success"):
        print(f"✅ تم إنشاء موقع جاهز للعمل بنجاح!")
        print(f"   URL الوصول: {result.get('access_url')}")
        print(f"   كلمة المرور: Microhard2610")
        print(f"   الموقع جاهز للاستخدام")
    else:
        print(f"❌ فشل الإنشاء: {result.get('error')}")
    print("=" * 60)
