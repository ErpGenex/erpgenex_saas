"""
Check tenant credentials
"""
import frappe

def check_credentials():
    tenant = frappe.get_doc('SaaS Tenant', 'شركة النجاح المتكاملة')
    print(f'Admin Username: {tenant.admin_username}')
    print(f'Admin Password: {tenant.admin_password}')
    print(f'Site URL: {tenant.site_url}')
    print(f'Site Name: {tenant.site_name}')
    print(f'Port Number: {tenant.port_number}')

if __name__ == "__main__":
    check_credentials()
