import frappe
import subprocess
import os
import secrets
from frappe.utils import get_bench_path

def test_site_creation():
    """Test site creation directly"""
    try:
        bench_path = get_bench_path()
        folder_name = os.environ.get("ERPGENEX_SAAS_TEST_SITE_NAME") or f"test-{secrets.token_hex(3)}"
        
        # Get passwords
        from erpgenex_saas.services.password_manager import PasswordManager
        password_manager = PasswordManager()
        database_password = password_manager.get_db_password()
        mariadb_root_password = password_manager.get_mariadb_root_password()
        admin_password = password_manager.generate_password(length=12)
        
        print(f"Database Password: {database_password}")
        print(f"MariaDB Root Password: {mariadb_root_password}")
        print(f"Admin Password: {admin_password}")
        
        # Create the site
        command = [
            "bench",
            "new-site",
            folder_name,
            "--admin-password", admin_password,
            "--mariadb-root-password", mariadb_root_password,
            "--no-mariadb-socket"
        ]
        
        print(f"Running command: {' '.join(command)}")
        
        result = subprocess.run(
            command,
            cwd=bench_path,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        print(f"Return code: {result.returncode}")
        print(f"Output:\n{result.stdout}")
        if result.stderr:
            print(f"Errors:\n{result.stderr}")
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
