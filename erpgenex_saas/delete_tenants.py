import frappe

def delete_all_tenants():
    """Delete all SaaS tenants and their related records"""
    # First delete all SaaS Notification Logs
    notification_logs = frappe.get_all("SaaS Notification Log")
    deleted_logs = 0
    
    for log in notification_logs:
        try:
            frappe.delete_doc("SaaS Notification Log", log['name'])
            deleted_logs += 1
            print(f"Deleted SaaS Notification Log: {log['name']}")
        except Exception as e:
            print(f"Failed to delete SaaS Notification Log {log['name']}: {str(e)}")
    
    print(f"\nTotal SaaS Notification Logs deleted: {deleted_logs}")
    
    # Then delete all Provisioning Requests
    provisioning_requests = frappe.get_all("Provisioning Request")
    deleted_requests = 0
    
    for request in provisioning_requests:
        try:
            frappe.delete_doc("Provisioning Request", request['name'])
            deleted_requests += 1
            print(f"Deleted Provisioning Request: {request['name']}")
        except Exception as e:
            print(f"Failed to delete Provisioning Request {request['name']}: {str(e)}")
    
    print(f"\nTotal Provisioning Requests deleted: {deleted_requests}")
    
    # Then delete all SaaS Domains
    domains = frappe.get_all("SaaS Domain")
    deleted_domains = 0
    
    for domain in domains:
        try:
            frappe.delete_doc("SaaS Domain", domain['name'])
            deleted_domains += 1
            print(f"Deleted SaaS Domain: {domain['name']}")
        except Exception as e:
            print(f"Failed to delete SaaS Domain {domain['name']}: {str(e)}")
    
    print(f"\nTotal SaaS Domains deleted: {deleted_domains}")
    
    # Then delete all SaaS Subscriptions
    subscriptions = frappe.get_all("SaaS Subscription")
    deleted_subscriptions = 0
    
    for subscription in subscriptions:
        try:
            frappe.delete_doc("SaaS Subscription", subscription['name'])
            deleted_subscriptions += 1
            print(f"Deleted SaaS Subscription: {subscription['name']}")
        except Exception as e:
            print(f"Failed to delete SaaS Subscription {subscription['name']}: {str(e)}")
    
    print(f"\nTotal SaaS Subscriptions deleted: {deleted_subscriptions}")
    
    # Finally delete all SaaS Tenants
    tenants = frappe.get_all("SaaS Tenant")
    deleted_count = 0
    
    for tenant in tenants:
        try:
            frappe.delete_doc("SaaS Tenant", tenant['name'])
            deleted_count += 1
            print(f"Deleted tenant: {tenant['name']}")
        except Exception as e:
            print(f"Failed to delete tenant {tenant['name']}: {str(e)}")
    
    print(f"\nTotal tenants deleted: {deleted_count}")
    return deleted_count
