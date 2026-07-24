"""
Update SaaS Settings to reserve port 80 for main site
"""

import frappe
from erpgenex_saas.runtime_config import get_root_domain, get_server_host


def update_saas_settings_port_80():
    """Update SaaS Settings to reserve port 80"""
    print("=" * 60)
    print("تحديث إعدادات SaaS Settings لحجز بورت 80")
    print("=" * 60)
    
    try:
        saas_settings = frappe.get_single("SaaS Settings")
        
        # Update settings
        saas_settings.site_distribution_method = "Port"
        saas_settings.base_port = 8001  # Start from 8001, skip 80
        saas_settings.max_port = 8888
        saas_settings.port_increment = 1
        saas_settings.platform_domain = get_root_domain()
        saas_settings.server_ip = get_server_host()
        saas_settings.server_port = 80  # Main site port
        
        saas_settings.save(ignore_permissions=True)
        
        print(f"✅ تم تحديث الإعدادات بنجاح:")
        print(f"   طريقة التوزيع: {saas_settings.site_distribution_method}")
        print(f"   البورت الأساسي: {saas_settings.base_port} (بورت 80 محجوز للموقع الرئيسي)")
        print(f"   أقصى بورت: {saas_settings.max_port}")
        print(f"   زيادة البورت: {saas_settings.port_increment}")
        print(f"   نطاق المنصة: {saas_settings.platform_domain}")
        print(f"   IP السيرفر: {saas_settings.server_ip}")
        print(f"   بورت السيرفر: {saas_settings.server_port} (للموقع الرئيسي)")
        print(f"   كلمة مرور قاعدة البيانات: ******** (محفوظة بأمان)")
        
        return True
        
    except Exception as e:
        print(f"❌ فشل تحديث الإعدادات: {str(e)}")
        print(f"التتبع: {frappe.get_traceback()}")
        return False


if __name__ == "__main__":
    update_saas_settings_port_80()
