import frappe

def cleanup_all_records():
    """Clean up all SaaS records in the correct order"""
    
    print("Starting cleanup of all SaaS records...")
    
    # First, delete SaaS Payments
    payments = frappe.db.get_all("SaaS Payment")
    print(f"Found {len(payments)} SaaS Payments")
    for payment in payments:
        try:
            frappe.delete_doc("SaaS Payment", payment['name'])
            print(f"Deleted SaaS Payment: {payment['name']}")
        except Exception as e:
            print(f"Failed to delete SaaS Payment {payment['name']}: {str(e)}")
    
    # Then, delete SaaS Invoices
    invoices = frappe.db.get_all("SaaS Invoice")
    print(f"Found {len(invoices)} SaaS Invoices")
    for invoice in invoices:
        try:
            frappe.delete_doc("SaaS Invoice", invoice['name'])
            print(f"Deleted SaaS Invoice: {invoice['name']}")
        except Exception as e:
            print(f"Failed to delete SaaS Invoice {invoice['name']}: {str(e)}")
    
    # Then, delete SaaS Customer Accounts
    customer_accounts = frappe.db.get_all("SaaS Customer Account")
    print(f"Found {len(customer_accounts)} SaaS Customer Accounts")
    for account in customer_accounts:
        try:
            frappe.delete_doc("SaaS Customer Account", account['name'])
            print(f"Deleted SaaS Customer Account: {account['name']}")
        except Exception as e:
            print(f"Failed to delete SaaS Customer Account {account['name']}: {str(e)}")
    
    # Then, delete SaaS Tenants with force=True to cascade delete subscriptions and requests
    tenants = frappe.db.get_all("SaaS Tenant")
    print(f"Found {len(tenants)} SaaS Tenants")
    for tenant in tenants:
        try:
            frappe.delete_doc("SaaS Tenant", tenant['name'], force=True, ignore_permissions=True)
            print(f"Deleted SaaS Tenant: {tenant['name']}")
        except Exception as e:
            print(f"Failed to delete SaaS Tenant {tenant['name']}: {str(e)}")
    
    # Then, delete any remaining SaaS Subscriptions
    subscriptions = frappe.db.get_all("SaaS Subscription")
    print(f"Found {len(subscriptions)} SaaS Subscriptions")
    for sub in subscriptions:
        try:
            frappe.delete_doc("SaaS Subscription", sub['name'], ignore_permissions=True)
            print(f"Deleted SaaS Subscription: {sub['name']}")
        except Exception as e:
            print(f"Failed to delete SaaS Subscription {sub['name']}: {str(e)}")
    
    # Then, delete any remaining Provisioning Requests
    requests = frappe.db.get_all("Provisioning Request")
    print(f"Found {len(requests)} Provisioning Requests")
    for req in requests:
        try:
            frappe.delete_doc("Provisioning Request", req['name'], ignore_permissions=True)
            print(f"Deleted Provisioning Request: {req['name']}")
        except Exception as e:
            print(f"Failed to delete Provisioning Request {req['name']}: {str(e)}")
    
    # Then, delete SaaS Domains
    domains = frappe.db.get_all("SaaS Domain")
    print(f"Found {len(domains)} SaaS Domains")
    for domain in domains:
        try:
            frappe.delete_doc("SaaS Domain", domain['name'])
            print(f"Deleted SaaS Domain: {domain['name']}")
        except Exception as e:
            print(f"Failed to delete SaaS Domain {domain['name']}: {str(e)}")
    
    print("Cleanup completed!")

if __name__ == "__main__":
    cleanup_all_records()
