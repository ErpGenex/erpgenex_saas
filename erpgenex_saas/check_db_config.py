"""
Check MariaDB root password from bench configuration
"""
import frappe

def check_db_password():
    # Try to get the database password from common_site_config.json
    import json
    import os
    
    config_path = "/home/frappeuser/frappe-bench/sites/common_site_config.json"
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = json.load(f)
            print(f"Config keys: {list(config.keys())}")
            # Check for db related keys
            for key in config.keys():
                if 'db' in key.lower() or 'password' in key.lower():
                    print(f"{key}: {config[key]}")

if __name__ == "__main__":
    check_db_password()
