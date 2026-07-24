import frappe
import subprocess
import os
import json
import secrets
from frappe.utils import get_bench_path
from erpgenex_saas.runtime_config import get_site_url

def create_site_manually():
    """Create site manually using subprocess"""
    try:
        bench_path = get_bench_path()
        site_name = os.environ.get("ERPGENEX_SAAS_SITE_NAME") or f"tenant-{secrets.token_hex(3)}"
        admin_password = os.environ.get("ERPGENEX_SAAS_ADMIN_PASSWORD") or secrets.token_urlsafe(12)
        mariadb_root_password = os.environ.get("ERPGENEX_SAAS_MARIADB_ROOT_PASSWORD") or secrets.token_urlsafe(16)
        
        print(f"Creating site: {site_name}")
        
        # Create the site using bench new-site command
        command = [
            "bench",
            "new-site",
            site_name,
            "--admin-password", admin_password,
            "--mariadb-root-password", mariadb_root_password,
            "--no-mariadb-socket"
        ]
        
        result = subprocess.run(
            command,
            cwd=bench_path,
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes timeout
        )
        
        print(f"Return code: {result.returncode}")
        print(f"Output:\n{result.stdout}")
        if result.stderr:
            print(f"Errors:\n{result.stderr}")
        
        if result.returncode == 0:
            print(f"Site created successfully")
            
            # Generate random admin password for the user
            user_password = os.environ.get("ERPGENEX_SAAS_TENANT_PASSWORD") or secrets.token_urlsafe(12)
            
            # Update site_config.json with the correct database password
            site_config_path = os.path.join(bench_path, "sites", site_name, "site_config.json")
            if os.path.exists(site_config_path):
                with open(site_config_path, 'r') as f:
                    config = json.load(f)
                config['db_password'] = admin_password
                with open(site_config_path, 'w') as f:
                    json.dump(config, f, indent=2)
                print(f"Updated database password in site_config.json")
            
            # Create tenant record
            tenant = frappe.get_doc({
                "doctype": "SaaS Tenant",
                "tenant_name": "شركة المقاولات التجريبية",
                "subdomain": "construction-demo",
                "email": "demo@erpgenex.com",
                "company_email": "demo@erpgenex.com",
                "phone": "+966500000000",
                "site_name": site_name,
                "port_number": 8002,
                "site_url": get_site_url(8002),
                "admin_username": "Administrator",
                "admin_password": user_password,
                "status": "Active"
            })
            tenant.insert()
            
            print(f"Tenant created: {tenant.name}")
            print(f"Admin Password: {user_password}")
            print(f"Site URL: {get_site_url(8002)}")
            
            return True
        else:
            print(f"Failed to create site")
            return False
            
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
