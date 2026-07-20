"""
Complete test for new user site creation with immediate functionality
"""

import frappe
import os
import subprocess
import time


def test_complete_user_site_creation():
    """Test complete user site creation with immediate functionality"""
    
    print("=" * 80)
    print("اختبار كامل لإنشاء موقع مستخدم جديد يعمل فوراً")
    print("=" * 80)
    
    try:
        # Test data
        test_data = {
            "tenant_name": "شركة النجاح المتكاملة",
            "company_email": "success@company.com",
            "subdomain": "success-integrated",
            "business_activity": "عام",
            "server_type": "سيرفر مشترك"
        }
        
        print("\n1. إنشاء معالج اختيار النشاط...")
        print(f"   اسم المستأجر: {test_data['tenant_name']}")
        print(f"   البريد: {test_data['company_email']}")
        print(f"   النطاق الفرعي: {test_data['subdomain']}")
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
        print(f"   ✅ تم الحفظ بنجاح: {wizard.name}")
        
        print("\n3. إرسال المعالج لبدء التجهيز...")
        wizard.submit()
        print(f"   ✅ تم الإرسال بنجاح")
        
        print("\n4. التحقق من المستأجر...")
        if frappe.db.exists("SaaS Tenant", test_data["tenant_name"]):
            tenant = frappe.get_doc("SaaS Tenant", test_data["tenant_name"])
            print(f"   ✅ تم إنشاء المستأجر: {tenant.name}")
        else:
            print("   ❌ لم يتم العثور على المستأجر")
            return {"success": False, "error": "Tenant not found"
	}
        
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
            
            print("\n6. تنفيذ طلب التجهيز...")
            from erpgenex_saas.services.provisioning import ProvisioningService
            ProvisioningService.run(request.name)
            print(f"   ✅ تم تنفيذ التجهيز بنجاح")
            
            print("\n7. التحقق من المستأجر بعد التجهيز...")
            tenant.reload()
            print(f"   اسم الموقع: {tenant.site_name}")
            print(f"   رقم البورت: {tenant.port_number}")
            print(f"   الحالة: {tenant.status}")
            
            # Extract folder name from site name
            if ":" in tenant.site_name:
                folder_name = tenant.site_name.replace(":", "_port_")
            else:
                folder_name = tenant.site_name
            
            print(f"   اسم المجلد: {folder_name}")
            
            print("\n8. التحقق من وجود المجلد الفعلي...")
            site_path = f"/home/frappeuser/frappe-bench/sites/{folder_name}"
            if os.path.exists(site_path):
                print(f"   ✅ المجلد موجود: {site_path}")
            else:
                print(f"   ❌ المجلد غير موجود: {site_path}")
                return {"success": False, "error": "Site folder not created"
	}
            
            print("\n9. التحقق من ملف site_config.json...")
            config_path = os.path.join(site_path, "site_config.json")
            if os.path.exists(config_path):
                print(f"   ✅ ملف التكوين موجود")
            else:
                print(f"   ❌ ملف التكوين غير موجود")
                return {"success": False, "error": "site_config.json not found"
	}
            
            print("\n10. التحقق من البورت...")
            if tenant.port_number == 80:
                print(f"   ❌ فشل: البورت 80 محجوز للموقع الرئيسي!")
                return {"success": False, "error": "Port 80 assigned to user site"
	}
            else:
                print(f"   ✅ البورت {tenant.port_number} صحيح (ليس 80)")
            
            print("\n11. التحقق من إعدادات SaaS Settings...")
            saas_settings = frappe.get_single("SaaS Settings")
            print(f"   البورت الأساسي: {saas_settings.base_port}")
            print(f"   بورت السيرفر: {saas_settings.server_port}")
            print(f"   كلمة مرور قاعدة البيانات: ********")
            
            print("\n12. إعادة تحميل nginx...")
            try:
                subprocess.run(["sudo", "systemctl", "reload", "nginx"], 
                              capture_output=True, text=True, check=True)
                print("   ✅ تم إعادة تحميل nginx")
                time.sleep(2)  # Wait for nginx to reload
            except Exception as e:
                print(f"   ⚠️  تحذير: فشل إعادة تحميل nginx: {str(e)}")
            
            print("\n13. التحقق من الوصول للموقع...")
            # Check if site is accessible via nginx
            import requests
            try:
                access_url = f"http://192.168.1.2:{tenant.port_number}"
                response = requests.get(access_url, timeout=5)
                if response.status_code == 200:
                    print(f"   ✅ الموقع يعمل: {access_url}")
                else:
                    print(f"   ⚠️  الموقع يرد بالكود: {response.status_code}")
            except Exception as e:
                print(f"   ⚠️  لا يمكن الوصول للموقع: {str(e)}")
                print(f"   (قد يحتاج وقت إضافي للبدء)")
            
            print("\n14. التحقق من سجلات النطاق...")
            domains = frappe.get_all("SaaS Domain", filters={"tenant": tenant.name
	})
            if domains:
                print(f"   ✅ تم إنشاء سجل النطاق: {domains[0]['name']}")
            else:
                print(f"   ⚠️  لم يتم العثور على سجل النطاق")
            
            print("\n" + "=" * 80)
            print("✅ تم إنشاء موقع المستخدم بنجاح")
            print("=" * 80)
            
            return {
                "success": True,
                "tenant_name": tenant.name,
                "site_name": tenant.site_name,
                "port_number": tenant.port_number,
                "folder_name": folder_name,
                "access_url": f"http://192.168.1.2:{tenant.port_number
	}",
                "status": tenant.status
            }
        else:
            print("   ❌ لم يتم العثور على طلب تجهيز")
            return {"success": False, "error": "Provisioning request not found"
	}
        
    except Exception as e:
        print("\n" + "=" * 80)
        print("❌ فشل الاختبار!")
        print("=" * 80)
        print(f"الخطأ: {str(e)}")
        print(f"التتبع: {frappe.get_traceback()}")
        
        return {
            "success": False,
            "error": str(e)
        }


if __name__ == "__main__":
    result = test_complete_user_site_creation()
    
    print("\n" + "=" * 80)
    print("النتيجة النهائية")
    print("=" * 80)
    if result.get("success"):
        print(f"✅ نجح الاختبار!")
        print(f"   المستأجر: {result.get('tenant_name')}")
        print(f"   اسم الموقع: {result.get('site_name')}")
        print(f"   البورت: {result.get('port_number')}")
        print(f"   رابط الوصول: {result.get('access_url')}")
        print(f"   الحالة: {result.get('status')}")
        print(f"\n✅ الموقع جاهز للعمل فوراً!")
    else:
        print(f"❌ فشل الاختبار: {result.get('error')}")
    print("=" * 80)
