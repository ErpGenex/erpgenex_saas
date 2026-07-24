import frappe
import os
from erpgenex_saas.runtime_config import get_main_site_name, get_root_domain, get_server_host, get_site_url

def show_passwords_and_commands():
    """Display passwords from SaaS Settings and commands for site creation"""
    try:
        # Get SaaS Settings
        saas_settings = frappe.get_single("SaaS Settings")
        
        print("=" * 60)
        print("SaaS Settings - Passwords")
        print("=" * 60)
        print(f"Server IP: {saas_settings.server_ip}")
        print(f"Server Port: {saas_settings.server_port}")
        print(f"Platform Domain: {saas_settings.platform_domain}")
        print(f"Database Password: {saas_settings.database_password}")
        print(f"MariaDB Root Password: {saas_settings.mariadb_root_password}")
        print(f"Site Distribution Method: {saas_settings.site_distribution_method}")
        
        print("\n" + "=" * 60)
        print("Commands for Creating New Site")
        print("=" * 60)
        
        # Get main site password
        import json
        from frappe.utils import get_bench_path

        site_name = getattr(frappe.local, "site", None) or get_main_site_name()
        if not site_name:
            raise frappe.ValidationError("Unable to resolve the current site name")
        main_config_path = os.path.join(get_bench_path(), "sites", site_name, "site_config.json")
        with open(main_config_path, 'r') as f:
            main_config = json.load(f)
        
        main_db_password = main_config['db_password']
        
        print(f"\n1. Create new site command:")
        print(f"   bench new-site <site_name> \\")
        print(f"     --admin-password {main_db_password} \\")
        print(f"     --mariadb-root-password {main_db_password} \\")
        print(f"     --no-mariadb-socket")
        
        print(f"\n2. Install apps command:")
        print(f"   bench --site <site_name> install-app omnexa_construction")
        
        print(f"\n3. Configure nginx command:")
        print(f"   bench setup-nginx --site <site_name>")
        
        print(f"\n4. Test nginx configuration:")
        print(f"   nginx -t")
        
        print(f"\n5. Reload nginx:")
        print(f"   nginx -s reload")
        
        print(f"\n" + "=" * 60)
        print("Port Allocation")
        print("=" * 60)
        print(f"Main Site Port: 80 (reserved)")
        print(f"Tenant Sites Port Range: 8001-8888")
        print(f"Current Used Ports: Check PortManager service")
        
        print(f"\n" + "=" * 60)
        print("Site URL Format")
        print("=" * 60)
        print(f"Port-based: {get_site_url('<port>')}")
        print(f"Server host: {get_server_host()}")
        print(f"Subdomain-based: http://<subdomain>.{get_root_domain()}")
        
        return True
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
