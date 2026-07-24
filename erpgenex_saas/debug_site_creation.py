import frappe
import subprocess
import os
from frappe.utils import get_bench_path
from erpgenex_saas.runtime_config import get_site_url

def debug_site_creation():
    """Debug site creation with detailed logging"""
    try:
        bench_path = get_bench_path()
        site_name = os.environ.get("ERPGENEX_SAAS_DEBUG_SITE_NAME") or f"debug-{os.getpid()}:8002"
        folder_name = site_name.split(":")[0] + "_port_" + site_name.split(":")[1]
        
        # Get passwords
        from erpgenex_saas.services.password_manager import PasswordManager
        password_manager = PasswordManager()
        database_password = password_manager.get_db_password()
        mariadb_root_password = password_manager.get_mariadb_root_password()
        admin_password = password_manager.generate_password(length=12)
        
        print(f"Database Password: {database_password}")
        print(f"MariaDB Root Password: {mariadb_root_password}")
        print(f"Admin Password: {admin_password}")
        print(f"Folder Name: {folder_name}")
        
        # Check if site exists
        site_path = os.path.join(bench_path, "sites", folder_name)
        print(f"Site Path: {site_path}")
        print(f"Site Exists: {os.path.exists(site_path)}")
        
        # Create the site
        command = [
            "bench",
            "new-site",
            folder_name,
            "--admin-password", admin_password,
            "--mariadb-root-password", mariadb_root_password,
            "--mariadb-user-host-login-scope=%"
        ]
        
        print(f"Command: {' '.join(command)}")
        print(f"Working Directory: {bench_path}")
        
        result = subprocess.run(
            command,
            cwd=bench_path,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        print(f"\nReturn Code: {result.returncode}")
        print(f"\nSTDOUT (first 500 chars):")
        print(result.stdout[:500])
        print(f"\nSTDERR (first 500 chars):")
        print(result.stderr[:500])
        print(f"Access URL preview: {get_site_url(8002)}")
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
