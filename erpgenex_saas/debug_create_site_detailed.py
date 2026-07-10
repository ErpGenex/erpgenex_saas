import frappe
import subprocess
import os

def debug_create_site_detailed():
    """Debug create_site with detailed logging"""
    try:
        bench_path = "/home/frappeuser/frappe-bench"
        site_name = "erpgenex.local:8002"
        tenant_name = "شركة المقاولات التجريبية"
        
        # Get passwords
        from erpgenex_saas.services.password_manager import PasswordManager
        password_manager = PasswordManager()
        database_password = password_manager.get_db_password()
        mariadb_root_password = password_manager.get_mariadb_root_password()
        admin_password = password_manager.generate_password(length=12)
        
        print(f"Database Password: {database_password}")
        print(f"MariaDB Root Password: {mariadb_root_password}")
        print(f"Admin Password: {admin_password}")
        
        # Generate folder name
        if ":" in site_name:
            folder_name = site_name.split(":")[0]
            port = site_name.split(":")[1]
            folder_name = f"{folder_name}_port_{port}"
        else:
            folder_name = site_name
        
        print(f"Folder Name: {folder_name}")
        
        # Check if site exists
        site_path = os.path.join(bench_path, "sites", folder_name)
        print(f"Site Path: {site_path}")
        print(f"Site Exists: {os.path.exists(site_path)}")
        
        if os.path.exists(site_path):
            print("Site already exists, cannot test")
            return False
        
        # Test pre-flight checks
        from erpgenex_saas.services.provisioning import ProvisioningService
        print("\nTesting pre-flight checks...")
        preflight_result = ProvisioningService.pre_flight_checks()
        print(f"Pre-flight result: {preflight_result}")
        
        if not preflight_result:
            print("Pre-flight checks failed")
            return False
        
        # Create the site
        print("\nCreating site...")
        command = [
            "bench",
            "new-site",
            folder_name,
            "--admin-password", admin_password,
            "--mariadb-root-password", mariadb_root_password,
            "--mariadb-user-host-login-scope=%"
        ]
        
        print(f"Command: {' '.join(command)}")
        
        result = subprocess.run(
            command,
            cwd=bench_path,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        print(f"\nReturn Code: {result.returncode}")
        print(f"STDOUT (last 1000 chars):")
        print(result.stdout[-1000:])
        if result.stderr:
            print(f"STDERR (last 1000 chars):")
            print(result.stderr[-1000:])
        
        if result.returncode == 0:
            print("\nSite created successfully")
            
            # Test database verification
            print("\nTesting database verification...")
            db_verify = ProvisioningService.verify_database(folder_name)
            print(f"Database verification: {db_verify}")
            
            # Test user verification
            print("\nTesting user verification...")
            user_verify = ProvisioningService.verify_database_user(folder_name)
            print(f"User verification: {user_verify}")
            
            # Update site_config.json
            print("\nUpdating site_config.json...")
            site_config_path = os.path.join(bench_path, "sites", folder_name, "site_config.json")
            if os.path.exists(site_config_path):
                import json
                with open(site_config_path, 'r') as f:
                    config = json.load(f)
                config['db_password'] = database_password
                with open(site_config_path, 'w') as f:
                    json.dump(config, f, indent=2)
                print("Updated site_config.json")
            
            return True
        else:
            print("\nSite creation failed")
            
            # Test rollback
            print("\nTesting rollback...")
            ProvisioningService.rollback_database(folder_name)
            ProvisioningService.rollback_site_folder(folder_name)
            
            return False
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
