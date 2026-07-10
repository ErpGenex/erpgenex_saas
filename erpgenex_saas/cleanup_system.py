"""
Delete all existing tenants and sites for fresh start
"""

import frappe
import os


def delete_all_tenants():
    """Delete all existing SaaS Tenants using SQL to bypass link checks"""
    print("=" * 60)
    print("حذف جميع المستأجرين الموجودين")
    print("=" * 60)
    
    try:
        # Use SQL to delete all records in correct order
        print("\nحذف جميع السجلات باستخدام SQL...")
        
        # Delete in correct order
        tables_to_delete = [
            "tabActivity Selection Wizard",
            "tabSaaS Subscription",
            "tabProvisioning Request", 
            "tabSaaS Domain",
            "tabSaaS Tenant"
        ]
        
        for table in tables_to_delete:
            result = frappe.db.sql(f"DELETE FROM `{table}`")
            print(f"   ✅ تم حذف من {table}")
        
        print("\n" + "=" * 60)
        print("✅ تم حذف جميع المستأجرين من قاعدة البيانات")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ فشل الحذف: {str(e)}")
        print(f"التتبع: {frappe.get_traceback()}")
        return False


def delete_all_sites():
    """Delete all site folders except the main site"""
    print("\n" + "=" * 60)
    print("حذف جميع المواقع من مجلد sites")
    print("=" * 60)
    
    try:
        sites_path = "/home/frappeuser/frappe-bench/sites"
        
        # Get all directories in sites folder
        all_items = os.listdir(sites_path)
        
        # Filter for directories (sites)
        site_dirs = []
        for item in all_items:
            item_path = os.path.join(sites_path, item)
            if os.path.isdir(item_path) and item != "common_site_config.json":
                site_dirs.append(item)
        
        print(f"\nعدد المواقع الموجودة: {len(site_dirs)}")
        
        for site in site_dirs:
            # Skip the main site and assets folder (main site needs assets)
            if site in ["erpgenex.local.site", "assets"]:
                print(f"\nتخطي الموقع الرئيسي/المجلدات الضرورية: {site}")
                continue
            
            site_path = os.path.join(sites_path, site)
            print(f"\nحذف الموقع: {site}")
            print(f"   المسار: {site_path}")
            
            # Delete the site directory
            import shutil
            shutil.rmtree(site_path)
            print(f"   ✅ تم حذف الموقع")
        
        print("\n" + "=" * 60)
        print("✅ تم حذف جميع المواقع من مجلد sites")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ فشل الحذف: {str(e)}")
        return False


if __name__ == "__main__":
    # Delete tenants from database
    delete_all_tenants()
    
    # Delete site folders
    delete_all_sites()
    
    print("\n" + "=" * 60)
    print("✅ تم تنظيف النظام بالكامل")
    print("جاهز لبدء اختبار جديد")
    print("=" * 60)
