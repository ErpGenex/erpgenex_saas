"""
Update SaaS Settings to use Port-based distribution
"""

import frappe
from erpgenex_saas.runtime_config import get_root_domain, get_server_host


def update_to_port_based():
    """Update SaaS Settings to use port-based distribution"""
    print("=" * 60)
    print("تحديث إعدادات SaaS Settings لاستخدام توزيع البورت")
    print("=" * 60)
    
    try:
        saas_settings = frappe.get_single("SaaS Settings")
        
        # Update to port-based distribution
        saas_settings.site_distribution_method = "Port"
        saas_settings.base_port = 8088
        saas_settings.port_increment = 1
        saas_settings.platform_domain = get_root_domain()
        saas_settings.server_ip = get_server_host()
        saas_settings.server_port = 8088
        
        saas_settings.save(ignore_permissions=True)
        
        print(f"✅ تم تحديث الإعدادات بنجاح:")
        print(f"   طريقة التوزيع: {saas_settings.site_distribution_method}")
        print(f"   البورت الأساسي: {saas_settings.base_port}")
        print(f"   زيادة البورت: {saas_settings.port_increment}")
        print(f"   نطاق المنصة: {saas_settings.platform_domain}")
        print(f"   IP السيرفر: {saas_settings.server_ip}")
        print(f"   البورت: {saas_settings.server_port}")
        
        return True
        
    except Exception as e:
        print(f"❌ فشل تحديث الإعدادات: {str(e)}")
        print(f"التتبع: {frappe.get_traceback()}")
        return False


if __name__ == "__main__":
    update_to_port_based()
