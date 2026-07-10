import frappe
import subprocess
import os

def configure_nginx_for_site():
    """Configure nginx for the construction site"""
    try:
        tenant = frappe.get_last_doc("SaaS Tenant")
        
        print(f"Configuring nginx for site: {tenant.site_name}")
        print(f"Port: {tenant.port_number}")
        
        # Handle port-based site names
        if ":" in tenant.site_name:
            folder_name = tenant.site_name.split(":")[0]
            port = tenant.site_name.split(":")[1]
            folder_name = f"{folder_name}_port_{port}"
        else:
            folder_name = tenant.site_name
        
        bench_path = "/home/frappeuser/frappe-bench"
        site_path = os.path.join(bench_path, "sites", folder_name)
        
        # Use bench to configure nginx for the site
        command = [
            "bench",
            "setup-nginx",
            "--site", folder_name
        ]
        
        result = subprocess.run(
            command,
            cwd=bench_path,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        print(f"Nginx configuration output:\n{result.stdout}")
        if result.stderr:
            print(f"Errors:\n{result.stderr}")
        
        # Test nginx configuration
        test_result = subprocess.run(
            ["nginx", "-t"],
            capture_output=True,
            text=True
        )
        print(f"Nginx test:\n{test_result.stdout}")
        if test_result.stderr:
            print(f"Test errors:\n{test_result.stderr}")
        
        # Reload nginx
        reload_result = subprocess.run(
            ["nginx", "-s", "reload"],
            capture_output=True,
            text=True
        )
        print(f"Nginx reload:\n{reload_result.stdout}")
        if reload_result.stderr:
            print(f"Reload errors:\n{reload_result.stderr}")
        
        return True
        
    except Exception as e:
        print(f"Error configuring nginx: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
