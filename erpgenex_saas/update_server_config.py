"""
Update SaaS Settings with server IP and port configuration
"""

import frappe


def update_server_configuration():
    """Update SaaS Settings with server IP and port"""
    print("=" * 60)
    print("تحديث إعدادات السيرفر في SaaS Settings")
    print("=" * 60)
    
    try:
        saas_settings = frappe.get_single("SaaS Settings")
        
        # Update server configuration
        saas_settings.server_ip = "192.168.1.2"
        saas_settings.server_port = 8088
        saas_settings.platform_domain = "erpgenex.local"
        saas_settings.site_distribution_method = "Subdomain"
        
        saas_settings.save(ignore_permissions=True)
        
        print(f"✅ تم تحديث الإعدادات بنجاح:")
        print(f"   IP السيرفر: {saas_settings.server_ip}")
        print(f"   البورت: {saas_settings.server_port}")
        print(f"   نطاق المنصة: {saas_settings.platform_domain}")
        print(f"   طريقة التوزيع: {saas_settings.site_distribution_method}")
        
        return True
        
    except Exception as e:
        print(f"❌ فشل تحديث الإعدادات: {str(e)}")
        print(f"التتبع: {frappe.get_traceback()}")
        return False


if __name__ == "__main__":
    update_server_configuration()
